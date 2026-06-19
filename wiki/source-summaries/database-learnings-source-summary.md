---
title: "Source summary — Database learnings"
type: concept
sources:
  - raw/notion-exports/database-learnings.md
related:
  - "[[database-processing-and-query-layers]]"
  - "[[mvcc-multi-version-concurrency-control]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# Source summary — Database learnings

## Summary
This export is my layered notes on how databases process data and queries (collection/prep/input/output/storage layers and parse/semantic/opt/execute layers), plus deep dives on concurrency and structure: ACID, structured vs unstructured vs semi-structured, OLTP/OLAP/HTAP, shared-nothing vs shared-storage, and MVCC internals (xmin/xmax snapshot visibility + SSI-style dependencies).

## Detail
- Data vs information distinction.
- Batch vs real-time vs stream processing, and Lambda architecture.
- Query processing pipeline (parse → semantic analysis → optimization like indexing/caching/parallel/pushdown → execution plan → execute).
- Architecture:
  - OLTP/OLAP/HTAP
  - shared-nothing vs shared-storage examples
- Integrity:
  - ACID definitions
- Data types:
  - unstructured/semi-structured/structured and typical storage implications
- DBMS components:
  - storage manager, index structure, buffer manager, transaction manager, recover manager
- MVCC:
  - snapshot object fields and tuple visibility checks using xmin/xmax
  - update as delete+insert with tuple headers
  - SSI dependency graph via SIREAD locks

## Connections
- [[database-processing-and-query-layers]] — structured pipeline
- [[mvcc-multi-version-concurrency-control]] — MVCC deep dive

## Open Questions
- Parts are extremely “notes-y” (“god knows” section on execution plan generation). Next pass could convert those into actionable examples.

## Sources
- raw/notion-exports/database-learnings.md