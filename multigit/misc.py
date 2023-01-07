import os
import sys
import subprocess


def error(s):
    sys.stderr.write(s + os.linesep)


def log_shell(s):
    print(s)


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
