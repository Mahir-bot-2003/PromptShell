"""
parser.py — Command tokenization and structure parsing.

Handles:
- shlex tokenization
- I/O redirection: >, >>, 2>, 2>>, <
- Pipeline parsing: cmd1 | cmd2 | cmd3
- Environment variable expansion: $VAR, ${VAR}
"""

import os
import re
import shlex
from dataclasses import dataclass, field


@dataclass
class Command:
    """Represents a single parsed command (one stage in a pipeline)."""
    tokens: list          # [command, arg1, arg2, ...]
    stdin_file: str       = None
    stdout_file: str      = None
    stderr_file: str      = None
    stdout_append: bool   = False
    stderr_append: bool   = False


@dataclass
class Pipeline:
    """Represents a full pipeline of one or more commands."""
    commands: list = field(default_factory=list)  # list of Command

    @property
    def is_single(self):
        return len(self.commands) == 1

    @property
    def first(self):
        return self.commands[0]


def expand_variables(token: str) -> str:
    """Expand $VAR and ${VAR} references using os.environ."""
    # Match ${VAR} first, then $VAR
    def replacer(match):
        var_name = match.group(1) or match.group(2)
        return os.environ.get(var_name, "")

    return re.sub(r"\$\{(\w+)\}|\$(\w+)", replacer, token)


def parse_line(line: str) -> Pipeline | None:
    """
    Parse a raw input line into a Pipeline of Commands.

    Returns None if the line is empty or a comment.
    Raises ValueError on malformed input.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    try:
        tokens = shlex.split(line)
    except ValueError as e:
        raise ValueError(f"parse error: {e}") from e

    if not tokens:
        return None

    # Expand environment variables in each token
    tokens = [expand_variables(t) for t in tokens]

    # Split on pipe symbols to get individual command segments
    segments = _split_on_pipe(tokens)

    commands = []
    for seg in segments:
        cmd = _parse_redirects(seg)
        commands.append(cmd)

    return Pipeline(commands=commands)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _split_on_pipe(tokens: list) -> list:
    """Split a token list on '|' to produce multiple segments."""
    segments = []
    current = []
    for tok in tokens:
        if tok == "|":
            if not current:
                raise ValueError("syntax error near unexpected token '|'")
            segments.append(current)
            current = []
        else:
            current.append(tok)
    if not current:
        if segments:
            raise ValueError("syntax error near unexpected token '|'")
    else:
        segments.append(current)
    return segments


def _parse_redirects(tokens: list) -> Command:
    """
    Parse redirect operators out of a token list and return a Command.

    Supported operators (as standalone tokens or attached):
        >file  >>file  2>file  2>>file  <file  1>file  1>>file
    """
    cmd_tokens = []
    stdin_file = None
    stdout_file = None
    stderr_file = None
    stdout_append = False
    stderr_append = False

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        # --- stdout redirect ---
        if tok in (">", "1>"):
            stdout_file = _next_token(tokens, i)
            stdout_append = False
            i += 2
        elif tok in (">>", "1>>"):
            stdout_file = _next_token(tokens, i)
            stdout_append = True
            i += 2

        # --- stderr redirect ---
        elif tok == "2>":
            stderr_file = _next_token(tokens, i)
            stderr_append = False
            i += 2
        elif tok == "2>>":
            stderr_file = _next_token(tokens, i)
            stderr_append = True
            i += 2

        # --- input redirect ---
        elif tok == "<":
            stdin_file = _next_token(tokens, i)
            i += 2

        # --- attached redirect forms: >file, >>file, 2>file, 2>>file ---
        elif tok.startswith(">>") and len(tok) > 2:
            stdout_file = tok[2:]
            stdout_append = True
            i += 1
        elif tok.startswith(">") and len(tok) > 1 and not tok.startswith("2>"):
            stdout_file = tok[1:]
            stdout_append = False
            i += 1
        elif tok.startswith("2>>") and len(tok) > 3:
            stderr_file = tok[3:]
            stderr_append = True
            i += 1
        elif tok.startswith("2>") and len(tok) > 2:
            stderr_file = tok[2:]
            stderr_append = False
            i += 1

        else:
            cmd_tokens.append(tok)
            i += 1

    if not cmd_tokens:
        raise ValueError("empty command in pipeline")

    return Command(
        tokens=cmd_tokens,
        stdin_file=stdin_file,
        stdout_file=stdout_file,
        stderr_file=stderr_file,
        stdout_append=stdout_append,
        stderr_append=stderr_append,
    )


def _next_token(tokens: list, i: int) -> str:
    """Get the token after position i, raising ValueError if missing."""
    if i + 1 >= len(tokens):
        raise ValueError(f"syntax error: expected filename after '{tokens[i]}'")
    return tokens[i + 1]
