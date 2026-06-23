# Knowledge Graph MCP — Design

Date: 2026-06-23
Status: Approved (Phase 1 buildable; Phase 2 outlined)

## Problem

When chatting with an AI to learn something, the AI cold-starts every time. It re-explains concepts I already know, and it doesn't use concepts I already know to explain new ones. I have a growing wiki of my own learnings (atomic, first-person concept pages cross-linked with `[[wikilinks]]`). I want to expose that knowledge to other AIs through MCP so they can see what I already know and teach on top of it.

The wiki is connection-heavy by design, so the retrieval system should be a real graph, not flat document search.

## Goals

- Let an AI retrieve what I already know, and how those things connect, during a chat.
- Specifically fix two failure modes: re-teaching known concepts, and not anchoring new concepts in known ones.
- Use a graph database (Neo4j) so connections are first-class.
- Work with Claude clients first (local MCP), and ChatGPT / web AIs later (remote MCP).

## Non-goals

- No mastery / depth modelling. A concept is either in the graph (I know it) or not. No inference of how well I know something.
- No classic chunk-and-embed vector RAG as the primary mechanism. Full-text + graph traversal is the core; a vector index is an optional later add-on.
- Phase 2 (remote/ChatGPT deployment) is outlined here but not built in the first implementation plan.

## Decisions (from brainstorming)

- Interaction model: both a session primer (push) and on-demand lookups (pull).
- Knowledge model: binary presence, no mastery levels.
- Retrieval: Neo4j graph database, using its full-text index for topic entry-matching and graph traversal for connections. Native vector index left as a future slot.
- Hosting: Neo4j Aura free tier (cloud, managed, already reachable for the eventual remote phase).
- Clients: Claude clients (Claude Code / Desktop / Cursor) via local stdio MCP in Phase 1; ChatGPT / web AIs via remote HTTP MCP in Phase 2.

## Architecture

One knowledge engine, fed by a sync script, queried through swappable MCP transports.

```
wiki/*.md ──► sync_graph.py ──► Neo4j Aura ◄── knowledge engine ◄── MCP transport ◄── AI client
            (parse, MERGE,        (graph +        (Cypher queries)    stdio (Phase 1)
             rebuild edges)        full-text idx)                     HTTP + auth (Phase 2)
```

The engine (Cypher queries + result shaping) is transport-agnostic. Phase 1 wraps it in a stdio MCP server; Phase 2 wraps the same engine in an authenticated HTTP MCP server.

## Graph model

Every wiki page becomes a node; `related` wikilinks become edges.

Nodes:
- `:Page` shared label, with a type sub-label: `:Concept`, `:Project` (NUS modules), `:Person`, `:SourceSummary`.
- Properties: `slug` (unique key, filename without `.md`), `title`, `type`, `summary` (the page's `## Summary`), `body` (full markdown), `created`, `lastUpdated`.
- `:Source` nodes for `raw/` files, property `path`, for provenance.

Relationships:
- `(:Page)-[:RELATED_TO]->(:Page)` from each `[[wikilink]]` in `related` frontmatter and inline body links. The core connection graph. Queried as undirected.
- `(:Page)-[:DERIVED_FROM]->(:Source)` from `sources:` frontmatter.
- `(:Project)-[:COVERS]->(:Concept)` for module-hub pages linking to concept pages, so "what did I learn in CS2040S" is one hop.

Indexes:
- Full-text index over `title`, `summary`, `body` for matching an arbitrary new topic to entry concepts.
- A native vector index is a future slot (requires an embedding step); not built in Phase 1.

## Sync pipeline — `sync_graph.py`

A standalone script in the same family as `fetch_modules.py` and `probe_providers.py`.

- Reads Aura connection details from a gitignored `.env` (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`).
- Parses every `wiki/**/*.md`: frontmatter (title, type, sources, related, created, last-updated) plus body, deriving `slug` from the path and `summary` from the `## Summary` section.
- Upserts with idempotent `MERGE` on `slug`, so re-running updates rather than duplicates.
- Rebuilds `RELATED_TO` / `DERIVED_FROM` / `COVERS` edges from the current wikilinks each run.
- Prunes nodes whose pages no longer exist.
- Run manually after `/ingest`; optionally chained so ingest triggers a sync.

## MCP tools (the engine surface)

- `knowledge_primer()` — push. Compact map of everything I know: topics grouped by area, one-line summaries, and their connections. Loaded at chat start.
- `search_knowledge(topic)` — full-text match to find my entry concepts for an arbitrary topic.
- `get_concept(slug)` — full page body plus immediate neighbours.
- `related_to(slug, hops=1..2)` — graph neighbourhood around a concept.
- `bridge(new_topic)` — finds the concepts I already know that are closest / most connected to a new topic, so a teaching AI can anchor explanations in them. This is the direct fix for the cold-start problem.

## Phasing

- Phase 1 (built first): `.env` + Aura setup, `sync_graph.py`, the knowledge engine, and a local stdio MCP server exposing the five tools. Validated in Claude Code / Desktop against the real wiki.
- Phase 2 (outlined): wrap the identical engine in a remote HTTP MCP server with authentication, deploy it to a reachable host, and point ChatGPT's connector at it. Aura is already reachable, so no data migration.

## Testing

- Pure functions (markdown/frontmatter parsing, slug derivation, wikilink/edge extraction) unit-tested on fixture pages.
- Idempotency test: running `sync_graph.py` twice yields the same node and edge counts.
- Tool queries checked against Aura with a small seeded set (primer returns known topics; `bridge` returns sensible anchors; `get_concept` returns the right body and neighbours).
- Manual end-to-end check via an MCP client against the live wiki.

## Secrets & safety

- Aura credentials live only in `.env`, which is gitignored. Neither the sync script nor the server hardcode them.
- Phase 2 adds auth on the public endpoint; until then the server is local stdio only and not exposed.
