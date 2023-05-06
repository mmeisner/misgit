import os
import sys
import subprocess


term_cols = 0
verbose = False


class Ansi:
    reset = "\033[0m"
    bold = "\033[1m"
    dim = "\033[2m"

    red = "\033[31m"
    green = "\033[32m"
    yellow = "\033[33m"
    blue = "\033[34m"
    magenta = "\033[35m"
    cyan = "\033[36m"
    white = "\033[37m"

    ired = "\033[91m"
    igreen = "\033[92m"
    iyellow = "\033[93m"
    iblue = "\033[94m"
    imagenta = "\033[95m"
    icyan ="\033[96m"
    iwhite ="\033[97m"

    pink = "\33[38:5:206m"

    @classmethod
    def name_to_code(cls, name):
        return Ansi.__dict__[name] or ""

    @classmethod
    def get_colors(cls):
        s = ""
        for k, code in Ansi.__dict__.items():
            if type(Ansi.__dict__[k]) == str and not k.startswith("__") and k != "reset":
                s += f"{code}{k}{Ansi.reset} "

        return s


def print_dim(s, file=None):
    print(f"{Ansi.dim}{s}{Ansi.reset}", file=file)

def print_lite(s, file=None):
    print(f"{Ansi.bold}{Ansi.iwhite}{s}{Ansi.reset}", file=file)

def error(s):
    sys.stderr.write(s + os.linesep)

def log_shell(s):
    print(s)


def progress_start():
    global term_cols
    if sys.stdout.isatty():
        term_cols, rows = os.get_terminal_size(0)

def progress_end():
    if verbose and term_cols:
        sys.stderr.write(" " * term_cols + "\r")

def progress_print(s):
    if verbose and term_cols:
        s = s[:term_cols - 1]
        sys.stderr.write(s + "\r")


def git_get_sha_branch_describe(repo_path: str, what="hbd"):
    root = cmd_run_get_output(f"git -C {repo_path} rev-parse --show-toplevel", on_error="")
    # SHA
    sha = cmd_run_get_output(f"git -C {repo_path} rev-parse --short HEAD", on_error="")
    # Current branch (if any)
    branch = cmd_run_get_output(f"git -C {repo_path} branch --show-current", on_error="")
    # Describe string like "3.12.0-10-ge678cf4" or "3.12.1" or "063924e"
    desc = cmd_run_get_output(f"git -C {repo_path} describe --tags --always", on_error="")
    return root, sha, branch, desc


def cmd_run_get_output(cmd: str, cwd=None, splitlines=False, on_error="raise"):
    """
    Run `cmd` in directory `cwd` and return output stripped for newline

    If `splitlines` is True, multiline output is expected and output will be a
    list of lines (without newline character)

    :param cmd: command to run
    :param cwd: directory in which to run the command
    :param splitlines: True to return lines as a list
    :param on_error: Value (or exception to raise) on error, i.e. if command fails
    :return:
    """
    # Using universal_newlines=True converts the output to a string instead of a byte array
    # From Python 3.7 we can use the more intuitive text=True instead of universal_newlines
    process = subprocess.run(
        cmd, shell=True, cwd=cwd,
        encoding="utf8", universal_newlines=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode != 0:
        if on_error == "raise":
            on_error = RuntimeError
        if isinstance(on_error, type(Exception)):
            raise on_error(f"Command failed: {cmd}\n{process.stderr}")
        return on_error

    if splitlines:
        return process.stdout.splitlines()

    return process.stdout.strip()


def secs_to_human_str(secs, indent="  "):
    """
    Format number of seconds into a short human-readable timespan like one of
    the following: "10.8y", "20.3w", "10.8d", "22.9h", "15.1m"

    :param secs:   Delta seconds
    :param indent: String to use as indent: more recent timestamps are indented more
    :return:
    """
    intervals = (
        (3600,                            60, "{v:.1f}m"),
        (3600 * 24,                     3600, "{v:.1f}h"),
        (3600 * 24 * 14,           24 * 3600, "{v:.1f}d"),
        (3600 * 24 * 7 * 52,   7 * 24 * 3600, "{v:.1f}w"),
        (3600 * 9999,        365 * 24 * 3600, "{v:.1f}y")
    )

    limit, div, fmt = intervals[-1]
    i = len(intervals)
    for i, (limit, div, fmt) in enumerate(intervals, start=1):
        if secs < limit:
            break

    v = secs / div
    indent = indent * (len(intervals) - i)
    return indent + fmt.format(v=v)
