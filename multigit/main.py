#!/usr/bin/env python3
# Extract git summary info across multiple git repos below some folder (recursively)
# tags: git

import argparse

from . import gitops
from . import misc


ALL_FIELDS = "path,url,name,desc,sub,branch,time,status"
DEFAULT_FIELDS = "path,desc,sub,branch,time,status"

opt = argparse.Namespace()

def main():
    global opt
    opt = parser_create().parse_args()
    misc.verbose = opt.verbose

    dirargs = opt.posargs
    if not dirargs:
        dirargs = ["."]

    excludes = opt.exclude
    fields = opt.fields

    if opt.only_path:
        fields = ""
    if opt.timeformat.startswith("n"):
        fields.replace("time,", "")

    misc.progress_start()

    if opt.pull:
        gitops.pull_repos(dirargs, excludes, depth=opt.maxdepth)
    else:
        gitops.list_repos(dirargs, excludes, depth=opt.maxdepth,
                          fields=fields, timeformat=opt.timeformat,
                          as_diff=opt.diff, more_info=opt.more_info)


examples = f"""Examples:
  Compare two directories of git repos:
    ./%(prog)s --diff foo baz
  List repos excluding some folder (matching any folder in the hierarchy):
    ./%(prog)s -x workdir
  List repos excluding top-level folder:
    ./%(prog)s -x workdir/foobaz
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
        help=f"""Exclude folder DIR. Relative to search folders (or absolute). Can be given multiple times.""")
    g.add_argument("-d", dest='maxdepth', metavar='NUM', type=int, default=999,
        help=f"Max depth of search")

    g = parser.add_argument_group("Output options")
    g.add_argument('-p', dest='only_path', action="store_true",
        help="Show only git repo paths")
    g.add_argument('-f', dest='fields', type=str, default=DEFAULT_FIELDS,
        help=f"Fields/columns to show. Available ones: {ALL_FIELDS}")
    g.add_argument('-m', dest='more_info', action="store_true",
        help="Show more info. E.g. print list of files from 'git status'")
    g.add_argument('-t', dest='timeformat', metavar="FORMAT", type=str, default="rel",
        help="Format of committer date column: rel, date, time, none")

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
