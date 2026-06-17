"""
builtins.py — All built-in shell commands for SmartShell.

Built-ins implemented:
    exit    — exit the shell
    echo    — print arguments
    pwd     — print working directory
    cd      — change directory
    type    — identify command type
    history — show/clear command history
    export  — set environment variable
    unset   — remove environment variable
    help    — show available commands + smart engine hints
"""

import os
import sys
import shutil

from app.history import print_history

# These names must match keys in BUILTINS dict at bottom of file
BUILTIN_NAMES = {"exit", "echo", "pwd", "cd", "type", "history", "export", "unset", "help", "setup-ai", "ls"}


# ---------------------------------------------------------------------------
# Individual command handlers
# Each handler signature: (args, stdout_write, stderr_write) -> str | None
#   args         — list of arguments (not including the command name itself)
#   stdout_write — callable to write to stdout (handles redirection)
#   stderr_write — callable to write to stderr (handles redirection)
# Returns "EXIT" to signal the shell should terminate.
# ---------------------------------------------------------------------------

def _exit(args, stdout_write, stderr_write):
    return "EXIT"


def _echo(args, stdout_write, stderr_write):
    stdout_write(" ".join(args) + "\n")


def _pwd(args, stdout_write, stderr_write):
    stdout_write(os.getcwd() + "\n")


def _cd(args, stdout_write, stderr_write):
    if not args:
        path = os.path.expanduser("~")
    else:
        path = os.path.expanduser(args[0])

    try:
        os.chdir(path)
    except FileNotFoundError:
        stderr_write(f"cd: {path}: No such file or directory\n")
    except NotADirectoryError:
        stderr_write(f"cd: {path}: Not a directory\n")
    except PermissionError:
        stderr_write(f"cd: {path}: Permission denied\n")


def _type(args, stdout_write, stderr_write):
    if not args:
        stderr_write("type: missing argument\n")
        return

    for name in args:
        if name in BUILTIN_NAMES:
            stdout_write(f"{name} is a shell builtin\n")
        elif found := shutil.which(name):
            stdout_write(f"{name} is {found}\n")
        else:
            stderr_write(f"{name}: not found\n")


def _history(args, stdout_write, stderr_write):
    print_history(args, stdout_write)


def _export(args, stdout_write, stderr_write):
    if not args:
        # Print all exported variables
        for key, val in sorted(os.environ.items()):
            stdout_write(f'export {key}="{val}"\n')
        return

    for arg in args:
        if "=" in arg:
            key, _, value = arg.partition("=")
            if not key.isidentifier():
                stderr_write(f"export: '{key}': not a valid identifier\n")
            else:
                os.environ[key] = value
        else:
            # export an already-existing variable (no-op if not set)
            if arg not in os.environ:
                stderr_write(f"export: '{arg}': not found in environment\n")


def _unset(args, stdout_write, stderr_write):
    if not args:
        stderr_write("unset: missing argument\n")
        return
    for name in args:
        os.environ.pop(name, None)


def _ls(args, stdout_write, stderr_write):
    """
    Cross-platform ls built-in.
    Supports -l, -a, -h flags (combined or separate).
    """
    import datetime

    target_dir = "."
    show_all = False
    long_format = False

    # Parse args
    for arg in args:
        if arg.startswith("-"):
            if "a" in arg: show_all = True
            if "l" in arg: long_format = True
            if "h" in arg: pass  # h is ignored, human-readable is default for long format
        else:
            target_dir = arg

    try:
        entries = os.listdir(target_dir)
    except FileNotFoundError:
        stderr_write(f"ls: {target_dir}: No such file or directory\n")
        return
    except NotADirectoryError:
        stderr_write(f"ls: {target_dir}: Not a directory\n")
        return
    except PermissionError:
        stderr_write(f"ls: {target_dir}: Permission denied\n")
        return

    if not show_all:
        entries = [e for e in entries if not e.startswith(".")]

    entries.sort(key=str.lower)

    if not long_format:
        # Simple print
        stdout_write("  ".join(entries) + "\n")
        return

    # Long format
    for entry in entries:
        path = os.path.join(target_dir, entry)
        try:
            stat = os.stat(path)
            is_dir = os.path.isdir(path)
            
            # Type char
            type_char = "d" if is_dir else "-"
            
            # Size (human readable)
            size = stat.st_size
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f}K"
            elif size < 1024 * 1024 * 1024:
                size_str = f"{size/(1024*1024):.1f}M"
            else:
                size_str = f"{size/(1024*1024*1024):.1f}G"

            # Time
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
            time_str = mtime.strftime("%b %d %H:%M")

            # Format: drwxr-xr-x  size  time  name
            # Fake permissions for cross-platform simplicity
            perms = type_char + "rwxr-xr-x" if is_dir else type_char + "rw-r--r--"
            
            stdout_write(f"{perms} {size_str:>8} {time_str} {entry}\n")
        except OSError:
            stdout_write(f"?---------        ? ?     ? {entry}\n")


def _setup_ai(args, stdout_write, stderr_write):
    """Interactive Gemini API key setup."""
    try:
        from app.gemini_ai import setup_api_key, is_configured
        if is_configured() and not args:
            stdout_write("  Gemini AI is already configured!\n")
            stdout_write("  Run `setup-ai --reset` to change the key.\n")
            return
        setup_api_key(stdout_write, stderr_write)
    except ImportError:
        stderr_write("  Error: gemini_ai module not found.\n")


def _help(args, stdout_write, stderr_write):
    # Check if Gemini is configured for the help text
    ai_status = "not configured"
    try:
        from app.gemini_ai import is_configured
        if is_configured():
            ai_status = "active"
    except ImportError:
        pass

    help_text = f"""
+--------------------------------------------------------------+
|            SmartShell -- Command Reference                   |
+--------------------------------------------------------------+

BUILT-IN COMMANDS:
  echo <text>          Print text to stdout
  pwd                  Show current directory
  cd <path>            Change directory  (cd ~ goes home)
  type <cmd>           Show if command is builtin or external
  export VAR=value     Set environment variable
  unset VAR            Remove environment variable
  history              Show command history
  history -c           Clear history
  history <N>          Show last N commands
  setup-ai             Set up Gemini AI (free, 15 req/min)
  help                 Show this help
  exit                 Exit the shell

I/O REDIRECTION:
  cmd > file           Redirect stdout (overwrite)
  cmd >> file          Redirect stdout (append)
  cmd 2> file          Redirect stderr (overwrite)
  cmd 2>> file         Redirect stderr (append)
  cmd < file           Redirect stdin from file
  cmd > out 2> err     Redirect both stdout and stderr

PIPELINES:
  cmd1 | cmd2          Pipe stdout of cmd1 to stdin of cmd2
  cmd1 | cmd2 | cmd3   Chain multiple pipes

ENVIRONMENT VARIABLES:
  echo $HOME           Expand environment variable
  echo ${{MY_VAR}}       Expand with braces
  export MY_VAR=hello  Set a variable
  unset MY_VAR         Remove a variable

SMART ENGINE (Natural Language):
  Just type plain English! No prefix needed.
  You can also use ? <request> if you prefer.

  Gemini AI: {ai_status}
  Run `setup-ai` to enable Gemini for unlimited understanding.

  Examples:
    find all python files
    what is the folder size
    show me the last 10 lines of server.log
    how much disk space is left
    show running processes
    compress the logs directory
    show git status
    ? --help             (show all rule patterns)

TAB COMPLETION:
  Press TAB once        -> auto-complete or ring bell
  Press TAB twice       -> list all matches

SHORTCUTS:
  Ctrl+C                -> cancel current line, new prompt
  Ctrl+D                -> exit shell
  Up / Down             -> navigate command history
"""
    stdout_write(help_text)


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

BUILTINS = {
    "exit":     _exit,
    "echo":     _echo,
    "pwd":      _pwd,
    "cd":       _cd,
    "type":     _type,
    "history":  _history,
    "export":   _export,
    "unset":    _unset,
    "ls":       _ls,
    "help":     _help,
    "setup-ai": _setup_ai,
}
