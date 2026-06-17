"""
executor.py — Command execution engine for SmartShell.

Handles:
- Dispatching to built-in commands
- Running external programs via subprocess
- Full I/O redirection (stdin, stdout, stderr)
- Pipeline execution (cmd1 | cmd2 | cmd3)
"""

import os
import sys
import shutil
import subprocess

from app.parser import Command, Pipeline
from app.builtins import BUILTINS


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def execute_pipeline(pipeline: Pipeline) -> str | None:
    """
    Execute a full pipeline. Returns "EXIT" if the shell should terminate.
    """
    if pipeline.is_single:
        return _execute_single(pipeline.first)

    return _execute_pipe_chain(pipeline.commands)


# ---------------------------------------------------------------------------
# Single command execution
# ---------------------------------------------------------------------------

def _execute_single(cmd: Command) -> str | None:
    """Execute a single command with its redirects."""
    stdout_fh, stderr_fh = None, None
    stdin_fh  = None

    try:
        # Open file handles for redirection
        stdin_fh  = _open_input(cmd.stdin_file)
        stdout_fh = _open_output(cmd.stdout_file, cmd.stdout_append)
        stderr_fh = _open_output(cmd.stderr_file, cmd.stderr_append)

        # Build write callables that respect redirection
        def stdout_write(text: str):
            if stdout_fh:
                stdout_fh.write(text)
            else:
                sys.stdout.write(text)

        def stderr_write(text: str):
            if stderr_fh:
                stderr_fh.write(text)
            else:
                sys.stderr.write(text)

        name = cmd.tokens[0]
        args = cmd.tokens[1:]

        # --- Built-in ---
        if name in BUILTINS:
            result = BUILTINS[name](args, stdout_write, stderr_write)
            return result  # may be "EXIT" or None

        # --- External program ---
        exe = shutil.which(name)
        if exe:
            _run_external(cmd.tokens, stdin_fh, stdout_fh, stderr_fh)
        else:
            stderr_write(f"{name}: command not found\n")

    finally:
        for fh in (stdin_fh, stdout_fh, stderr_fh):
            if fh:
                fh.close()

    return None


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

def _execute_pipe_chain(commands: list) -> None:
    """
    Execute a list of Command objects as a pipeline using subprocess.Popen.

    cmd1 | cmd2 | cmd3
    - Each command's stdout is piped to the next command's stdin.
    - The first command inherits our stdin (or its own redirect).
    - The last command inherits our stdout (or its own redirect).
    - stderr is inherited by all (or redirected per command).
    """
    # Resolve any built-ins in the pipeline into wrapper scripts — complex
    # pipelines with built-ins on either end are handled by converting the
    # built-in output to a subprocess through piping via Python itself.
    # For simplicity and reliability: run built-ins by converting to subproc.

    processes = []
    prev_stdout = None

    for i, cmd in enumerate(commands):
        is_last = (i == len(commands) - 1)

        # stdin source
        if prev_stdout is not None:
            stdin_src = prev_stdout
        elif cmd.stdin_file:
            stdin_src = _open_input(cmd.stdin_file)
        else:
            stdin_src = None  # inherit

        # stdout destination
        if not is_last:
            stdout_dst = subprocess.PIPE
        elif cmd.stdout_file:
            stdout_dst = _open_output(cmd.stdout_file, cmd.stdout_append)
        else:
            stdout_dst = None  # inherit

        # stderr destination
        if cmd.stderr_file:
            stderr_dst = _open_output(cmd.stderr_file, cmd.stderr_append)
        else:
            stderr_dst = None  # inherit

        exe = shutil.which(cmd.tokens[0])
        if not exe:
            sys.stderr.write(f"{cmd.tokens[0]}: command not found\n")
            # Kill already-started processes
            for p in processes:
                p.kill()
            return

        proc = subprocess.Popen(
            cmd.tokens,
            stdin=stdin_src,
            stdout=stdout_dst,
            stderr=stderr_dst,
        )
        processes.append(proc)

        # Close the read end in the parent so the child owns it
        if prev_stdout and prev_stdout != subprocess.PIPE:
            try:
                prev_stdout.close()
            except Exception:
                pass

        prev_stdout = proc.stdout  # pipe for next stage

    # Wait for all processes to finish
    for proc in processes:
        proc.wait()


# ---------------------------------------------------------------------------
# External subprocess helper
# ---------------------------------------------------------------------------

def _run_external(tokens: list, stdin_fh, stdout_fh, stderr_fh):
    """Run an external command with optional file handle redirections."""
    subprocess.run(
        tokens,
        stdin=stdin_fh  or None,
        stdout=stdout_fh or None,
        stderr=stderr_fh or None,
    )


# ---------------------------------------------------------------------------
# File handle helpers
# ---------------------------------------------------------------------------

def _open_output(path: str | None, append: bool):
    """Open an output file for writing/appending. Returns None if path is None."""
    if path is None:
        return None
    _ensure_parent_dir(path)
    mode = "a" if append else "w"
    return open(path, mode)


def _open_input(path: str | None):
    """Open an input file for reading. Returns None if path is None."""
    if path is None:
        return None
    return open(path, "r")


def _ensure_parent_dir(path: str):
    """Create parent directories for a file path if they don't exist."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
