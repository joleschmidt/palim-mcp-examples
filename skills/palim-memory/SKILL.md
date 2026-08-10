---
name: palim-memory
description: Carry useful context across AI tools with Palim. Use when the user wants to resume earlier work, search saved sessions or durable memories, save a checkpoint or decision, inspect Palim history, or preserve context for another MCP client.
---

# Palim Memory

Use Palim as the durable context layer for work the user explicitly wants to retrieve across AI clients.

## Resume and retrieve

1. Call `palim_resume` when the user asks to continue recent work without naming a specific session.
2. Use `palim_search` for concrete keywords across saved sessions.
3. Use `palim_search_by_date_range` for date or metadata filters; do not expect it to search encrypted message bodies.
4. Use `palim_search_memories` for durable facts, preferences, and decisions stored as memories.
5. Use `palim_get_context` when the user needs a compact synthesis across several relevant sessions.

Palim currently uses PostgreSQL full-text and exact-text matching, not semantic embeddings. If an exact title phrase misses, retry with distinctive keywords, tags, or a date range.

## Save useful context

1. Prefer `palim_save_context` for a lightweight, self-contained checkpoint after a substantial result, decision, or change of direction.
2. Keep one stable `session_id` for checkpoints in the same conversation so later saves update the same thread.
3. When continuing a thread returned by `palim_resume`, pass its session ID as `continues_from` while keeping the current conversation's own stable `session_id`.
4. Use `palim_add_memory` for a durable fact or preference that should be independently searchable.
5. Use `palim_save_session` only when the user requests or genuinely needs the full transcript.

Never save secrets, trivial exchanges, or content the user asked not to persist. Do not claim a save succeeded unless the tool confirms it.

## Safety and scope

- Keep reads and writes within the authenticated user's Palim account.
- Treat deletion as destructive and require clear scope before calling a delete tool.
- Do not publish Palim content to external services unless the user separately requests and authorizes that action through an appropriate tool.
- If a named Palim tool is unavailable, use the closest available Palim tool and state the limitation instead of inventing a result.
