"""
smart.py -- Rule-based Natural Language Smart Engine for SmartShell.

Works TWO ways:
  1. Explicit: type `?` before your request
  2. Automatic: just type plain English -- if it's not a known command,
     the smart engine kicks in automatically

No API keys, no internet, no dependencies -- 100% offline.

How it works:
  1. User's query is lowercased and synonyms are expanded
  2. Each Rule has trigger keywords -- scored by how many match
  3. Best-scoring rule wins (minimum threshold required)
  4. Command is shown to user for confirmation before execution
"""

import os
import re
import sys
from dataclasses import dataclass
from typing import Callable


# ---------------------------------------------------------------------------
# Synonym expansion -- this is what makes natural language flexible
# ---------------------------------------------------------------------------

# Maps common alternative words to canonical keywords used in rules.
# "directory" -> "folder", "show" -> "list", etc.
SYNONYMS = {
    # folder/directory
    "directory":   "folder",
    "directories": "folder",
    "dir":         "folder",
    "dirs":        "folder",
    "folders":     "folder",
    # file
    "files":       "file",
    # find/search/look/locate
    "search":      "find",
    "locate":      "find",
    "look":        "find",
    "where":       "find",
    "show":        "list",
    "display":     "list",
    "view":        "list",
    "see":         "list",
    "tell":        "list",
    "give":        "list",
    "print":       "list",
    # size
    "sizes":       "size",
    "weight":      "size",
    "big":         "large",
    "biggest":     "largest",
    "huge":        "large",
    "heavy":       "large",
    # process
    "processes":   "process",
    "program":     "process",
    "programs":    "process",
    "task":        "process",
    "tasks":       "process",
    "app":         "process",
    "apps":        "process",
    # disk
    "storage":     "disk",
    "drive":       "disk",
    # memory / ram
    "ram":         "memory",
    "mem":         "memory",
    # delete/remove
    "remove":      "delete",
    "erase":       "delete",
    "destroy":     "delete",
    "rm":          "delete",
    # create/make/new
    "make":        "create",
    "new":         "create",
    "add":         "create",
    "mkdir":       "create",
    # copy
    "duplicate":   "copy",
    "clone":       "copy",
    # rename/move
    "mv":          "move",
    # count/number
    "number":      "count",
    "total":       "count",
    "many":        "count",
    "how many":    "count",
    # hidden
    "dotfiles":    "hidden",
    "dotfile":     "hidden",
    # running
    "active":      "running",
    "alive":       "running",
    # kill/stop/end/terminate
    "stop":        "kill",
    "terminate":   "kill",
    "end":         "kill",
    "close":       "kill",
    # compress
    "archive":     "compress",
    "backup":      "compress",
    # extract
    "uncompress":  "extract",
    "decompress":  "extract",
    "unpack":      "extract",
    # ip
    "ip":          "ip",
    "ipaddress":   "ip",
    # current
    "present":     "current",
    "my":          "current",
    # line
    "lines":       "line",
    # word
    "words":       "word",
    # last/recent
    "recent":      "last",
    "latest":      "last",
    "newest":      "last",
    "tail":        "last",
    # first/top/beginning
    "beginning":   "first",
    "start":       "first",
    "head":        "first",
    "top":         "first",
    # empty/clear/truncate
    "truncate":    "empty",
    "wipe":        "empty",
    "blank":       "empty",
}


def _expand_synonyms(text: str) -> str:
    """Replace synonyms in the query with their canonical form."""
    words = text.lower().split()
    expanded = []
    for w in words:
        canonical = SYNONYMS.get(w, w)
        expanded.append(canonical)
    return " ".join(expanded)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    """
    A single smart-engine rule.

    match_words : list of keyword strings -- scored by how many appear
    resolver    : callable(query: str) -> str -- returns the shell command
    description : short human-readable description
    min_match   : minimum number of match_words that must appear (default: all)
    """
    match_words: list
    resolver: Callable
    description: str
    min_match: int = 0   # 0 means "all must match"

    @property
    def required(self):
        return self.min_match if self.min_match > 0 else len(self.match_words)


# ---------------------------------------------------------------------------
# Resolver helpers
# ---------------------------------------------------------------------------

def _extract_filename(query: str) -> str:
    """Try to find a filename/path mentioned in the query."""
    patterns = [
        r"(?:in|of|for|from|called|named|file)\s+([\w./\-]+\.\w+)",
        r"([\w./\-]+\.\w+)",
        r"(?:called|named|folder|directory|dir)\s+([\w./\-]+)",
    ]
    for p in patterns:
        m = re.search(p, query, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def _extract_number(query: str) -> str:
    """Extract first integer from query."""
    m = re.search(r"\b(\d+)\b", query)
    return m.group(1) if m else ""


def _extract_port(query: str) -> str:
    """Extract a port number from query."""
    m = re.search(r"\bport\s*:?\s*(\d+)\b", query, re.IGNORECASE)
    return m.group(1) if m else _extract_number(query)


def _extract_extension(query: str) -> str:
    """Extract a file extension like .py .txt .log."""
    m = re.search(r"\.(py|txt|log|csv|json|yaml|yml|sh|md|html|css|js|ts|go|java|c|cpp|h)\b",
                  query, re.IGNORECASE)
    if m:
        return m.group(0)
    lang_map = {
        "python": ".py", "javascript": ".js", "typescript": ".ts",
        "java": ".java", "c++": ".cpp", "cpp": ".cpp", "go": ".go",
        "rust": ".rs", "shell": ".sh", "bash": ".sh", "markdown": ".md",
        "yaml": ".yaml", "json": ".json", "html": ".html", "css": ".css",
        "text": ".txt", "log": ".log",
    }
    for word, ext in lang_map.items():
        if word in query.lower():
            return ext
    return "*"


def _extract_dir(query: str) -> str:
    """Extract a directory/folder name from query."""
    # Special case: Windows "x drive"
    drive_m = re.search(r"\b([a-zA-Z])\s+drive\b", query, re.IGNORECASE)
    if drive_m:
        return f"{drive_m.group(1).upper()}:/"

    m = re.search(
        r"(?:folder|directory|dir|called|named|of|in)\s+([\w./\-:]+)",
        query, re.IGNORECASE
    )
    if m:
        val = m.group(1)
        # filter out noise words
        if val.lower() not in ("the", "this", "a", "an", "my", "all", "that", "it", "drive"):
            return val
    return "."


def _extract_search_term(query: str) -> str:
    """Extract a search term/pattern from query."""
    m = re.search(r"(?:for|containing|with|pattern|text|string)\s+['\"]?(\S+)['\"]?",
                  query, re.IGNORECASE)
    if m:
        return m.group(1)
    return "PATTERN"


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

RULES: list = []


def _r(match_words, resolver, description, min_match=0):
    RULES.append(Rule(
        match_words=match_words,
        resolver=resolver,
        description=description,
        min_match=min_match,
    ))


# === FILE SEARCH ===
_r(["find", "file"],
   lambda q: f"find . -name '*{_extract_extension(q)}' -type f",
   "find files: ? find all python files")
_r(["find"],
   lambda q: f"find . -name '*{_extract_extension(q)}' -type f" if _extract_extension(q) != "*" else "find . -type f",
   "find anything: ? find python files",
   min_match=1)
_r(["search", "content"],
   lambda q: f'grep -r "{_extract_search_term(q)}" .',
   "search inside files: ? search for TODO in files",
   min_match=1)
_r(["grep"],
   lambda q: f'grep -r "{_extract_search_term(q)}" .',
   "grep: ? grep for error in logs")
_r(["large", "file"],
   lambda q: "find . -type f -size +10M | sort",
   "find large files: ? show large files",
   min_match=1)
_r(["last", "modified"],
   lambda q: f"find . -type f -mtime -{_extract_number(q) or '7'} | sort",
   "recently modified: ? files modified in last 7 days",
   min_match=1)

# === DISK / STORAGE / SIZE ===
_r(["disk", "space"],
   lambda q: "df -h",
   "disk space: ? how much disk space is left",
   min_match=1)
_r(["size", "folder"],
   lambda q: f"du -sh {_extract_dir(q)}",
   "folder size: ? what is the size of this folder",
   min_match=1)
_r(["size", "file"],
   lambda q: f"du -sh {_extract_dir(q)}",
   "file size: ? size of all files")
_r(["size"],
   lambda q: f"du -sh {_extract_dir(q)}",
   "size of anything: ? tell me size of this",
   min_match=1)
_r(["largest", "folder"],
   lambda q: "du -sh */ 2>/dev/null | sort -rh | head -10",
   "largest folders: ? which folders are biggest")
_r(["free", "memory"],
   lambda q: "free -h",
   "free memory: ? how much free memory",
   min_match=1)
_r(["space"],
   lambda q: "df -h",
   "storage space: ? how much space is left",
   min_match=1)

# === PROCESSES ===
_r(["running", "process"],
   lambda q: "ps aux",
   "running processes: ? show running processes",
   min_match=1)
_r(["list", "process"],
   lambda q: "ps aux",
   "list processes: ? list all processes",
   min_match=1)
_r(["cpu", "process"],
   lambda q: "ps aux --sort=-%cpu | head -10",
   "top cpu: ? which processes use the most cpu",
   min_match=1)
_r(["memory", "process"],
   lambda q: "ps aux --sort=-%mem | head -10",
   "top memory: ? which processes use the most memory",
   min_match=1)
_r(["kill", "port"],
   lambda q: f"lsof -ti:{_extract_port(q)} | xargs kill -9",
   "kill port: ? kill port 8080")
_r(["kill", "process"],
   lambda q: f"kill -9 {_extract_number(q) or 'PID'}",
   "kill process: ? kill process 1234")
_r(["listening", "port"],
   lambda q: f"lsof -i :{_extract_port(q)}" if _extract_port(q) else "ss -tlnp",
   "what's on a port: ? what is listening on port 3000",
   min_match=1)

# === NETWORKING ===
_r(["ip", "address"],
   lambda q: "hostname -I 2>/dev/null || ipconfig",
   "IP address: ? what is my ip address",
   min_match=1)
_r(["open", "port"],
   lambda q: "ss -tlnp",
   "open ports: ? show all open ports")
_r(["ping"],
   lambda q: f"ping -c 4 {_extract_filename(q) or 'google.com'}",
   "ping: ? ping google.com",
   min_match=1)
_r(["download"],
   lambda q: f"curl -O {_extract_filename(q) or 'URL'}",
   "download: ? download file from URL",
   min_match=1)

# === FILES & DIRECTORIES ===
_r(["create", "folder"],
   lambda q: f"mkdir -p {_extract_dir(q)}",
   "create folder: ? create a folder called backup")
_r(["delete", "folder"],
   lambda q: f"rm -rf {_extract_dir(q)}",
   "delete folder: ? delete the temp folder")
_r(["copy", "folder"],
   lambda q: f"cp -r {_extract_dir(q)} {_extract_dir(q)}_copy",
   "copy folder: ? copy the src folder")
_r(["list", "file"],
   lambda q: f"ls -lah {_extract_dir(q)}".replace(" .", ""),
   "list files: ? list all files with sizes")
_r(["hidden", "file"],
   lambda q: f"ls -lah {_extract_dir(q)}".replace(" .", ""),
   "hidden files: ? show hidden files")
_r(["count", "file"],
   lambda q: f"ls {_extract_dir(q)} | wc -l",
   "count files: ? how many files are in this folder")
_r(["rename"],
   lambda q: f"mv {_extract_filename(q) or 'OLD'} NEW_NAME",
   "rename: ? rename file.txt",
   min_match=1)
_r(["move", "file"],
   lambda q: f"mv {_extract_filename(q) or 'FILE'} DESTINATION/",
   "move file: ? move file.txt to backup")
_r(["empty", "file"],
   lambda q: f"> {_extract_filename(q) or 'FILE'}",
   "empty file: ? empty the log file")

# === TEXT / FILE CONTENT ===
_r(["last", "line"],
   lambda q: f"tail -n {_extract_number(q) or '10'} {_extract_filename(q) or 'FILE'}",
   "last N lines: ? show last 20 lines of server.log")
_r(["first", "line"],
   lambda q: f"head -n {_extract_number(q) or '10'} {_extract_filename(q) or 'FILE'}",
   "first N lines: ? show first 5 lines of README.md")
_r(["count", "line"],
   lambda q: f"wc -l {_extract_filename(q) or 'FILE'}",
   "count lines: ? count lines in main.py")
_r(["word", "count"],
   lambda q: f"wc -w {_extract_filename(q) or 'FILE'}",
   "word count: ? word count of README.md")
_r(["sort", "file"],
   lambda q: f"sort {_extract_filename(q) or 'FILE'}",
   "sort file: ? sort names.txt")
_r(["unique", "line"],
   lambda q: f"sort {_extract_filename(q) or 'FILE'} | uniq",
   "unique lines: ? show unique lines in file.txt")
_r(["replace", "text"],
   lambda q: f"sed -i 's/OLD/NEW/g' {_extract_filename(q) or 'FILE'}",
   "replace text: ? replace foo with bar in config.txt",
   min_match=1)

# === COMPRESSION ===
_r(["compress", "folder"],
   lambda q: f"zip -r {_extract_dir(q)}.zip {_extract_dir(q)}",
   "compress folder: ? compress the logs folder")
_r(["compress"],
   lambda q: f"zip -r {_extract_dir(q)}.zip {_extract_dir(q)}",
   "compress: ? compress the logs folder",
   min_match=1)
_r(["zip", "folder"],
   lambda q: f"zip -r {_extract_dir(q)}.zip {_extract_dir(q)}",
   "zip folder: ? zip the src folder")
_r(["zip"],
   lambda q: f"zip -r {_extract_dir(q)}.zip {_extract_dir(q)}",
   "zip: ? zip the src folder",
   min_match=1)
_r(["extract", "unzip"],
   lambda q: f"unzip {_extract_filename(q) or 'FILE.zip'}",
   "extract/unzip: ? extract archive.zip",
   min_match=1)
_r(["tar", "compress"],
   lambda q: f"tar -czf {_extract_dir(q)}.tar.gz {_extract_dir(q)}",
   "tar folder: ? tar the src folder")
_r(["extract", "tar"],
   lambda q: f"tar -xzf {_extract_filename(q) or 'FILE.tar.gz'}",
   "extract tar: ? extract backup.tar.gz")

# === GIT ===
_r(["git", "status"],
   lambda q: "git status",
   "git status: ? show git status")
_r(["git", "log"],
   lambda q: f"git log --oneline -{_extract_number(q) or '10'}",
   "git log: ? show last 10 git commits")
_r(["git", "branch"],
   lambda q: "git branch -a",
   "git branches: ? list all git branches")
_r(["git", "commit"],
   lambda q: "git add . && git commit -m 'Update'",
   "git commit: ? commit all changes")
_r(["git", "push"],
   lambda q: "git push origin HEAD",
   "git push: ? push my changes")
_r(["git", "pull"],
   lambda q: "git pull",
   "git pull: ? pull latest changes")
_r(["git", "diff"],
   lambda q: "git diff",
   "git diff: ? show git differences")
_r(["git", "stash"],
   lambda q: "git stash",
   "git stash: ? stash my changes")
_r(["git", "clone"],
   lambda q: f"git clone {_extract_filename(q) or 'REPO_URL'}",
   "git clone: ? clone the repository")

# === PYTHON ===
_r(["python", "install"],
   lambda q: f"pip install {_extract_filename(q) or 'PACKAGE'}",
   "pip install: ? install the requests package",
   min_match=1)
_r(["pip", "install"],
   lambda q: f"pip install {_extract_filename(q) or 'PACKAGE'}",
   "pip install: ? pip install flask")
_r(["python", "run"],
   lambda q: f"python {_extract_filename(q) or 'script.py'}",
   "run python: ? run main.py")
_r(["python", "version"],
   lambda q: "python --version",
   "python version: ? what python version")
_r(["virtual", "env"],
   lambda q: "python -m venv venv",
   "create venv: ? create a virtual environment",
   min_match=1)
_r(["requirements", "install"],
   lambda q: "pip install -r requirements.txt",
   "install requirements: ? install all requirements")

# === SYSTEM INFO ===
_r(["system", "info"],
   lambda q: "uname -a",
   "system info: ? show system info",
   min_match=1)
_r(["uptime"],
   lambda q: "uptime",
   "uptime: ? system uptime",
   min_match=1)
_r(["who", "logged"],
   lambda q: "who",
   "who: ? who is logged in")
_r(["date"],
   lambda q: "date",
   "date/time: ? what is the date",
   min_match=1)
_r(["time"],
   lambda q: "date",
   "time: ? what time is it",
   min_match=1)
_r(["environment", "variable"],
   lambda q: "env | sort",
   "env vars: ? show all environment variables")
_r(["hostname"],
   lambda q: "hostname",
   "hostname: ? what is my hostname",
   min_match=1)

# === PERMISSIONS ===
_r(["permission"],
   lambda q: f"chmod 644 {_extract_filename(q) or 'FILE'}",
   "permissions: ? set permissions on file",
   min_match=1)
_r(["executable"],
   lambda q: f"chmod +x {_extract_filename(q) or 'FILE'}",
   "make executable: ? make script.sh executable",
   min_match=1)
_r(["owner", "file"],
   lambda q: f"ls -la {_extract_filename(q) or '.'}",
   "ownership: ? who owns this file")

# === MISC ===
_r(["clear"],
   lambda q: "clear",
   "clear screen: ? clear the screen",
   min_match=1)
_r(["current", "folder"],
   lambda q: "pwd",
   "current dir: ? what directory am i in",
   min_match=1)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def match_query(query: str) -> str | None:
    """
    Match a natural language query against all rules.
    Returns the best matching shell command, or None if no match.

    The query goes through synonym expansion before matching, so
    "show me the directory size" becomes "list me the folder size"
    and matches the size/folder rule.
    """
    # Expand synonyms BEFORE matching
    expanded = _expand_synonyms(query)
    expanded_lower = expanded.lower()

    best_rule = None
    best_score = 0
    best_total = 0

    for rule in RULES:
        # Count how many match_words appear in the EXPANDED query
        score = sum(1 for w in rule.match_words if w in expanded_lower)
        required = rule.required

        if score >= required and score > 0:
            # Prefer rules that match MORE keywords (higher specificity)
            # If tied, prefer rules that require more keywords (more specific rule)
            if score > best_score or (score == best_score and len(rule.match_words) > best_total):
                best_score = score
                best_total = len(rule.match_words)
                best_rule = rule

    if best_rule is None:
        return None

    try:
        return best_rule.resolver(query)
    except Exception:
        return None


def print_smart_help(stdout_write):
    """Print a categorized list of all available smart patterns."""
    stdout_write("\nSmart Engine -- Available Patterns\n")
    stdout_write("=" * 55 + "\n")
    stdout_write("Just type plain English. No `?` prefix needed!\n")
    stdout_write("You can also prefix with `?` if you prefer.\n\n")

    categories = {
        "File Search":     [r for r in RULES if any(w in ("find","search","large","last","grep") for w in r.match_words)],
        "Disk & Storage":  [r for r in RULES if any(w in ("disk","size","largest","free","space") for w in r.match_words) and "process" not in r.match_words and "file" not in r.match_words],
        "Processes":       [r for r in RULES if any(w in ("process","kill","running") for w in r.match_words)],
        "Networking":      [r for r in RULES if any(w in ("ip","port","ping","download") for w in r.match_words)],
        "Files & Dirs":    [r for r in RULES if any(w in ("create","delete","copy","list","hidden","count","rename","move","empty") for w in r.match_words)],
        "Text Content":    [r for r in RULES if any(w in ("first","count","word","sort","unique","replace") for w in r.match_words) and "file" not in r.match_words],
        "Compression":     [r for r in RULES if any(w in ("compress","zip","extract","tar") for w in r.match_words)],
        "Git":             [r for r in RULES if "git" in r.match_words],
        "Python":          [r for r in RULES if "python" in r.match_words or "pip" in r.match_words or "virtual" in r.match_words or "requirements" in r.match_words],
        "System Info":     [r for r in RULES if any(w in ("system","uptime","who","date","time","environment","hostname") for w in r.match_words)],
        "Permissions":     [r for r in RULES if any(w in ("permission","executable","owner") for w in r.match_words)],
    }

    for category, rules in categories.items():
        if not rules:
            continue
        stdout_write(f"\n  {'-'*50}\n")
        stdout_write(f"  {category}\n")
        stdout_write(f"  {'-'*50}\n")
        seen = set()
        for rule in rules:
            if rule.description not in seen:
                stdout_write(f"    {rule.description}\n")
                seen.add(rule.description)

    stdout_write("\n")


def handle_smart_query(query: str, execute_fn, stdout_write, stderr_write) -> bool:
    """
    Process a smart query using a hybrid approach:
      1. Try rule-based engine first (instant, offline)
      2. If no rule matches, try Gemini AI (if configured)
      3. If neither works, return False

    Returns True if a match was found and handled.
    Returns False if nothing matched (caller should handle).
    """
    query = query.strip()

    if query in ("--help", "-h", "help", ""):
        print_smart_help(stdout_write)
        return True

    # --- Step 1: Try rule-based engine (instant, offline) ---
    command = match_query(query)
    source = "rules"

    # --- Step 2: If rules didn't match, try Gemini AI ---
    if command is None:
        try:
            from app.gemini_ai import ask_gemini, is_configured
            if is_configured():
                stdout_write("  Thinking...\n")
                command = ask_gemini(query)
                source = "Gemini AI"
        except ImportError:
            pass

    # --- Nothing matched ---
    if command is None:
        return False

    # Show the suggestion with source label
    stdout_write(f"\n  [{source}] suggestion:\n   {command}\n\n")

    try:
        answer = input("   Run this? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        stdout_write("\n")
        return True

    if answer in ("y", "yes"):
        stdout_write("\n")
        execute_fn(command)
    else:
        stdout_write("   Skipped.\n\n")

    return True
