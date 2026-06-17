"""
shell.py -- REPL loop and signal handling for SmartShell.

Responsibilities:
- Print the prompt and read input
- Handle Ctrl+C (SIGINT) gracefully
- Handle Ctrl+D (EOF) gracefully
- Dispatch lines to the parser + executor
- Auto-detect natural language when command is not found
- Handle the `?` smart engine prefix
"""

import os
import sys
import shutil
import signal

from app.parser    import parse_line
from app.executor  import execute_pipeline
from app.history   import init_history, save_history
from app.completer import setup_completer
from app.builtins  import BUILTIN_NAMES
from app.smart     import handle_smart_query


# ---------------------------------------------------------------------------
# Signal handling
# ---------------------------------------------------------------------------

def _sigint_handler(signum, frame):
    """Ctrl+C: print a newline and return to the prompt."""
    sys.stdout.write("\n")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Command detection
# ---------------------------------------------------------------------------

def _is_known_command(word: str) -> bool:
    """Check if a word is a known builtin or an executable on PATH."""
    if word in BUILTIN_NAMES:
        return True
    if shutil.which(word):
        return True
    return False


# ---------------------------------------------------------------------------
# Smart query executor (bridge to executor)
# ---------------------------------------------------------------------------

def _smart_execute(command_str: str):
    """Execute a command string from the smart engine."""
    try:
        pipeline = parse_line(command_str)
        if pipeline:
            execute_pipeline(pipeline)
    except Exception as e:
        sys.stderr.write(f"Error executing smart command: {e}\n")


# ---------------------------------------------------------------------------
# Main REPL
# ---------------------------------------------------------------------------

def run():
    """Start the SmartShell REPL. Runs until the user exits."""

    # Set up Ctrl+C to return to prompt instead of crashing
    signal.signal(signal.SIGINT, _sigint_handler)

    # Initialize tab completion
    setup_completer(BUILTIN_NAMES)

    # Load persistent command history (enables up/down navigation)
    init_history()

    # Print welcome banner
    _print_banner()

    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            line = input()
        except EOFError:
            # Ctrl+D -- exit gracefully
            sys.stdout.write("exit\n")
            break
        except KeyboardInterrupt:
            # Ctrl+C between prompts
            sys.stdout.write("\n")
            continue

        line = line.strip()

        # Empty line
        if not line:
            continue

        # ---------------------------------------------------------------
        # EXPLICIT smart engine -- lines starting with `?`
        # ---------------------------------------------------------------
        if line.startswith("?"):
            query = line[1:].strip()
            handled = handle_smart_query(
                query,
                execute_fn=_smart_execute,
                stdout_write=sys.stdout.write,
                stderr_write=sys.stderr.write,
            )
            if not handled:
                sys.stdout.write(
                    "  I don't understand that request.\n"
                    "  Type `? --help` for all available patterns.\n"
                )
            continue

        # ---------------------------------------------------------------
        # Check if the first word is a known command
        # If NOT -> try the smart engine AUTOMATICALLY before failing
        # ---------------------------------------------------------------
        first_word = line.split()[0] if line.split() else ""

        if not _is_known_command(first_word):
            # Looks like natural language -- try smart engine
            handled = handle_smart_query(
                line,
                execute_fn=_smart_execute,
                stdout_write=sys.stdout.write,
                stderr_write=sys.stderr.write,
            )
            if handled:
                continue
            # Smart engine didn't match either -> fall through to normal
            # execution which will show "command not found"

        # ---------------------------------------------------------------
        # Normal command: parse and execute
        # ---------------------------------------------------------------
        try:
            pipeline = parse_line(line)
            if pipeline is None:
                continue
        except ValueError as e:
            sys.stderr.write(f"myshell: {e}\n")
            continue

        try:
            result = execute_pipeline(pipeline)
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            continue
        except Exception as e:
            sys.stderr.write(f"myshell: {e}\n")
            continue

        if result == "EXIT":
            break

    # Save history before exiting
    save_history()


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def _print_banner():
    banner = (
        "\n"
        "  ======================================================\n"
        "   SmartShell  --  Python Shell Built From Scratch\n"
        "  ======================================================\n"
        "  Pipelines | I/O Redirection | Env Vars | Smart Engine\n"
        "\n"
        "  Type  help             for all commands\n"
        "  Type plain English     to use the smart engine\n"
        "                         e.g. find all python files\n"
        "                         e.g. what is the folder size\n"
        "  Type  exit             or press Ctrl+D to quit\n"
        "  ======================================================\n"
    )
    sys.stdout.write(banner + "\n")
