---
description: Synthesise an answer from the wiki.
argument-hint: the question to answer
---

You are answering a question using only what is in the wiki. The question is:

$ARGUMENTS

**Step 1 — Orient**
Read `wiki/index.md` to get a map of all available pages.

**Step 2 — Gather relevant pages**
Identify and read every wiki page that is likely relevant to the question. When in doubt, read it — a broader read is better than a missed source.

**Step 3 — Synthesise**
Write a clear, direct answer grounded in what the wiki actually says. For every claim you make:
- Cite the wiki page it comes from, e.g. "(→ [[page-name]])"
- If two pages disagree on a point, state both positions explicitly and flag the contradiction rather than silently resolving it.

**Step 4 — Flag gaps**
If the wiki does not have enough information to answer the question fully, say so clearly. Identify which raw sources might fill the gap if they were ingested.

**Step 5 — Propose updates (do not write them)**
If answering revealed a connection between pages that is not yet cross-linked, or a concept that deserves its own page, propose the update in a `## Proposed Wiki Updates` section at the end. Do not create or modify any wiki pages without explicit confirmation.
