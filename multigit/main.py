#!/usr/bin/env python3
# Extract git summary info across multiple git repos below some folder (recursively)
# tags: git

import argparse
import os
import sys

from multigit import misc


def main():
    opt = parser_create().parse_args()

    dirargs = opt.posargs
    if not dirargs:
        dirargs = ["."]

    excludes = opt.exclude
    fields = "desc,branch,status"
    if opt.only_path:
        fields = ""

    git_list_all(dirargs, excludes, fields=fields, as_diff=opt.diff)


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
    g.add_argument('--diff', dest='diff', action='store_true', default=False,
        help="Compare two trees (requires two DIRectory arguments)")

    #g = parser.add_argument_group("Advanced options")
    g.add_argument('-p', dest='only_path', action="store_true",
        help="Show only git repo paths")

    g = parser.add_argument_group("Misc options")
    # g.add_argument('-v', dest='verbose', action='count', default=1,
    #     help="Be more verbose")
    g.add_argument('-h', action='help',
        help="Show this help message and exit")

    return parser


################################################################################
#
################################################################################

def git_list_all(dirargs, exclude=None, fields="", as_diff=False):
    if as_diff and len(dirargs) != 2:
        misc.error("Two directories are required")
        sys.exit(1)

    out_files = []

    for i, dirarg in enumerate(dirargs):
        if not os.path.isdir(dirarg):
            misc.error(f"Not a directory: {dirarg}")
            continue

        dirpaths = find_git_repos(dirarg, exclude)
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

        repos = {}
        failed_paths = []
        for path in dirpaths:
            desc, branch, status = "", "", ""
            try:
                if "desc" in fields:
                    desc = misc.cmd_run_get_output(f"git -C {path} describe --tags --always")
                if "branch" in fields:
                    branch = misc.cmd_run_get_output(f"git -C {path} branch --show-current")
                if "status" in fields:
                    status = git_status_to_shortstr(path)
            except Exception as e:
                failed_paths.append(path)
                print(e)
                continue

            repos[path] = {
                'path': path,
                'desc': desc,
                'branch': branch,
                'status': status,
            }

        for p in failed_paths:
            dirpaths.remove(p)

        # Compute max width of all columns across all lines
        head = ['path', 'desc', 'branch', 'status']
        w = {}
        for k in head:
            w[k] = max([len(repos[path][k]) for path in repos.keys()] + [len(k)])

        # Print the header
        header = [f"{col:{w[col]}}" for col in head]
        print(" ".join(header))

        # Print info line for each repo
        for path in dirpaths:
            d = repos[path]
            line = [f"{d[col]:{w[col]}}" for col in head]
            print(" ".join(line), file=fd_out)

        # close file to ensure that it is flushed before launching difftool
        if as_diff:
            fd_out.close()

    if as_diff:
        cmd = f"meld {out_files[0]} {out_files[1]} &"
        misc.log_shell(cmd)
        os.system(cmd)


def find_git_repos(path=".", exclude=None):
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
        if ".git" in dirs:
            gitdirs.append(root)
            dirs.remove(".git")
        if ".git" in files:
            gitdirs.append(root)

    # remove "./" prefix from all paths
    dirs = []
    for path in gitdirs:
        dirs.append(path[2:] if path.startswith("./") else path)

    return sorted(dirs)


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
