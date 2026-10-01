#!/usr/bin/env python3
"""Palim SessionStart hook — injects the last thread so a new chat starts informed.

Deterministic counterpart to the `palim_resume` MCP tool: the context is present
before the model's first token, with no tool call and no model decision involved.
Also states the session id this chat should checkpoint into, so the model's
handoff and the Stop hook's live tail end up on the same row.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palim_hook_lib import credentials, fetch_resume, read_hook_input  # noqa: E402

WITHIN_HOURS = os.environ.get("PALIM_RESUME_WITHIN_HOURS", "48")


def main():
    if not credentials():
        return

    payload = read_hook_input()
    context = fetch_resume(WITHIN_HOURS)
    if not context:
        return

    session_id = payload.get("session_id")
    if session_id:
        context += (
            f"\n\nCheckpoint-Ziel für diesen Chat: `claude-code-{session_id}`. "
            "Nutze genau diese `session_id` bei `palim_save_context`, damit deine Übergabe "
            "und der automatisch fortgeschriebene Stand auf derselben Zeile landen."
        )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
