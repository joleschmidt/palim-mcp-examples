# Palim session hooks

Session hooks for Claude Code. They load the Palim thread you worked on last when a session
starts, keep a checkpoint of the current state while you work, and save one more before Claude
Code compacts its context. No tool call and no model decision is involved: a hook fires at
turn 400 the same way it fires at turn 1.

Use them together with the [Palim plugin](https://github.com/joleschmidt/palim-claude-plugin),
which brings the connector and the skills.

## Set it up

```bash
claude plugin marketplace add joleschmidt/palim-mcp-examples
claude plugin install palim-hooks@palim
```

The hooks run outside the model and cannot use the connector's sign-in. Create an API key at
[api.usepalim.com/setup](https://api.usepalim.com/setup) and enter it when Claude Code asks for
the plugin's options, or later under `/plugin` > palim-hooks > Configure. Claude Code keeps it
in your system's secure storage. Without a key the hooks do nothing.

If you registered the Palim hooks by hand in `~/.claude/settings.json`, remove those three
entries so each hook runs once. `/palim-hooks:status` shows whether the hooks work.

## What the hooks run and what they send

They talk to one host, `api.usepalim.com`, and to nothing else.

**Hooks.** Three Python scripts in `hooks/`, started by Claude Code. They use the API key from
the plugin's options, or `PALIM_API_KEY` if you set it. They read no other credential.

| Hook | When | What it sends |
|---|---|---|
| `palim-resume.py` | Session start, and after `/clear` | A request for your last thread from the past 48 hours. The answer is added to Claude's context. |
| `palim-checkpoint-turn.py` | After a turn, once 3 minutes or 5 turns have passed since the last checkpoint | Your last prompt, Claude's last answer, the session id, the turn count and the name of the project folder |
| `palim-precompact.py` | Before Claude Code compacts the context | The first line of your last 3 prompts, Claude's last answer, the session id, the turn count and the name of the project folder |

To find your last prompt, the checkpoint hooks read the session transcript that Claude Code
keeps on your machine. They send no file contents, no tool output and no other part of the
transcript.

**Status.** `hooks/palim-status.py` runs only when you ask for the status. It reads the notes
described below and requests `https://api.usepalim.com/health` without a credential.

**On your machine.** The hooks keep small files in `~/.palim/hook-state`: when a session was
last written, and the outcome of the last hook run. These files never contain your key or
your prompts. Files of old sessions are deleted after 14 days.

**On the server.** Stored conversation content is encrypted with AES-256-GCM. Details are in
the [security notes](https://www.usepalim.com/en/docs/security/) and the
[privacy policy](https://www.usepalim.com/en/privacy/).

Every hook exits with status 0 whatever happens: no key, no network, a timeout, broken
input. A hook cannot block a session, and it gives up on a request after 5 seconds.

## Requirements

Claude Code with plugin options support, and `python3` (3.8 or later) on your `PATH`. The
scripts use the standard library only.

## Settings

Environment variables for the hooks. All are optional.

| Variable | Default | Effect |
|---|---|---|
| `PALIM_API_KEY` | not set | Used in place of the key from the plugin's options |
| `PALIM_API_URL` | `https://api.usepalim.com` | Another Palim server, for testing |
| `PALIM_CHECKPOINT_MIN_SECONDS` | `180` | Minimum time between two turn checkpoints |
| `PALIM_CHECKPOINT_MIN_TURNS` | `5` | Turns after which a checkpoint is written anyway |
| `PALIM_RESUME_WITHIN_HOURS` | `48` | Older threads are not loaded at session start |
| `PALIM_PRECOMPACT_PROMPTS` | `3` | Prompts included in the checkpoint before compaction |
| `PALIM_STATE_DIR` | `~/.palim/hook-state` | Where the hooks keep their local files |
| `PALIM_HOOK_TIMEOUT` | `5` | Seconds after which a hook gives up on a request |

## What it does not do

The hooks record what was said, not what it meant. The handoff that a later session can
really work from is the one Claude writes with `palim_save_context`. The hooks make sure
there is a current state even when that did not happen.

## Source

The scripts are generated from `hooks/` in the main Palim repository. MIT licensed, see
[LICENSE](../../LICENSE).
