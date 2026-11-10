---
name: status
description: Check whether the Palim session hooks are working in Claude Code. Use when the user asks why the last thread was not loaded at session start, whether checkpoints are being saved, or how to set the hooks' API key.
---

# Palim hooks status

The hooks load the last thread when a session starts and keep a checkpoint current while the
user works. They fail silently on purpose, so this is the only way to see what they did.

Run this and show its output unchanged:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/palim-status.py"
```

The last line, `Result:`, says what to do. The usual case is a missing API key: the hooks cannot
use the connector's sign-in and need their own key. The user creates one at
https://api.usepalim.com/setup and enters it under `/plugin` > palim-hooks > Configure. Do not
ask them to paste the key into the chat.
