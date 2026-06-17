"""
history.py — Persistent command history with readline integration.

Features:
- Saves history to ~/.myshell_history on exit
- Restores history on startup (↑/↓ arrow navigation)
- `history` builtin shows numbered history list
- `history -c` clears history
"""

import os

# readline is Unix-only. On Windows, try pyreadline3, then fall back to a stub.
try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline  # pip install pyreadline3
    except ImportError:
        # Minimal no-op stub so the rest of the code works without history
        class _ReadlineStub:
            def set_history_length(self, n): pass
            def read_history_file(self, f): pass
            def write_history_file(self, f): pass
            def get_history_length(self): return 0
            def get_current_history_length(self): return 0
            def get_history_item(self, i): return ""
            def clear_history(self): pass
            def add_history(self, line): pass
            def parse_and_bind(self, s): pass
            def set_completer(self, fn): pass
            def set_completer_delims(self, s): pass
            def get_line_buffer(self): return ""
            def get_begidx(self): return 0
        readline = _ReadlineStub()

HISTORY_FILE = os.path.expanduser("~/.myshell_history")
MAX_HISTORY = 1000


def init_history():
    """Load history file and configure readline."""
    readline.set_history_length(MAX_HISTORY)
    if os.path.exists(HISTORY_FILE):
        try:
            readline.read_history_file(HISTORY_FILE)
        except OSError:
            pass  # File unreadable — start fresh


def save_history():
    """Persist history to disk. Call this on shell exit."""
    try:
        readline.write_history_file(HISTORY_FILE)
    except OSError:
        pass


def add_entry(line: str):
    """Add a line to the in-memory history (readline tracks this automatically,
    but this wrapper exists for clarity and future hooks)."""
    # readline.add_history is called automatically by input()
    # We keep this function as an explicit hook point.
    pass


def get_history() -> list:
    """Return all history entries as a list of strings."""
    return [
        readline.get_history_item(i)
        for i in range(1, readline.get_current_history_length() + 1)
    ]


def print_history(args: list, stdout_write):
    """
    Handle the `history` builtin command.

    history        — show all entries
    history -c     — clear history
    history <N>    — show last N entries
    """
    if args and args[0] == "-c":
        readline.clear_history()
        stdout_write("History cleared.\n")
        return

    entries = get_history()

    if args:
        try:
            n = int(args[0])
            entries = entries[-n:]
            start_index = max(1, readline.get_current_history_length() - n + 1)
        except ValueError:
            stdout_write(f"history: invalid option: {args[0]}\n")
            return
    else:
        start_index = 1

    for idx, entry in enumerate(entries, start=start_index):
        stdout_write(f"  {idx:4d}  {entry}\n")
