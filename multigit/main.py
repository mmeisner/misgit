#!/usr/bin/env python3
# Extract git summary info across multiple git repos below some folder (recursively)
# tags: git

import argparse
import os
import sys
import time

from multigit import misc

# Column text to show if a repo is a submodule
COL_SUBMODULE_TEXT = "mod"

# Column separator (default is two spaces between columns)
COL_SEPARATOR = "  "


opt = argparse.Namespace()

def main():
    global opt
    opt = parser_create().parse_args()

    dirargs = opt.posargs
    if not dirargs:
        dirargs = ["."]

    excludes = opt.exclude

    fields = "desc,sub,branch,time,status"
    if opt.only_path:
        fields = ""
    if opt.timeformat.startswith("n"):
        fields.replace("time,", "")

    progress_start()

    git_list_all(dirargs, excludes, fields=fields, depth=opt.maxdepth, as_diff=opt.diff)


examples = f"""Examples:
  Compare two directories of git repos:
    ./%(prog)s --diff foo baz
"""

def parser_create():
    description = f"""
Show git summary info for all git repos below some folder (recursively) 
For each repo found, shows: repo path, tag, branch, status
"""
    parser = argparse.ArgumentParser(
        description=description, epilog=examples, add_help=False, formatter_class=argparse.RawTextHelpFormatter)

    g = parser.add_argument_group("Main options")
    g.add_argument(dest='posargs', metavar='DIR', type=str, nargs="*",
        help=f"""Folder(s) to search for git repos. Default is current dir""")
    g.add_argument("-x", dest='exclude', metavar='DIR', type=str, action="append",
        help=f"""Exclude folder. Relative to search folders (or absolute). Can be given multiple times.""")
    g.add_argument("-d", dest='maxdepth', metavar='NUM', type=int, default=999,
        help=f"Max depth of search")

    g = parser.add_argument_group("Output options")
    g.add_argument('-p', dest='only_path', action="store_true",
        help="Show only git repo paths")
    g.add_argument('-t', dest='timeformat', metavar="FORMAT", type=str, default="rel",
        help="Format of committer date column: rel, date, time, none")

    g = parser.add_argument_group("Advanced options")
    g.add_argument('--diff', dest='diff', action='store_true', default=False,
        help="Compare two trees (requires two DIRectory arguments)")

    g = parser.add_argument_group("Misc options")
    g.add_argument('-v', dest='verbose', action='count', default=0,
        help="Be more verbose")
    g.add_argument('-h', action='help',
        help="Show this help message and exit")

    return parser


################################################################################
#
################################################################################

def git_list_all(dirargs, exclude=None, fields="", depth=999, as_diff=False):
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
        dirpaths = find_git_repos(dirarg, exclude, depth=depth)
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
            progress_print(path)

            desc, branch, status, _time, is_submodule = "", "", "", "", ""
            try:
                if "desc" in fields:
                    desc = misc.cmd_run_get_output(f"git -C {path} describe --tags --always")
                if "branch" in fields:
                    branch = misc.cmd_run_get_output(f"git -C {path} branch --show-current")
                if "status" in fields:
                    status = git_status_to_shortstr(path)
                if "time" in fields:
                    # %ct committer date, UNIX timestamp
                    # %cd committer date (format respects --date= option)
                    # %ci committer date, ISO 8601-like format: "2022-12-05 10:37:49 +0100"
                    # %cs committer date, short format (YYYY-MM-DD)
                    # --date=short
                    # --date=format-local:'%Y-%m-%d %H:%M:%S'
                    if opt.timeformat in ("rel", "human"):
                        _time = misc.cmd_run_get_output(f"git -C {path} show -s --format=%ct")
                        _time = started - int(_time)
                        _time = misc.secs_to_human_str(_time)
                    elif opt.timeformat == "date":
                        _time = misc.cmd_run_get_output(f"git -C {path} show -s --format=%cs")
                    elif opt.timeformat in ("time", "datetime"):
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
                'time': _time,
                'sub': is_submodule,
            }

        elapsed_gitcmd += time.time() - started

        for p in failed_paths:
            dirpaths.remove(p)

        # Compute max width of all columns across all lines
        head = ['path', 'desc', 'sub', 'branch', 'time', 'status']
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

        # close file to ensure that it is flushed before launching difftool
        if as_diff:
            fd_out.close()

    progress_end()

    if as_diff:
        cmd = f"meld {out_files[0]} {out_files[1]} &"
        misc.log_shell(cmd)
        os.system(cmd)

    if opt.verbose > 0:
        print(f"elapsed: dirwalk={elapsed_oswalk:.1f}s git={elapsed_gitcmd:.1f}s", file=sys.stderr)


def find_git_repos(path=".", exclude=None, depth=999):
    gitdirs = []

    if exclude is None:
        exclude = []

    # From Python os.walk() docs:
    # When topdown is True, the caller can modify the dirnames list in-place
    # (perhaps using del or slice assignment), and walk() will only recurse
    # into the subdirectories whose names remain in dirnames;
    # this can be used to prune the search, impose a specific order of visiting,
    # or even to inform walk() about directories the caller creates or renames
    # before it resumes walk() again.
    # Note that ".git" can be either a directory or a file!!!
    for root, dirs, files in os.walk(top=path, topdown=True, followlinks=True):
        dirs[:] = [d for d in dirs if d not in exclude]
        if root.count("/") > depth:
            dirs[:] = []
            continue
        progress_print(root)
        if ".git" in dirs:
            gitdirs.append(root)
            dirs.remove(".git")
        if ".git" in files:
            gitdirs.append(root)

    # remove "./" prefix from all paths
    dirs = []
    for path in gitdirs:
        dirs.append(path[2:] if path.startswith("./") else path)

    progress_end()

    return sorted(dirs)


term_cols = 0

def progress_start():
    global term_cols
    if sys.stdout.isatty():
        term_cols, rows = os.get_terminal_size(0)

def progress_end():
    if opt.verbose and term_cols:
        sys.stderr.write(" " * term_cols + "\r")

def progress_print(s):
    if opt.verbose and term_cols:
        s = s[:term_cols - 1]
        sys.stderr.write(s + "\r")


def git_status_to_shortstr(path):
    lines = misc.cmd_run_get_output(f"git -C {path} status --porcelain", splitlines=True)
    if not lines:
        return ""

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
    return " ".join(s_list)
