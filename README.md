# misgit

`misgit` (Multi Info Summary of Git repos) is a small and simple command-line
program for collecting summary info over multiple git repositories.
It is written in python 3, it is quite small, and has no dependencies.

## Example Output

Here is an example:

```
$ misgit
path                      desc    branch status
benchmark-ab              c0bafbb main
jenkins-cli               e301f85 main   M1 ?8
logadoo                   b9cfb67 main   M1 ?2
misgit                    d790567 main   M1
openwrt-image-buildomatic 9466633 main   ?4
repomaker                 v0.1.0  main   M2 ?2
rspsu                     v0.1.0  main
```

And here is the help:
```
$ misgit -h
usage: misgit [-x DIR] [--diff] [-p] [-h] [DIR [DIR ...]]

Show git summary info for all git repos below some folder (recursively)
For each repo found, shows: repo path, tag, branch, status

Main options:
  DIR     Folder(s) to search for git repos. Default is current dir
  -x DIR  Exclude folder. Relative to search folders (or absolute).
          Can be given multiple times.
  --diff  Compare two trees (requires two DIRectory arguments)
  -p      Show only git repo paths

Misc options:
  -h      Show this help message and exit

Examples:
  Compare two directories of git repos:
    ./misgit --diff foo baz
```

## Installation

Install with:

```
pip install git+https://github.com/mmeisner/misgit.git
```
