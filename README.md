# Second Brain

A structured knowledge vault with two clear ownership zones:

- **`raw/`** — your source documents, imported as-is. Never modified.
- **`wiki/`** — Claude's domain. Synthesized, cross-linked knowledge pages built from raw sources.
- **`journal/`** — Daily notes and reflections (Part 2).
- **`content/`** — Content creation pipeline (Part 2).

---

## Knowledge graph (gbrain)

The wiki is served to AI tools as a queryable knowledge graph via [gbrain](https://github.com/garrytan/gbrain), so an AI can see what you already know and build on it instead of cold-starting. Everything runs **locally and key-free** (gbrain on PGLite + Ollama for embeddings).

### One-time setup

```bash
# 1. Install Bun (gbrain's runtime) and gbrain
curl -fsSL https://bun.sh/install | bash
export PATH="$HOME/.bun/bin:$PATH"
bun install -g github:garrytan/gbrain
gbrain apply-migrations --yes

# 2. Install Ollama and a local embedding model, run it as a service
brew install ollama
brew services start ollama
ollama pull nomic-embed-text

# 3. Create the local brain (PGLite, no cloud) wired to the local embedder
gbrain init --pglite --embedding-model ollama:nomic-embed-text
gbrain apply-migrations --yes

# 4. Load the wiki into the graph
./sync_gbrain.sh
```

The brain lives in `~/.gbrain` (outside this repo). On a new machine, repeat steps 1–4.

### Everyday use

After you add notes and run `/ingest` (so the wiki gains pages), refresh the graph:

```bash
./sync_gbrain.sh        # import knowledge folders, wire [[wikilinks]], embed new pages
```

Query it directly from the CLI:

```bash
gbrain query "how do databases handle many transactions at once"
gbrain search "redis"                 # fast keyword search
gbrain graph concepts/mvcc-multi-version-concurrency-control --depth 2
```

> **One process at a time.** The brain runs on PGLite, which allows a single connection. If an MCP client (Claude Code/Cursor) has gbrain connected, its server holds the lock and CLI commands fail with "Timed out waiting for PGLite lock." Use one or the other: query via the AI/MCP tools while a client is connected, or quit the client to use the CLI.

### Use it from an AI (MCP)

`.mcp.json` registers gbrain's MCP server for Claude Code / Cursor / Claude Desktop. Restart the client to load it and approve the `gbrain` server when prompted. Then ask things like *"using gbrain, what do I already know related to consistent hashing?"* and the AI will query your brain (tools: `query`, `search`, `traverse_graph`, `get_backlinks`, …). This is the primary way to use it day-to-day.

Requirements at query time: the **Ollama service must be running** (`brew services start ollama`) so queries can be embedded.

> ChatGPT / web AIs need the remote HTTP server (`gbrain serve --http` + OAuth on a reachable host) — a separate, heavier setup not covered here.
