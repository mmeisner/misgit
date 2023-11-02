#!/usr/bin/env python3
# Extract git summary info across multiple git repos below some folder (recursively)
# tags: git

import argparse

from . import gitops
from . import misc
from .misc import Ansi


ALL_FIELDS = "path,url,name,sub,desc,lasttag,branch,time,status,msg"
DEFAULT_FIELDS = "path,sub,desc,branch,time,status,msg"
BRANCH_COLORS = {
    "main": "",
    "master": "",
    "*": "green",
}

opt = argparse.Namespace()

def main():
    global opt
    opt = parser_create().parse_args()
    misc.verbose = opt.verbose

    # We don't want any ANSI codes when writing output to a file
    if opt.diff:
        Ansi.set_no_colors()

    dirargs = opt.posargs
    if not dirargs:
        dirargs = ["."]

    excludes = opt.exclude

    if opt.fields_show_all:
        fields = ALL_FIELDS.replace("name,", "")
    else:
        fields = opt.fields

    if opt.only_path:
        fields = ""
    if opt.timeformat.startswith("n"):
        fields.replace("time,", "")

    branch_colors = get_branch_colors()

    misc.progress_start()

    if opt.pull:
        gitops.pull_repos(dirargs, excludes, depth=opt.maxdepth)
    else:
        gitops.list_repos(dirargs, excludes, depth=opt.maxdepth,
                          fields=fields, timeformat=opt.timeformat,
                          as_diff=opt.diff, more_info=opt.more_info,
                          branch_colors=branch_colors)


examples = f"""Examples:
  Compare two directories of git repos:
    %(prog)s --diff ./foo:1 /home/joe/work/foo:4
  List repos excluding some folder (matching any folder in the hierarchy):
    %(prog)s -x workdir
  List repos excluding specific folder:
    %(prog)s -x workdir/foobaz
  List repos with specific branches colored:
    %(prog)s -c'feat*=pink,bugfix*=ired'

Colors (for -c option):
    {Ansi.get_colors()}
"""

def parser_create():
    description = f"""
Show git summary info for all git repos below some folder (recursively) 

For each repo found, shows: {DEFAULT_FIELDS}
All available fields are:   {ALL_FIELDS}
"""
    parser = argparse.ArgumentParser(
        description=description, epilog=examples, add_help=False, formatter_class=argparse.RawTextHelpFormatter)

    g = parser.add_argument_group("Main options")
    g.add_argument(dest='posargs', metavar='DIR', type=str, nargs="*",
        help=f"""Folder(s) to search for git repos. Default is current dir.
If directory is suffixed with ':N' then the N first path components will be
removed when printing the repo path. This is especially useful with --diff option""")
    g.add_argument("-x", dest='exclude', metavar='DIR', type=str, action="append",
        help=f"""Exclude folder DIR. Relative to search folders (or absolute).
Can be given multiple times.""")
    g.add_argument("-d", dest='maxdepth', metavar='NUM', type=int, default=999,
        help=f"Max depth of search")

    g = parser.add_argument_group("Output options")
    g.add_argument('-a', dest='fields_show_all', action="store_true",
        help="Show almost all output columns")
    g.add_argument('-p', dest='only_path', action="store_true",
        help="Show only git repo paths")
    g.add_argument('-f', dest='fields', type=str, default=DEFAULT_FIELDS,
        help=f"Fields/columns to show. Available ones: {ALL_FIELDS}")
    g.add_argument('-m', dest='more_info', action="store_true",
        help="Show more info. E.g. print list of files from 'git status'")
    g.add_argument('-t', dest='timeformat', metavar="FORMAT", type=str, default="rel",
        help="Format of committer date column: rel, date, time, none")
    g.add_argument('-c', dest='branch_color', type=str, metavar="BRANCH=COLOR",
        help="""\
Colorize branch column where BRANCH is a glob pattern, e.g.
'master=cyan,feature*=ired'
The '*' name/pattern acts as default color""")

    g = parser.add_argument_group("Advanced options")
    g.add_argument('--diff', dest='diff', action='store_true', default=False,
        help="Compare two trees (requires two DIRectory arguments)")
    g.add_argument('--pull', dest='pull', action='store_true', default=False,
        help="Pull all repos (with --rebase)")

    g = parser.add_argument_group("Misc options")
    g.add_argument('-v', dest='verbose', action='count', default=0,
        help="Be more verbose. E.g. print progress")
    g.add_argument('-h', action='help',
        help="Show this help message and exit")

    return parser


def get_branch_colors():
    branch_colors = BRANCH_COLORS.copy()
    if opt.branch_color:
        if "," in opt.branch_color:
            items = opt.branch_color.split(",")
        else:
            items = [opt.branch_color]

        for branch_color in items:
            if "=" in branch_color:
                branch, color = branch_color.split("=")
            else:
                branch, color = branch_color, "iyellow"
            branch_colors[branch] = color

    for name in branch_colors.keys():
        ansi_name = branch_colors[name]
        if ansi_name:
            branch_colors[name] = Ansi.name_to_code(ansi_name)

    return branch_colors
