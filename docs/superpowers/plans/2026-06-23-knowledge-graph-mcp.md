# Knowledge Graph MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the wiki as a Neo4j knowledge graph through a local MCP server, so other AIs can see what the user already knows and how it connects.

**Architecture:** A pure Python parser turns `wiki/*.md` into nodes and edges. A sync script upserts them into Neo4j Aura. A transport-agnostic engine runs Cypher queries. A stdio MCP server wraps the engine as five tools. Phase 2 (remote HTTP server for ChatGPT) is out of scope here.

**Tech Stack:** Python 3.14 (existing venv at `env/`), `neo4j` driver, `mcp` SDK (FastMCP, stdio), `PyYAML`, `python-dotenv`, `pytest`.

## Global Constraints

- No mastery / depth / level modelling anywhere. Knowledge is binary presence: a page is a node or it isn't. Copied verbatim from spec: "A concept is either in the graph (I know it) or not."
- Nodes use a single `:Page` label plus a `type` string property (`concept` | `project` | `person` | `source-summary`); `:Source` nodes hold provenance. (Plain Cypher cannot set dynamic labels without APOC, so type is a property — functionally equivalent for all queries here.)
- Relationship types: `RELATED_TO` (wikilinks), `COVERS` (project→concept), `DERIVED_FROM` (page→source).
- Neo4j credentials live ONLY in `.env` (already gitignored). Never hardcode them. Env vars: `NEO4J_URI`, `NEO4J_USER` (default `neo4j`), `NEO4J_PASSWORD`.
- Vector index is NOT built in this phase. Entry-matching uses Neo4j's full-text index only.
- Run all Python with the project venv: `./env/bin/python`, `./env/bin/pip`, `./env/bin/pytest`.
- Exclude these wiki files from the graph: any `README.md`, `index.md`, `log.md`, and anything under `wiki/meta/`. Include `concepts/`, `projects/`, `people/`, `source-summaries/`.

---

### Task 1: Project setup — dependencies, config, env scaffold

**Files:**
- Create: `requirements-kg.txt`
- Create: `.env.example`
- Create: `kg/__init__.py` (empty)
- Create: `kg/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `kg.config.neo4j_config() -> tuple[str, str, str]` returning `(uri, user, password)`; raises `RuntimeError` if `NEO4J_URI` or `NEO4J_PASSWORD` is missing.

- [ ] **Step 1: Add the dependency list**

Create `requirements-kg.txt`:

```
neo4j>=5.20
mcp>=1.2.0
PyYAML>=6.0
python-dotenv>=1.0
pytest>=8.0
```

- [ ] **Step 2: Install the dependencies**

Run: `./env/bin/pip install -r requirements-kg.txt`
Expected: ends with "Successfully installed ... neo4j-5.x mcp-1.x ..." (PyYAML, python-dotenv, pytest may already be satisfied).

- [ ] **Step 3: Create the env example**

Create `.env.example`:

```
# Neo4j Aura connection (copy to .env and fill in; .env is gitignored)
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
```

- [ ] **Step 4: Write the failing test for config loading**

Create `tests/test_config.py`:

```python
import importlib
import pytest
import kg.config as config


def test_neo4j_config_reads_env(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "neo4j+s://example.databases.neo4j.io")
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "secret")
    importlib.reload(config)
    assert config.neo4j_config() == (
        "neo4j+s://example.databases.neo4j.io", "neo4j", "secret",
    )


def test_neo4j_config_missing_raises(monkeypatch):
    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
    importlib.reload(config)
    with pytest.raises(RuntimeError):
        config.neo4j_config()


def test_user_defaults_to_neo4j(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "neo4j+s://x.databases.neo4j.io")
    monkeypatch.setenv("NEO4J_PASSWORD", "secret")
    monkeypatch.delenv("NEO4J_USER", raising=False)
    importlib.reload(config)
    assert config.neo4j_config()[1] == "neo4j"
```

- [ ] **Step 5: Run the test to verify it fails**

Run: `./env/bin/pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'kg.config'` (or AttributeError).

- [ ] **Step 6: Create the package and config module**

Create empty `kg/__init__.py`.

Create `kg/config.py`:

```python
"""Configuration loading for the knowledge-graph MCP. Reads Neo4j Aura
credentials from environment / .env. Credentials never live in code."""

import os
from dotenv import load_dotenv

load_dotenv()


def neo4j_config():
    """Return (uri, user, password). Raise if required values are missing."""
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD")
    if not uri or not password:
        raise RuntimeError(
            "Set NEO4J_URI and NEO4J_PASSWORD in your environment or .env "
            "(see .env.example)."
        )
    return uri, user, password
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `./env/bin/pytest tests/test_config.py -v`
Expected: 3 passed.

- [ ] **Step 8: Commit**

```bash
git add requirements-kg.txt .env.example kg/__init__.py kg/config.py tests/test_config.py
git commit -m "feat(kg): project setup — deps, config loader, env scaffold"
```

---

### Task 2: Wiki markdown parser (pure functions)

**Files:**
- Create: `kg/parse.py`
- Test: `tests/test_parse.py`
- Test fixtures: `tests/fixtures/wiki/concepts/alpha.md`, `tests/fixtures/wiki/concepts/beta.md`, `tests/fixtures/wiki/projects/cs0000x-demo.md`, `tests/fixtures/wiki/README.md`

**Interfaces:**
- Produces:
  - `kg.parse.Page` dataclass: `slug: str`, `title: str`, `type: str`, `summary: str`, `body: str`, `sources: list[str]`, `related: list[str]`, `created: str`, `last_updated: str`.
  - `kg.parse.slug_from_path(path: str) -> str`
  - `kg.parse.extract_wikilinks(text: str) -> list[str]`
  - `kg.parse.parse_page(path: str, text: str) -> Page`
  - `kg.parse.parse_wiki(wiki_dir: str) -> list[Page]`
  - `kg.parse.build_graph(pages: list[Page]) -> GraphData` where `GraphData` is a dataclass with `nodes: list[Page]`, `related_edges: list[tuple[str, str]]`, `covers_edges: list[tuple[str, str]]`, `source_edges: list[tuple[str, str]]` (each tuple is `(src_slug, dst_slug_or_source_path)`).

- [ ] **Step 1: Write the fixtures**

Create `tests/fixtures/wiki/concepts/alpha.md`:

```markdown
---
title: "Alpha Concept"
type: concept
sources:
  - raw/notion-exports/alpha.md
related:
  - "[[beta]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# Alpha Concept

## Summary
Alpha is the first thing. It connects to beta and is used everywhere.

## Detail
Some detail about alpha that also mentions [[beta]] again inline.
```

Create `tests/fixtures/wiki/concepts/beta.md`:

```markdown
---
title: "Beta Concept"
type: concept
sources:
  - raw/notion-exports/alpha.md
related: []
created: 2026-06-19
last-updated: 2026-06-20
---
# Beta Concept

## Summary
Beta is the second thing.
```

Create `tests/fixtures/wiki/projects/cs0000x-demo.md`:

```markdown
---
title: "CS0000X — Demo Module"
type: project
sources:
  - raw/nusmods/CS0000X.md
related:
  - "[[alpha]]"
created: 2026-06-21
last-updated: 2026-06-21
---
# CS0000X — Demo Module

## Summary
A demo module that covers alpha.
```

Create `tests/fixtures/wiki/README.md`:

```markdown
# Folder readme — must be ignored by the parser
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_parse.py`:

```python
import os
import kg.parse as parse

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "wiki")


def test_slug_from_path():
    assert parse.slug_from_path("wiki/concepts/mvcc-snapshots.md") == "mvcc-snapshots"
    assert parse.slug_from_path("alpha.md") == "alpha"


def test_extract_wikilinks():
    text = "see [[beta]] and [[gamma-thing]] but not [plain](x)"
    assert parse.extract_wikilinks(text) == ["beta", "gamma-thing"]


def test_parse_page_fields():
    path = os.path.join(FIX, "concepts", "alpha.md")
    with open(path, encoding="utf-8") as f:
        page = parse.parse_page(path, f.read())
    assert page.slug == "alpha"
    assert page.title == "Alpha Concept"
    assert page.type == "concept"
    assert page.summary.startswith("Alpha is the first thing")
    assert page.sources == ["raw/notion-exports/alpha.md"]
    # related comes from frontmatter AND inline body links, de-duplicated
    assert page.related == ["beta"]
    assert page.created == "2026-06-19"
    assert page.last_updated == "2026-06-19"


def test_parse_wiki_excludes_readme():
    pages = parse.parse_wiki(FIX)
    slugs = sorted(p.slug for p in pages)
    assert slugs == ["alpha", "beta", "cs0000x-demo"]


def test_build_graph_edges():
    pages = parse.parse_wiki(FIX)
    g = parse.build_graph(pages)
    # alpha -> beta is concept->concept = related
    assert ("alpha", "beta") in g.related_edges
    # cs0000x-demo (project) -> alpha (concept) = covers, NOT related
    assert ("cs0000x-demo", "alpha") in g.covers_edges
    assert ("cs0000x-demo", "alpha") not in g.related_edges
    # source edges
    assert ("alpha", "raw/notion-exports/alpha.md") in g.source_edges


def test_build_graph_skips_dangling_links():
    # a page linking to a non-existent slug produces no edge
    pages = [
        parse.Page(slug="x", title="X", type="concept", summary="", body="[[ghost]]",
                   sources=[], related=["ghost"], created="2026-01-01", last_updated="2026-01-01"),
    ]
    g = parse.build_graph(pages)
    assert g.related_edges == []
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `./env/bin/pytest tests/test_parse.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'kg.parse'`.

- [ ] **Step 4: Implement the parser**

Create `kg/parse.py`:

```python
"""Pure functions that turn wiki markdown into graph nodes and edges.
No I/O beyond reading files in parse_wiki; no Neo4j here."""

import os
import re
from dataclasses import dataclass, field

import yaml

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
EXCLUDED_NAMES = {"readme.md", "index.md", "log.md"}
EXCLUDED_DIRS = {"meta"}


@dataclass
class Page:
    slug: str
    title: str
    type: str
    summary: str
    body: str
    sources: list = field(default_factory=list)
    related: list = field(default_factory=list)
    created: str = ""
    last_updated: str = ""


@dataclass
class GraphData:
    nodes: list = field(default_factory=list)
    related_edges: list = field(default_factory=list)
    covers_edges: list = field(default_factory=list)
    source_edges: list = field(default_factory=list)


def slug_from_path(path):
    return os.path.splitext(os.path.basename(path))[0]


def extract_wikilinks(text):
    """Return wikilink targets in order, de-duplicated, preserving first seen."""
    seen, out = set(), []
    for m in WIKILINK_RE.findall(text or ""):
        slug = m.strip()
        if slug and slug not in seen:
            seen.add(slug)
            out.append(slug)
    return out


def _split_frontmatter(text):
    """Return (frontmatter_dict, body_str). Tolerates a missing block."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            fm = yaml.safe_load(parts[1]) or {}
            return fm, parts[2].lstrip("\n")
    return {}, text


def _extract_summary(body):
    """Return the text under a '## Summary' heading, up to the next '## '."""
    lines = body.splitlines()
    out, capturing = [], False
    for line in lines:
        if line.strip().lower() == "## summary":
            capturing = True
            continue
        if capturing and line.startswith("## "):
            break
        if capturing:
            out.append(line)
    return "\n".join(out).strip()


def parse_page(path, text):
    fm, body = _split_frontmatter(text)
    fm_related = extract_wikilinks(" ".join(fm.get("related", []) or []))
    body_related = extract_wikilinks(body)
    related = []
    for s in fm_related + body_related:
        if s not in related:
            related.append(s)
    return Page(
        slug=slug_from_path(path),
        title=str(fm.get("title", slug_from_path(path))),
        type=str(fm.get("type", "concept")),
        summary=_extract_summary(body),
        body=body,
        sources=list(fm.get("sources", []) or []),
        related=related,
        created=str(fm.get("created", "")),
        last_updated=str(fm.get("last-updated", "")),
    )


def parse_wiki(wiki_dir):
    pages = []
    for root, _, files in os.walk(wiki_dir):
        if os.path.basename(root).lower() in EXCLUDED_DIRS:
            continue
        for name in files:
            if not name.endswith(".md") or name.lower() in EXCLUDED_NAMES:
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as f:
                pages.append(parse_page(path, f.read()))
    return pages


def build_graph(pages):
    by_slug = {p.slug: p for p in pages}
    g = GraphData(nodes=list(pages))
    for p in pages:
        for target in p.related:
            if target not in by_slug:
                continue  # skip dangling links to non-existent pages
            if p.type == "project" and by_slug[target].type == "concept":
                g.covers_edges.append((p.slug, target))
            else:
                g.related_edges.append((p.slug, target))
        for src in p.sources:
            g.source_edges.append((p.slug, src))
    return g
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `./env/bin/pytest tests/test_parse.py -v`
Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add kg/parse.py tests/test_parse.py tests/fixtures/
git commit -m "feat(kg): wiki markdown parser and graph builder"
```

---

### Task 3: Graph sync to Neo4j

**Files:**
- Create: `kg/graph_sync.py`
- Create: `sync_graph.py` (CLI entrypoint at vault root)
- Create: `tests/conftest.py`
- Test: `tests/test_graph_sync.py`

**Interfaces:**
- Consumes: `kg.config.neo4j_config`, `kg.parse.parse_wiki`, `kg.parse.build_graph`.
- Produces:
  - `kg.graph_sync.ensure_indexes(driver) -> None` — creates the full-text index if absent.
  - `kg.graph_sync.sync(driver, wiki_dir: str) -> dict` — upserts nodes/edges, prunes stale, returns `{"pages": int, "sources": int, "related": int, "covers": int}`.
  - `kg.graph_sync.get_driver()` — returns a `neo4j.Driver` built from `neo4j_config()`.

- [ ] **Step 1: Write the shared test fixture (driver, gated on a TEST uri)**

Create `tests/conftest.py`:

```python
import os
import pytest

# Integration tests use a DISPOSABLE Neo4j (local Docker or a throwaway Aura),
# never the real graph. Set NEO4J_TEST_URI / NEO4J_TEST_PASSWORD to enable them.
# Without those, integration tests skip and only the pure parser tests run.


@pytest.fixture
def driver():
    uri = os.environ.get("NEO4J_TEST_URI")
    password = os.environ.get("NEO4J_TEST_PASSWORD")
    if not uri or not password:
        pytest.skip("NEO4J_TEST_URI/NEO4J_TEST_PASSWORD not set; skipping integration test")
    from neo4j import GraphDatabase
    user = os.environ.get("NEO4J_TEST_USER", "neo4j")
    drv = GraphDatabase.driver(uri, auth=(user, password))
    # Clean slate so tests are deterministic
    with drv.session() as s:
        s.run("MATCH (n) DETACH DELETE n")
    yield drv
    with drv.session() as s:
        s.run("MATCH (n) DETACH DELETE n")
    drv.close()
```

- [ ] **Step 2: Write the failing idempotency test**

Create `tests/test_graph_sync.py`:

```python
import os
import kg.graph_sync as gs

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "wiki")


def _counts(driver):
    with driver.session() as s:
        pages = s.run("MATCH (p:Page) RETURN count(p) AS c").single()["c"]
        rels = s.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) AS c").single()["c"]
        covers = s.run("MATCH ()-[r:COVERS]->() RETURN count(r) AS c").single()["c"]
        return pages, rels, covers


def test_sync_is_idempotent(driver):
    gs.ensure_indexes(driver)
    first = gs.sync(driver, FIX)
    counts_after_first = _counts(driver)
    second = gs.sync(driver, FIX)
    counts_after_second = _counts(driver)
    assert counts_after_first == counts_after_second
    assert first == second
    # 3 pages, 1 related (alpha->beta), 1 covers (demo->alpha)
    assert counts_after_first == (3, 1, 1)


def test_sync_prunes_deleted_pages(driver, tmp_path):
    # sync the real fixtures, then sync an empty dir → all pruned
    gs.sync(driver, FIX)
    empty = tmp_path / "empty_wiki"
    empty.mkdir()
    gs.sync(driver, str(empty))
    assert _counts(driver)[0] == 0
```

- [ ] **Step 3: Run to verify it fails**

Run: `./env/bin/pytest tests/test_graph_sync.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'kg.graph_sync'` (or SKIP if no test DB configured — if skipped, still implement and rely on Step 5's manual check).

- [ ] **Step 4: Implement the sync module**

Create `kg/graph_sync.py`:

```python
"""Upsert the parsed wiki graph into Neo4j. Idempotent: MERGE on slug,
rebuild edges each run, prune nodes whose pages no longer exist."""

from neo4j import GraphDatabase

from kg.config import neo4j_config
from kg.parse import parse_wiki, build_graph

FULLTEXT_INDEX = "pageText"


def get_driver():
    uri, user, password = neo4j_config()
    return GraphDatabase.driver(uri, auth=(user, password))


def ensure_indexes(driver):
    with driver.session() as s:
        s.run(
            f"CREATE FULLTEXT INDEX {FULLTEXT_INDEX} IF NOT EXISTS "
            "FOR (p:Page) ON EACH [p.title, p.summary, p.body]"
        )


def sync(driver, wiki_dir):
    pages = parse_wiki(wiki_dir)
    g = build_graph(pages)
    slugs = [p.slug for p in g.nodes]
    source_paths = sorted({src for _, src in g.source_edges})

    page_rows = [
        {
            "slug": p.slug, "title": p.title, "type": p.type,
            "summary": p.summary, "body": p.body,
            "created": p.created, "lastUpdated": p.last_updated,
        }
        for p in g.nodes
    ]

    with driver.session() as s:
        # Upsert page nodes
        s.run(
            """
            UNWIND $rows AS row
            MERGE (p:Page {slug: row.slug})
            SET p.title = row.title, p.type = row.type, p.summary = row.summary,
                p.body = row.body, p.created = row.created, p.lastUpdated = row.lastUpdated
            """,
            rows=page_rows,
        )
        # Upsert source nodes
        s.run(
            "UNWIND $paths AS path MERGE (:Source {path: path})",
            paths=source_paths,
        )
        # Rebuild edges: clear ours, then recreate from current data
        s.run("MATCH ()-[r:RELATED_TO|COVERS|DERIVED_FROM]->() DELETE r")
        s.run(
            """
            UNWIND $edges AS e
            MATCH (a:Page {slug: e[0]}) MATCH (b:Page {slug: e[1]})
            MERGE (a)-[:RELATED_TO]->(b)
            """,
            edges=g.related_edges,
        )
        s.run(
            """
            UNWIND $edges AS e
            MATCH (a:Page {slug: e[0]}) MATCH (b:Page {slug: e[1]})
            MERGE (a)-[:COVERS]->(b)
            """,
            edges=g.covers_edges,
        )
        s.run(
            """
            UNWIND $edges AS e
            MATCH (a:Page {slug: e[0]}) MATCH (b:Source {path: e[1]})
            MERGE (a)-[:DERIVED_FROM]->(b)
            """,
            edges=g.source_edges,
        )
        # Prune pages and sources no longer present
        s.run("MATCH (p:Page) WHERE NOT p.slug IN $slugs DETACH DELETE p", slugs=slugs)
        s.run(
            "MATCH (src:Source) WHERE NOT src.path IN $paths DETACH DELETE src",
            paths=source_paths,
        )

    return {
        "pages": len(g.nodes),
        "sources": len(source_paths),
        "related": len(g.related_edges),
        "covers": len(g.covers_edges),
    }
```

- [ ] **Step 5: Create the CLI entrypoint**

Create `sync_graph.py` (vault root):

```python
#!/usr/bin/env python3
"""Sync the wiki into the Neo4j knowledge graph.

Usage:
    ./env/bin/python sync_graph.py
"""

import os
import sys

from kg.graph_sync import get_driver, ensure_indexes, sync

WIKI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wiki")


def main():
    try:
        driver = get_driver()
    except RuntimeError as e:
        print(f"Config error: {e}")
        return 1
    try:
        ensure_indexes(driver)
        stats = sync(driver, WIKI_DIR)
        print(
            f"Synced {stats['pages']} pages, {stats['sources']} sources, "
            f"{stats['related']} related edges, {stats['covers']} covers edges."
        )
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run the tests**

Run: `./env/bin/pytest tests/test_graph_sync.py -v`
Expected: 2 passed if a test DB is configured; otherwise 2 skipped (acceptable — Step 7 is the live check).

- [ ] **Step 7: Manual live check against Aura**

Ensure `.env` has real Aura credentials, then run: `./env/bin/python sync_graph.py`
Expected: prints e.g. `Synced 12 pages, 4 sources, 6 related edges, 2 covers edges.` with no errors.

- [ ] **Step 8: Commit**

```bash
git add kg/graph_sync.py sync_graph.py tests/conftest.py tests/test_graph_sync.py
git commit -m "feat(kg): sync wiki graph into Neo4j (idempotent upsert + prune)"
```

---

### Task 4: Knowledge query engine

**Files:**
- Create: `kg/engine.py`
- Test: `tests/test_engine.py`

**Interfaces:**
- Consumes: a `neo4j.Driver`, plus `kg.graph_sync.FULLTEXT_INDEX`.
- Produces (all take `driver` as first arg, return plain Python data):
  - `kg.engine.primer(driver) -> list[dict]` — `[{"type": str, "items": [{"slug","title","summary"}]}]`.
  - `kg.engine.search_knowledge(driver, query: str, limit: int = 8) -> list[dict]` — `[{"slug","title","summary","score"}]`.
  - `kg.engine.get_concept(driver, slug: str) -> dict | None` — `{"slug","title","type","body","neighbors":[{"slug","title"}]}` or `None`.
  - `kg.engine.related_to(driver, slug: str, hops: int = 1) -> list[dict]` — `[{"slug","title","type"}]`.
  - `kg.engine.bridge(driver, topic: str, limit: int = 5) -> list[dict]` — `[{"slug","title","summary","neighbors":[{"slug","title"}]}]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_engine.py`:

```python
import os
import pytest
import kg.graph_sync as gs
import kg.engine as engine

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "wiki")


@pytest.fixture
def seeded(driver):
    gs.ensure_indexes(driver)
    gs.sync(driver, FIX)
    return driver


def test_primer_groups_by_type(seeded):
    groups = {g["type"]: g for g in engine.primer(seeded)}
    assert "concept" in groups and "project" in groups
    concept_slugs = {i["slug"] for i in groups["concept"]["items"]}
    assert {"alpha", "beta"} <= concept_slugs


def test_get_concept_returns_body_and_neighbors(seeded):
    c = engine.get_concept(seeded, "alpha")
    assert c["title"] == "Alpha Concept"
    assert "first thing" in c["body"]
    neighbor_slugs = {n["slug"] for n in c["neighbors"]}
    assert "beta" in neighbor_slugs  # alpha -[:RELATED_TO]- beta


def test_get_concept_missing_returns_none(seeded):
    assert engine.get_concept(seeded, "does-not-exist") is None


def test_related_to_one_hop(seeded):
    rel = {r["slug"] for r in engine.related_to(seeded, "alpha", hops=1)}
    assert "beta" in rel


def test_search_knowledge_finds_by_text(seeded):
    hits = engine.search_knowledge(seeded, "second thing", limit=5)
    assert any(h["slug"] == "beta" for h in hits)


def test_bridge_returns_anchors_with_neighbors(seeded):
    anchors = engine.bridge(seeded, "first thing connects", limit=5)
    assert any(a["slug"] == "alpha" for a in anchors)
    alpha = next(a for a in anchors if a["slug"] == "alpha")
    assert "neighbors" in alpha
```

- [ ] **Step 2: Run to verify it fails**

Run: `./env/bin/pytest tests/test_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'kg.engine'` (or SKIP without a test DB).

- [ ] **Step 3: Implement the engine**

Create `kg/engine.py`:

```python
"""Transport-agnostic knowledge queries over the Neo4j graph. Each function
takes a driver and returns plain Python data (dicts/lists). No MCP here."""

from kg.graph_sync import FULLTEXT_INDEX


def primer(driver):
    with driver.session() as s:
        rows = s.run(
            """
            MATCH (p:Page)
            RETURN p.type AS type,
                   collect({slug: p.slug, title: p.title, summary: p.summary}) AS items
            ORDER BY type
            """
        ).data()
    return rows


def search_knowledge(driver, query, limit=8):
    with driver.session() as s:
        rows = s.run(
            f"""
            CALL db.index.fulltext.queryNodes('{FULLTEXT_INDEX}', $q) YIELD node, score
            RETURN node.slug AS slug, node.title AS title,
                   node.summary AS summary, score
            ORDER BY score DESC LIMIT $limit
            """,
            q=query, limit=limit,
        ).data()
    return rows


def get_concept(driver, slug):
    with driver.session() as s:
        rec = s.run(
            """
            MATCH (p:Page {slug: $slug})
            OPTIONAL MATCH (p)-[:RELATED_TO|COVERS]-(n:Page)
            RETURN p.slug AS slug, p.title AS title, p.type AS type, p.body AS body,
                   collect(DISTINCT {slug: n.slug, title: n.title}) AS neighbors
            """,
            slug=slug,
        ).single()
    if rec is None or rec["slug"] is None:
        return None
    data = rec.data()
    data["neighbors"] = [n for n in data["neighbors"] if n["slug"] is not None]
    return data


def related_to(driver, slug, hops=1):
    hops = 2 if int(hops) >= 2 else 1  # clamp; only 1 or 2 supported
    with driver.session() as s:
        rows = s.run(
            f"""
            MATCH (p:Page {{slug: $slug}})-[:RELATED_TO|COVERS*1..{hops}]-(n:Page)
            RETURN DISTINCT n.slug AS slug, n.title AS title, n.type AS type
            """,
            slug=slug,
        ).data()
    return rows


def bridge(driver, topic, limit=5):
    with driver.session() as s:
        rows = s.run(
            f"""
            CALL db.index.fulltext.queryNodes('{FULLTEXT_INDEX}', $q) YIELD node, score
            WITH node, score ORDER BY score DESC LIMIT $limit
            OPTIONAL MATCH (node)-[:RELATED_TO|COVERS]-(n:Page)
            RETURN node.slug AS slug, node.title AS title, node.summary AS summary,
                   collect(DISTINCT {{slug: n.slug, title: n.title}}) AS neighbors
            """,
            q=topic, limit=limit,
        ).data()
    for r in rows:
        r["neighbors"] = [n for n in r["neighbors"] if n["slug"] is not None]
    return rows
```

- [ ] **Step 4: Run the tests**

Run: `./env/bin/pytest tests/test_engine.py -v`
Expected: 6 passed with a test DB; otherwise 6 skipped (rely on Task 5 manual check).

- [ ] **Step 5: Commit**

```bash
git add kg/engine.py tests/test_engine.py
git commit -m "feat(kg): knowledge query engine (primer, search, get, related, bridge)"
```

---

### Task 5: Local stdio MCP server

**Files:**
- Create: `kg/server.py`
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes: `kg.engine` functions, `kg.graph_sync.get_driver`.
- Produces: a runnable MCP stdio server (`./env/bin/python -m kg.server`) exposing five tools that return markdown strings: `knowledge_primer()`, `search_knowledge(topic)`, `get_concept(slug)`, `related_to(slug, hops=1)`, `bridge(new_topic)`.

- [ ] **Step 1: Write the failing test (formatter is pure and unit-testable)**

Create `tests/test_server.py`:

```python
import kg.server as server


def test_format_primer_renders_markdown():
    groups = [
        {"type": "concept", "items": [
            {"slug": "alpha", "title": "Alpha", "summary": "First thing."},
        ]},
        {"type": "project", "items": [
            {"slug": "cs0000x-demo", "title": "CS0000X — Demo", "summary": "A demo."},
        ]},
    ]
    md = server.format_primer(groups)
    assert "## concept" in md
    assert "alpha" in md and "First thing." in md
    assert "## project" in md


def test_format_bridge_lists_anchors_and_neighbors():
    anchors = [
        {"slug": "alpha", "title": "Alpha", "summary": "First.",
         "neighbors": [{"slug": "beta", "title": "Beta"}]},
    ]
    md = server.format_bridge("some new topic", anchors)
    assert "Alpha" in md
    assert "beta" in md


def test_format_primer_handles_empty():
    assert "Nothing" in server.format_primer([])


def test_tools_are_registered():
    names = {t.name for t in server.mcp._tool_manager.list_tools()}
    assert {"knowledge_primer", "search_knowledge", "get_concept",
            "related_to", "bridge"} <= names
```

- [ ] **Step 2: Run to verify it fails**

Run: `./env/bin/pytest tests/test_server.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'kg.server'`.

- [ ] **Step 3: Implement the server**

Create `kg/server.py`:

```python
"""Local stdio MCP server exposing the knowledge graph as five tools.
Run: ./env/bin/python -m kg.server

Formatting helpers (format_*) are pure so they can be unit-tested without a DB.
"""

from mcp.server.fastmcp import FastMCP

from kg.graph_sync import get_driver
from kg import engine

mcp = FastMCP("second-brain-knowledge")

_driver = None


def driver():
    """Lazily open a single shared Neo4j driver."""
    global _driver
    if _driver is None:
        _driver = get_driver()
    return _driver


# ---- pure formatters -------------------------------------------------------

def format_primer(groups):
    if not groups:
        return "Nothing in the knowledge graph yet. Run sync_graph.py first."
    out = ["# What I already know\n"]
    for g in groups:
        out.append(f"## {g['type']}")
        for item in g["items"]:
            summary = (item.get("summary") or "").strip().replace("\n", " ")
            out.append(f"- **{item['title']}** (`{item['slug']}`) — {summary}")
        out.append("")
    return "\n".join(out).strip()


def format_hits(hits):
    if not hits:
        return "No matching concepts found in what I know."
    return "\n".join(
        f"- **{h['title']}** (`{h['slug']}`) — {(h.get('summary') or '').strip()}"
        for h in hits
    )


def format_concept(c):
    if c is None:
        return "I have no note on that concept."
    neighbors = ", ".join(f"[[{n['slug']}]]" for n in c["neighbors"]) or "none"
    return f"# {c['title']} (`{c['slug']}`)\n\nConnected to: {neighbors}\n\n{c['body']}"


def format_related(slug, rows):
    if not rows:
        return f"`{slug}` has no recorded connections."
    return f"Connected to `{slug}`:\n" + "\n".join(
        f"- **{r['title']}** (`{r['slug']}`, {r['type']})" for r in rows
    )


def format_bridge(topic, anchors):
    if not anchors:
        return (f"I don't have notes that clearly connect to \"{topic}\". "
                "Teach it from scratch.")
    out = [f"To explain \"{topic}\", anchor on what I already know:\n"]
    for a in anchors:
        nb = ", ".join(n["title"] for n in a["neighbors"]) or "none"
        summary = (a.get("summary") or "").strip().replace("\n", " ")
        out.append(f"- **{a['title']}** (`{a['slug']}`) — {summary}\n  connects to: {nb}")
    return "\n".join(out)


# ---- tools -----------------------------------------------------------------

@mcp.tool()
def knowledge_primer() -> str:
    """Load a compact map of everything the user already knows, grouped by area.
    Call this at the start of a teaching conversation."""
    return format_primer(engine.primer(driver()))


@mcp.tool()
def search_knowledge(topic: str) -> str:
    """Find the concepts the user already has notes on for a given topic."""
    return format_hits(engine.search_knowledge(driver(), topic))


@mcp.tool()
def get_concept(slug: str) -> str:
    """Get the user's full note on one concept, plus its connections."""
    return format_concept(engine.get_concept(driver(), slug))


@mcp.tool()
def related_to(slug: str, hops: int = 1) -> str:
    """List concepts connected to a given concept (1 or 2 hops away)."""
    return format_related(slug, engine.related_to(driver(), slug, hops))


@mcp.tool()
def bridge(new_topic: str) -> str:
    """Given a new topic to teach, return the concepts the user already knows
    that are closest to it, so you can anchor the explanation in them."""
    return format_bridge(new_topic, engine.bridge(driver(), new_topic))


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Run the tests**

Run: `./env/bin/pytest tests/test_server.py -v`
Expected: 4 passed.

- [ ] **Step 5: Manual MCP smoke test with the inspector**

Run: `./env/bin/python -m kg.server` should start without error (Ctrl-C to stop). Then with the inspector: `npx @modelcontextprotocol/inspector ./env/bin/python -m kg.server` — confirm the five tools list, and calling `knowledge_primer` returns your real concepts (requires `.env` + a prior `sync_graph.py` run).

- [ ] **Step 6: Register the server in your MCP client**

For Claude Code, add to the project's MCP config (`.mcp.json` at vault root):

```json
{
  "mcpServers": {
    "second-brain-knowledge": {
      "command": "./env/bin/python",
      "args": ["-m", "kg.server"]
    }
  }
}
```

Restart the client and confirm the `second-brain-knowledge` tools appear.

- [ ] **Step 7: Commit**

```bash
git add kg/server.py tests/test_server.py .mcp.json
git commit -m "feat(kg): local stdio MCP server exposing the knowledge graph"
```

---

## Notes for the implementer

- Run everything with the venv: `./env/bin/python`, `./env/bin/pytest`.
- Tasks 1 and 2 need no database and their tests always run. Tasks 3 and 4 have integration tests that **skip** unless `NEO4J_TEST_URI` / `NEO4J_TEST_PASSWORD` point at a **disposable** Neo4j (local Docker `docker run -p7687:7687 -e NEO4J_AUTH=neo4j/testtest neo4j:5`, or a throwaway Aura instance). Never point the test vars at the real graph — the fixture wipes the database.
- The real graph lives in your Aura instance, reached via `.env` (`NEO4J_URI` etc.), used by `sync_graph.py` and the server.
- After implementing, the end-to-end path is: fill `.env` → `./env/bin/python sync_graph.py` → register the MCP server → ask another AI to call `knowledge_primer` / `bridge`.
- Phase 2 (remote HTTP MCP + auth for ChatGPT) reuses `kg/engine.py` unchanged; only a new transport module is added. Out of scope for this plan.
