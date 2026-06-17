"""
gemini_ai.py -- Google Gemini AI integration for SmartShell.

Used as a FALLBACK when the rule-based engine can't match a query.
Requires a Gemini API key stored securely via:
  - Environment variable: GEMINI_API_KEY
  - Or .env file in project root (auto-loaded, gitignored)

Free tier: 15 requests/minute, no credit card needed.
Get a key at: https://aistudio.google.com

Security:
  - API key is NEVER stored in source code
  - .env file is gitignored
  - Key is read from environment at runtime only
"""

import os
import sys
import json
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# System prompt tells Gemini to act as a command translator
SYSTEM_PROMPT = """You are a shell command assistant embedded in a terminal.
The user is on {os_type} in directory: {cwd}

Your ONLY job: convert the user's plain English request into a SINGLE shell command.

Rules:
- Reply with ONLY the shell command, nothing else
- No explanations, no markdown, no code blocks
- No backticks, no quotes around the command
- If the request is ambiguous, give the most common/safe interpretation
- Use commands appropriate for {os_type}
- If you truly cannot convert to a command, reply with exactly: CANNOT_CONVERT

Examples:
  User: show me all python files
  You: find . -name "*.py" -type f

  User: what is the size of this folder
  You: du -sh .

  User: tell me the weather
  You: CANNOT_CONVERT
"""


# ---------------------------------------------------------------------------
# API key management
# ---------------------------------------------------------------------------

def _load_env_file():
    """Try to load .env file from project root if it exists."""
    # Walk up from this file to find .env
    current = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(current)

    for directory in [parent, current, os.getcwd()]:
        env_path = os.path.join(directory, ".env")
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, _, value = line.partition("=")
                            key = key.strip()
                            value = value.strip().strip("'\"")
                            if key and value:
                                os.environ.setdefault(key, value)
            except OSError:
                pass
            break


def get_api_key() -> str | None:
    """
    Get the Gemini API key from environment.
    Checks GEMINI_API_KEY env var, loading .env file first if needed.
    Returns None if no key is configured.
    """
    # Try loading .env file first
    _load_env_file()

    key = os.environ.get("GEMINI_API_KEY", "").strip()
    return key if key else None


def is_configured() -> bool:
    """Check if Gemini API is configured (key available)."""
    return get_api_key() is not None


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def ask_gemini(user_query: str) -> str | None:
    """
    Send a natural language query to Gemini and get back a shell command.

    Returns:
        The shell command string, or None if:
        - API key not configured
        - Network error
        - Gemini can't convert the request
    """
    api_key = get_api_key()
    if not api_key:
        return None

    # Detect OS type
    os_type = "Windows" if os.name == "nt" else "Linux/macOS"

    # Build the system prompt with context
    system = SYSTEM_PROMPT.format(
        os_type=os_type,
        cwd=os.getcwd(),
    )

    # Build Gemini API request
    url = f"{GEMINI_API_URL}?key={api_key}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_query}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system}]
        },
        "generationConfig": {
            "temperature": 0.1,    # Low temp = deterministic commands
            "maxOutputTokens": 200,
            "topP": 0.8,
        }
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Read error body for debugging
        try:
            err_body = e.read().decode("utf-8")
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)

        if e.code == 400:
            return None  # Bad request — silently fail
        if e.code == 403 or e.code == 401:
            sys.stderr.write(f"  Gemini API key error: {msg}\n")
            return None
        if e.code == 429:
            sys.stderr.write("  Gemini rate limit reached. Try again in a moment.\n")
            return None
        return None
    except urllib.error.URLError:
        # No internet
        return None
    except Exception:
        return None

    # Extract the response text
    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        return None

    # Clean up the response
    # Remove any markdown code fences Gemini might add despite instructions
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Check if Gemini couldn't convert
    if text == "CANNOT_CONVERT" or not text:
        return None

    return text


# ---------------------------------------------------------------------------
# Setup helper
# ---------------------------------------------------------------------------

def setup_api_key(stdout_write, stderr_write) -> bool:
    """
    Interactive setup: prompt user for API key and save to .env file.
    Called by the `setup-ai` builtin command.

    Returns True if key was saved successfully.
    """
    stdout_write("\n")
    stdout_write("  Gemini AI Setup\n")
    stdout_write("  " + "-" * 50 + "\n")
    stdout_write("  Get a free API key at: https://aistudio.google.com\n")
    stdout_write("  (15 requests/minute, no credit card)\n\n")

    try:
        key = input("  Paste your Gemini API key: ").strip()
    except (EOFError, KeyboardInterrupt):
        stdout_write("\n  Setup cancelled.\n")
        return False

    if not key:
        stderr_write("  No key provided. Setup cancelled.\n")
        return False

    # Save to .env file in project root
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)
    env_path = os.path.join(project_root, ".env")

    try:
        # Read existing .env content
        existing = ""
        if os.path.isfile(env_path):
            with open(env_path, "r") as f:
                existing = f.read()

        # Replace or append the key
        lines = existing.split("\n") if existing else []
        found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith("GEMINI_API_KEY"):
                new_lines.append(f"GEMINI_API_KEY={key}")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"GEMINI_API_KEY={key}")

        with open(env_path, "w") as f:
            f.write("\n".join(new_lines) + "\n")

        # Also set in current environment
        os.environ["GEMINI_API_KEY"] = key

        stdout_write(f"\n  Key saved to {env_path}\n")
        stdout_write("  Gemini AI is now active!\n")
        stdout_write("  This file is gitignored -- your key stays safe.\n\n")

        # Ensure .gitignore includes .env
        _ensure_gitignore(project_root)

        return True

    except OSError as e:
        stderr_write(f"  Error saving key: {e}\n")
        return False


def _ensure_gitignore(project_root: str):
    """Make sure .env is in .gitignore."""
    gitignore_path = os.path.join(project_root, ".gitignore")
    try:
        content = ""
        if os.path.isfile(gitignore_path):
            with open(gitignore_path, "r") as f:
                content = f.read()

        if ".env" not in content:
            with open(gitignore_path, "a") as f:
                f.write("\n# SmartShell API keys\n.env\n")
    except OSError:
        pass
