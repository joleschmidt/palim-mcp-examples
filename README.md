# Palim MCP examples

Copy-paste configs to connect [Palim](https://usepalim.com) — a **hosted MCP memory server** — to Claude, Cursor, ChatGPT, and other MCP clients.

Palim stores sessions, decisions, and memories you **explicitly save**, then makes them searchable from every connected AI client.

> Not a local SQLite sidecar. Hosted MCP endpoint. Search today: PostgreSQL full-text + text match (not vector/semantic embeddings).

## Quick links

| | |
|---|---|
| MCP endpoint | `https://api.usepalim.com/mcp` |
| Setup / API key | https://api.usepalim.com/setup |
| Docs | https://usepalim.com/en/docs/ |
| Machine-readable | https://usepalim.com/llms.txt |
| Site | https://usepalim.com |


## Add to Cursor

[![Add Palim MCP to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](cursor://anysphere.cursor-deeplink/mcp/install?name=palim&config=eyJ1cmwiOiJodHRwczovL2FwaS51c2VwYWxpbS5jb20vbWNwIn0=)

One-click install (OAuth on first use). Or copy [`configs/cursor.mcp.json`](configs/cursor.mcp.json).

This repo is also an [Agent Plugins](https://open-plugins.com) package (`plugin.json` + `mcp.json`) for [cursor.directory](https://cursor.directory).

### Intent pages

- [Share context ChatGPT ↔ Claude](https://usepalim.com/en/use-cases/share-context-chatgpt-claude/)
- [Hosted MCP memory server](https://usepalim.com/en/use-cases/hosted-mcp-memory-server/)
- [Palim vs Mem0](https://usepalim.com/en/compare/palim-vs-mem0/)

---

## Claude Code (OAuth)

```bash
claude mcp add --transport http palim https://api.usepalim.com/mcp
```

First use opens OAuth. API key alternative:

```bash
claude mcp add --transport http palim https://api.usepalim.com/mcp \
  --header "x-api-key: YOUR_API_KEY"
```

Also see [`configs/claude-code.sh`](configs/claude-code.sh).

---

## Cursor (OAuth)

Settings → Tools & MCP → Add server → URL `https://api.usepalim.com/mcp`, or put this in `~/.cursor/mcp.json` / `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "palim": {
      "url": "https://api.usepalim.com/mcp"
    }
  }
}
```

File: [`configs/cursor.mcp.json`](configs/cursor.mcp.json). Restart Cursor after edits. For API key auth, see [`configs/cursor.api-key.mcp.json`](configs/cursor.api-key.mcp.json).

---

## Claude Desktop / Claude.ai

Add a **custom connector** / remote MCP:

- URL: `https://api.usepalim.com/mcp`
- Auth: OAuth (no API key required for that flow)

---

## ChatGPT

1. Settings → Apps → Advanced → enable **Developer Mode**
2. Create app → URL `https://api.usepalim.com/mcp` → Auth: **OAuth**
3. Advanced settings → **disable OIDC** (otherwise: “Authorization Request Expired” / token exchange failures)
4. In **each** chat, mention `@Palim` — without that, tools are not available

---

## Perplexity

API key from https://api.usepalim.com/setup. Settings → Connectors → Advanced → paste [`configs/perplexity.mcp.json`](configs/perplexity.mcp.json) and replace `YOUR_API_KEY`.

---

## Smoke test

In any connected client:

```text
Palim Help
```

You should get the tool overview. Then save a real session and retrieve it from a second client.

---

## What not to claim

- Semantic / embedding search (not shipped)
- Automatic sync without an explicit save (except documented extension/hooks)
- ChatGPT Memory portability


## Tools

Palim exposes hosted memory tools over MCP (45+), including:

| Tool | Purpose |
|------|---------|
| `palim_resume` | Continue the latest handoff |
| `palim_save_context` | Lightweight checkpoint (default save) |
| `palim_save_session` | Full transcript save/append |
| `palim_search` / `palim_search_by_date_range` | Find past work |
| `palim_add_memory` | Durable facts/preferences |
| `palim_help` | Tool overview |

Full list: connect and call `palim_help`, or see https://usepalim.com/en/docs/

## Usage

1. Connect with OAuth or `x-api-key`
2. In a new chat, call `palim_resume` (or ask "Palim Help")
3. After real work, checkpoint with `palim_save_context`
4. Retrieve from another client with `palim_search`

## License

MIT — configs only; Palim the service remains proprietary.
