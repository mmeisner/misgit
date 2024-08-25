# misgit

`misgit` (Multi Info Summary of Git repos) is a small and simple command-line
program for collecting summary info over multiple git repositories.
It is written in python 3, it is quite small, and has no dependencies.

## Example Output

Here is an example:

```
$ misgit
path                        desc                branch  time      status
------------------------------------------------------------------------
jenkins-cli                 v0.1.0              main    1.7y      M1 ?6
misgit                      v0.1.0-16-gfe9d4ab  main        4.5d  ?1
openwrt-image-buildomatic   9466633             main      46.4w   ?4
repomaker                   v0.1.0              main    1.2y      M2 ?2
rspsu                       v0.1.0              main    1.0y
Listed 5 repos
```

And here is the help:
```
$ misgit -h
usage: misgit [-x DIR] [-d NUM] [-a] [-p] [-f FIELDS] [-m] [-t FORMAT] [-c BRANCH=COLOR] [--diff] [--pull] [-b]
              [-s SORTBY][-v] [-h]
              [DIR ...]

Show git summary info for all git repos below some folder (recursively)
For each repo found, shows: repo path, tag, branch, status

Main options:
  DIR              Folder(s) to search for git repos. Default is current dir.
                   If directory is suffixed with ':N' then the N first path components will be
                   removed when printing the repo path. This is especially useful with --diff option
  -x DIR           Exclude folder DIR. Relative to search folders (or absolute).
                   Can be given multiple times.
  -d NUM           Max depth of search

Output options:
  -a               Show almost all output columns
  -p               Show only git repo paths
  -f FIELDS        Fields/columns to show. Available ones: path,url,name,sub,desc,branch,time,status
  -m               Show more info. E.g. print list of files from 'git status'
  -t FORMAT        Format of committer date column: rel, date, time, none
  -c BRANCH=COLOR  Colorize branch column where BRANCH is a glob pattern, e.g.
                   'master=cyan,feature*=ired'
                   The '*' name/pattern acts as default color

Advanced options:
  --diff           Compare two trees (requires two DIRectory arguments)
  --pull           Pull all repos (with --rebase)

Other commands/options:
  -b               List branches of current repo with last commit date and author
  -s SORTBY        Sort branches by 'author', 'date' or 'branch' (default is 'date')

Misc options:
  -v               Be more verbose. E.g. print progress
  -h               Show this help message and exit

Examples:
  Compare two directories of git repos:
    misgit --diff ./foo:1 /home/joe/work/foo:4
  List repos excluding some folder (matching any folder in the hierarchy):
    misgit -x workdir
  List repos excluding specific folder:
    misgit -x workdir/foobaz
  List repos with specific branches colored:
    misgit -c'feat*=pink,bugfix*=ired'
  List branches (refs) of current repo:
    misgit -b

Colors (for -c option):
    bold dim red green yellow blue magenta cyan white ired igreen iyellow iblue imagenta icyan iwhite pink
```

## Installation

Install with:

```
pip install git+https://github.com/mmeisner/misgit.git
```
