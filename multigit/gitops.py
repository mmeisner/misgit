import os
import sys
import time

from multigit import misc


# Column text to show if a repo is a submodule
COL_SUBMODULE_TEXT = "mod"

# Column separator (default is two spaces between columns)
COL_SEPARATOR = "  "


def list_repos(dirargs, exclude=None, depth=999,
               fields="", timeformat="",
               as_diff=False, more_info=False):
    if as_diff and len(dirargs) != 2:
        misc.error("Two directories are required")
        sys.exit(1)

    out_files = []
    elapsed_oswalk = 0
    elapsed_gitcmd = 0

    for i, dirarg in enumerate(dirargs):
        if not os.path.isdir(dirarg):
            misc.error(f"Not a directory: {dirarg}")
            continue

        started = time.time()
        dirpaths = find_repos(dirarg, exclude, depth=depth)
        elapsed_oswalk += time.time() - started
        if not dirpaths:
            misc.error(f"No git repos found below {dirarg}")
            continue

        if as_diff:
            # If user wants to diff/compare then close previous file
            # ensure each top-level directory listing goes into separate file
            tmpfile = f"/tmp/misgit{i}.lst"
            fd_out = open(tmpfile, "w")
            out_files.append(tmpfile)
        else:
            fd_out = sys.stdout

        # Just print path and nothing else
        if fields == "":
            print("\n".join(dirpaths), file=fd_out)
            continue

        started = time.time()
        repos = {}
        failed_paths = []
        for path in dirpaths:
            misc.progress_print(path)

            desc, branch, status, status_lines, url, reponame, _time, is_submodule = "", "", "", "", "", "", "", ""
            try:
                if "desc" in fields:
                    desc = misc.cmd_run_get_output(f"git -C {path} describe --tags --always")
                if "branch" in fields:
                    branch = misc.cmd_run_get_output(f"git -C {path} branch --show-current")
                if "status" in fields:
                    status_lines, status = git_status_long_and_short(path)
                if "url" in fields or "name" in fields:
                    url = misc.cmd_run_get_output(f"git -C {path} config --get remote.origin.url")
                    reponame = os.path.basename(url).replace(".git", "")
                if "time" in fields:
                    # %ct committer date, UNIX timestamp
                    # %cd committer date (format respects --date= option)
                    # %ci committer date, ISO 8601-like format: "2022-12-05 10:37:49 +0100"
                    # %cs committer date, short format (YYYY-MM-DD)
                    # --date=short
                    # --date=format-local:'%Y-%m-%d %H:%M:%S'
                    if timeformat in ("rel", "human"):
                        _time = misc.cmd_run_get_output(f"git -C {path} show -s --format=%ct")
                        _time = started - int(_time)
                        _time = misc.secs_to_human_str(_time)
                    elif timeformat == "date":
                        _time = misc.cmd_run_get_output(f"git -C {path} show -s --format=%cs")
                    elif timeformat in ("time", "datetime"):
                        _time = misc.cmd_run_get_output(f"git -C {path} show -s --format=%cd --date=format-local:'%Y-%m-%d %H:%M:%S'")
                if "sub" in fields:
                    is_submodule = COL_SUBMODULE_TEXT if os.path.isfile(f"{path}/.git") else ""
            except Exception as e:
                failed_paths.append(path)
                print(e)
                continue

            repos[path] = {
                'path': path,
                'desc': desc,
                'branch': branch,
                'status': status,
                'status_lines': status_lines,
                'url': url,
                'name': reponame,
                'time': _time,
                'sub': is_submodule,
            }
            if os.path.islink(path):
                repos[path]['path'] += "@"

        elapsed_gitcmd += time.time() - started

        # Remove "submodule" column if there are no submodule repos
        any_submods = any(1 for path in repos.keys() if repos[path]['sub'])
        if not any_submods:
            fields = fields.replace(",sub", "")

        for p in failed_paths:
            dirpaths.remove(p)

        # Compute max width of all columns across all lines
        head = fields.split(",")
        w = {}
        for k in head:
            w[k] = max([len(repos[path][k]) for path in repos.keys()] + [len(k)])

        # Print the header
        header = [f"{col:{w[col]}}" for col in head]
        header = COL_SEPARATOR.join(header)
        print(header, file=sys.stderr)
        print("-" * len(header), file=sys.stderr)

        # Print info line for each repo
        for path in dirpaths:
            d = repos[path]
            line = [f"{d[col]:{w[col]}}" for col in head]
            print(COL_SEPARATOR.join(line), file=fd_out)
            if more_info and d['status_lines']:
                lines = "\n    ".join(d['status_lines'])
                misc.print_dim("    " + lines)

        # close file to ensure that it is flushed before launching difftool
        if as_diff:
            fd_out.close()

    misc.progress_end()

    if as_diff:
        cmd = f"meld {out_files[0]} {out_files[1]} &"
        misc.log_shell(cmd)
        os.system(cmd)

    if misc.verbose > 0:
        misc.print_dim(f"elapsed: dirwalk={elapsed_oswalk:.1f}s git={elapsed_gitcmd:.1f}s", file=sys.stderr)


def find_repos(path=".", exclude=None, depth=999):
    gitdirs = []

    if exclude is None:
        exclude = []

    for i in range(len(exclude)):
        exclude[i] = exclude[i].rstrip("/")

    exc_rel = []
    exc_abs = []
    for x in exclude:
        if "/" in x:
            x_noslash = x.lstrip("/")
            exc_abs.append(f"{path}/{x_noslash}")
        else:
            exc_rel.append(x)

    # From Python os.walk() docs:
    # When topdown is True, the caller can modify the dirnames list in-place
    # (perhaps using del or slice assignment), and walk() will only recurse
    # into the subdirectories whose names remain in dirnames;
    # this can be used to prune the search, impose a specific order of visiting,
    # or even to inform walk() about directories the caller creates or renames
    # before it resumes walk() again.
    # Note that ".git" can be either a directory or a file!!!
    for root, dirs, files in os.walk(top=path, topdown=True, followlinks=True):
        dirs[:] = [d for d in dirs if d not in exc_rel]
        if root.count("/") > depth:
            dirs[:] = []
            continue

        if any([x for x in exc_abs if root.startswith(x)]):
            continue

        misc.progress_print(root)
        if ".git" in dirs:
            gitdirs.append(root)
            dirs.remove(".git")
        if ".git" in files:
            gitdirs.append(root)

    # remove "./" prefix from all paths
    dirs = []
    for path in gitdirs:
        dirs.append(path[2:] if path.startswith("./") else path)

    misc.progress_end()

    return sorted(dirs)


def git_status_long_and_short(path):
    lines = misc.cmd_run_get_output(f"git -C {path} status --porcelain", splitlines=True)
    if not lines:
        return "", ""

    status = {'M': 0, 'D': 0, 'R': 0, '?': 0}
    unparsed = 0

    # TODO: This is surely not the correct way to parse the output but it works in many cases
    for line in lines:
        xy = line[0:2]
        if xy[0] in status.keys():
            status[xy[0]] += 1
        elif xy[1] in status.keys():
            status[xy[1]] += 1
        else:
            unparsed += 1

    status['X'] = unparsed
    s_list = [f"{k}{v}" for k, v in status.items() if v > 0]
    lines = [line for line in lines if not line.startswith("??")]
    return lines, " ".join(s_list)


def pull_repos(dirargs, exclude=None, depth=999):
    elapsed_oswalk = 0
    elapsed_gitcmd = 0

    for i, dirarg in enumerate(dirargs):
        if not os.path.isdir(dirarg):
            misc.error(f"Not a directory: {dirarg}")
            continue

        started = time.time()
        dirpaths = find_repos(dirarg, exclude, depth=depth)
        elapsed_oswalk += time.time() - started
        if not dirpaths:
            misc.error(f"No git repos found below {dirarg}")
            continue

        started = time.time()
        for path in dirpaths:
            misc.print_lite(path)
            try:
                lines = misc.cmd_run_get_output(f"git -C {path} pull --rebase", splitlines=True, on_error=RuntimeError)
                print("\n".join(lines))
            except RuntimeError as e:
                print(str(e))

        elapsed_gitcmd += time.time() - started

    misc.progress_end()

    if misc.verbose > 0:
        misc.print_dim(f"elapsed: dirwalk={elapsed_oswalk:.1f}s git={elapsed_gitcmd:.1f}s", file=sys.stderr)
