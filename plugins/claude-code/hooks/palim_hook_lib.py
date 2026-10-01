"""Shared helpers for the Palim Claude Code hooks.

Design rule for every hook in this directory: a hook must never block, slow down
or break a session. Every failure path exits quietly with status 0.
"""
import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request

API_BASE = os.environ.get("PALIM_API_URL", "https://api.usepalim.com").rstrip("/")
TIMEOUT = float(os.environ.get("PALIM_HOOK_TIMEOUT", "5"))
STATE_DIR = pathlib.Path(
    os.environ.get("PALIM_STATE_DIR", os.path.expanduser("~/.palim/hook-state"))
)

# Where an already-connected client keeps its Palim credential. Reading it here is
# what makes the hooks work without any setup: whoever has Palim connected already
# holds a valid credential, and it is the same one, going to the same server.
CLIENT_CONFIGS = [
    os.path.expanduser("~/.claude.json"),
    os.path.expanduser("~/.claude/settings.json"),
]

_credentials_cache = "unset"


def _looks_like_key(value):
    """Guard against a placeholder in the environment shadowing a working key.

    Copying a documented example verbatim ("palim_…") is an easy mistake, and the
    env var takes precedence — so an unusable value there would silently disable
    an otherwise working setup. Anything that is not plausibly a real credential
    is ignored in favour of the client config.
    """
    if not value or not value.isascii():
        return False
    return len(value) >= 20 and re.match(r"^(palim|ctxu)_[A-Za-z0-9_-]+$", value) is not None


def _from_client_config(path):
    """Find the Palim MCP entry in a client config and extract its credential."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return None

    found = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "palim" and isinstance(value, dict):
                    found.append(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)

    for entry in found:
        headers = entry.get("headers") or {}
        for name, value in headers.items():
            if not isinstance(value, str) or not value.strip():
                continue
            lowered = name.lower()
            if lowered in ("x-api-key", "api-key"):
                return {"headers": {name: value}}
            if lowered == "authorization":
                return {"headers": {"Authorization": value}}
        # Connection-URL setups carry a token in the query string instead.
        url = entry.get("url")
        if isinstance(url, str) and "token=" in url:
            match = re.search(r"[?&](ctx_token|token)=([^&\s]+)", url)
            if match:
                return {"query": {match.group(1): match.group(2)}}
    return None


def credentials():
    """Auth material for Palim requests, or None. Result is cached per process.

    PALIM_API_KEY wins when set, so an explicit key always overrides whatever a
    client config happens to contain.
    """
    global _credentials_cache
    if _credentials_cache != "unset":
        return _credentials_cache

    # CLAUDE_PLUGIN_OPTION_API_KEY is how Claude Code hands the plugin's userConfig key to hooks.
    env_key = (os.environ.get("PALIM_API_KEY") or os.environ.get("CLAUDE_PLUGIN_OPTION_API_KEY") or "").strip()
    if _looks_like_key(env_key):
        _credentials_cache = {"headers": {"Authorization": f"Bearer {env_key}"}}
        return _credentials_cache

    for path in CLIENT_CONFIGS:
        found = _from_client_config(path)
        if found:
            _credentials_cache = found
            return _credentials_cache

    _credentials_cache = None
    return None


def build_url(path, params=None):
    """Compose a URL, folding in query-based credentials when that is what we have."""
    query = dict(params or {})
    creds = credentials() or {}
    query.update(creds.get("query") or {})
    suffix = f"?{urllib.parse.urlencode(query)}" if query else ""
    return f"{API_BASE}{path}{suffix}"


def auth_headers():
    return dict((credentials() or {}).get("headers") or {})


def read_hook_input():
    """Parse the hook payload from stdin. Returns {} when anything is off."""
    try:
        raw = os.read(0, 1 << 20).decode("utf-8", "replace")
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def _text_of(content):
    """Claude Code message content is either a string or a list of blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        return "\n".join(chunks)
    return ""


def scan_transcript(path, want_user_messages=1):
    """Return (recent user messages, total turn count) from a JSONL transcript.

    The transcript is written asynchronously and may lag the current turn, so
    callers should treat the user text as best-effort and rely on the hook
    payload's own fields where available.
    """
    users, turns = [], 0
    if not path or not os.path.isfile(path):
        return [], 0
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except Exception:
                    continue
                if event.get("isSidechain"):
                    continue
                message = event.get("message") or {}
                role = message.get("role")
                if role not in ("user", "assistant"):
                    continue
                turns += 1
                if role == "user":
                    text = _text_of(message.get("content")).strip()
                    # Tool results arrive as user turns; they are not prompts.
                    if text and not text.startswith("<"):
                        users.append(text)
    except Exception:
        return [], turns
    return users[-want_user_messages:], turns


def project_of(cwd):
    if not cwd:
        return None
    return os.path.basename(str(cwd).rstrip("/")) or None


def _state_file(session_id):
    safe = "".join(c for c in str(session_id) if c.isalnum() or c in "-_")[:120]
    return STATE_DIR / f"{safe}.json"


def should_write(session_id, turns, min_seconds, min_turns):
    """Debounce: without this a single user costs ~1150 writes/day."""
    try:
        state = json.loads(_state_file(session_id).read_text())
    except Exception:
        return True
    if time.time() - float(state.get("at", 0)) >= min_seconds:
        return True
    return turns - int(state.get("turns", 0)) >= min_turns


def remember_write(session_id, turns):
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        _state_file(session_id).write_text(json.dumps({"at": time.time(), "turns": turns}))
    except Exception:
        pass


def post_checkpoint(body):
    """Fire the turn checkpoint. Returns True on success, never raises."""
    if not credentials():
        return False
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers())
    request = urllib.request.Request(
        build_url("/api/checkpoint-turn"),
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def fetch_resume(within_hours):
    """Return the formatted handoff for the last thread, or None."""
    if not credentials():
        return None
    request = urllib.request.Request(
        build_url("/api/resume", {"format": "text", "within_hours": within_hours}),
        headers=auth_headers(),
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read().decode("utf-8", "replace").strip() or None
    except Exception:
        return None
