"""
completer.py — Tab completion for SmartShell.

Features:
- Command completion (builtins + PATH executables)
- Argument/path completion with directory trailing slash
- LCP (longest common prefix) auto-fill
- Double-tab lists all matches; first tab rings bell
"""

import os
import sys

# readline is Unix-only. On Windows, try pyreadline3, then fall back to a stub.
try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline  # pip install pyreadline3
    except ImportError:
        class _ReadlineStub:
            def parse_and_bind(self, s): pass
            def set_completer(self, fn): pass
            def set_completer_delims(self, s): pass
            def get_line_buffer(self): return ""
            def get_begidx(self): return 0
        readline = _ReadlineStub()

_last_prefix = None
_tab_count   = 0

# Populated by shell.py after builtins are known
BUILTIN_NAMES: set = set()


def get_all_commands() -> list:
    """Return sorted list of all known commands (builtins + PATH executables)."""
    cmds = set(BUILTIN_NAMES)
    for folder in os.environ.get("PATH", "").split(os.pathsep):
        if not folder:
            continue
        try:
            for name in os.listdir(folder):
                full = os.path.join(folder, name)
                if os.path.isfile(full) and os.access(full, os.X_OK):
                    cmds.add(name)
        except OSError:
            pass
    return sorted(cmds)


def _longest_common_prefix(words: list) -> str:
    """Return the longest string that is a prefix of all words."""
    if not words:
        return ""
    for i in range(len(words[0])):
        char = words[0][i]
        for word in words:
            if i >= len(word) or word[i] != char:
                return words[0][:i]
    return words[0]


def _path_matches(text: str) -> tuple:
    """
    Given a partial path text, return (matches, directory, prefix).
    matches  — list of matching names (basenames)
    directory — the directory part of text
    prefix    — the basename prefix being completed
    """
    if "/" in text or os.sep in text:
        # Normalize to forward slash for splitting
        sep = "/" if "/" in text else os.sep
        directory, _, prefix = text.rpartition(sep)
        search_dir = directory if directory else (sep if text.startswith(sep) else ".")
    else:
        search_dir, directory, prefix = ".", "", text

    try:
        names = os.listdir(search_dir)
        matches = sorted(n for n in names if n.startswith(prefix))
    except OSError:
        matches = []

    return matches, search_dir, directory, prefix


def _complete_path(text: str, search_dir: str, directory: str, matches: list) -> str | None:
    """Build the full completion string from a path match."""
    def _build(name):
        full = os.path.join(search_dir, name)
        suffix = "/" if os.path.isdir(full) else " "
        if directory:
            return directory + "/" + name + suffix
        if text.startswith("/"):
            return "/" + name + suffix
        return name + suffix

    return _build


def command_completer(text: str, state: int):
    """
    readline completer function.
    Called repeatedly with state=0,1,2,... until None is returned.
    We do all work on state==0 and return None for state>0.
    """
    global _last_prefix, _tab_count

    if state != 0:
        return None

    line  = readline.get_line_buffer()
    begin = readline.get_begidx()

    # ------------------------------------------------------------------ #
    # ARGUMENT COMPLETION (cursor is not at the first word)               #
    # ------------------------------------------------------------------ #
    if begin > 0:
        matches, search_dir, directory, prefix = _path_matches(text)

        if not matches:
            _last_prefix, _tab_count = None, 0
            return None

        build = _complete_path(text, search_dir, directory, matches)

        if len(matches) == 1:
            _last_prefix, _tab_count = None, 0
            return build(matches[0])

        lcp_name = _longest_common_prefix(matches)
        if len(lcp_name) > len(prefix):
            _last_prefix, _tab_count = None, 0
            # Return the lcp without a trailing space/slash (ambiguous)
            if directory:
                return directory + "/" + lcp_name
            if text.startswith("/"):
                return "/" + lcp_name
            return lcp_name

        # Multiple matches, LCP exhausted
        if _last_prefix == text:
            _tab_count += 1
        else:
            _last_prefix, _tab_count = text, 1

        if _tab_count == 1:
            sys.stdout.write("\x07")  # bell
        else:
            display = []
            for n in matches:
                full = os.path.join(search_dir, n)
                display.append(n + "/" if os.path.isdir(full) else n)
            sys.stdout.write("\n" + "  ".join(display) + "\n")
            sys.stdout.write("$ " + line)
            _tab_count = 0

        sys.stdout.flush()
        return None

    # ------------------------------------------------------------------ #
    # COMMAND COMPLETION (cursor is at the first word)                    #
    # ------------------------------------------------------------------ #
    matches = [c for c in get_all_commands() if c.startswith(text)]

    if not matches:
        _last_prefix, _tab_count = None, 0
        return None

    if len(matches) == 1:
        _last_prefix, _tab_count = None, 0
        return matches[0] + " "

    lcp = _longest_common_prefix(matches)
    if len(lcp) > len(text):
        _last_prefix, _tab_count = None, 0
        return lcp

    if _last_prefix == text:
        _tab_count += 1
    else:
        _last_prefix, _tab_count = text, 1

    if _tab_count == 1:
        sys.stdout.write("\x07")
    else:
        sys.stdout.write("\n" + "  ".join(matches) + "\n")
        sys.stdout.write("$ " + line)
        _tab_count = 0

    sys.stdout.flush()
    return None


def setup_completer(builtin_names: set):
    """Initialize readline tab completion. Call once on startup."""
    global BUILTIN_NAMES
    BUILTIN_NAMES = builtin_names
    readline.parse_and_bind("tab: complete")
    readline.set_completer(command_completer)
    readline.set_completer_delims(" \t\n")
