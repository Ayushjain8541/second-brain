---
title: "Database processing pipeline and query processing layers"
type: concept
sources:
  - raw/notion-exports/database-learnings.md
related:
  - "[[mvcc-multi-version-concurrency-control]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# Database processing pipeline and query processing layers

## Summary
I built a layered mental model of how databases move from raw input to usable results, and how a query gets transformed into an execution plan. This helps me reason about performance bottlenecks: parse/semantic analysis/optimization/execution, and earlier data prep/storage layers too.

## Detail
## Data processing layers (raw → information → output)
Notes define layers like:
1. **Collection layer**: collect raw data from sources.
2. **Preparation layer**: validate raw data, clean it, standardize it, possibly enrich.
3. **Input layer**: introduce prepared data into the system.
4. **Processing layer**: transform to information (arithmetic, sorting, summarizing, analysis, classification).
5. **Output layer**: convert internal representation to something readable for users.
6. **Storage layer**: store data/information durably, and index.

Batch vs real-time:
- **Batch**: collect over time then run analysis.
- **Real-time**: process per request.
- If it gets more advanced: **stream processing** for data that flows together.

**Lambda architecture** (from notes):
- batch path
- speed (real-time) path
- serve layer merges both.

## Query processing layers
Notes again split the flow into:
1. **Parse query**
2. **Semantic analysis**:
   - check table exists,
   - check permissions,
   - analyze query meaning.
3. **Optimization**:
   - indexing (hash or B+-tree),
   - caching,
   - parallel processing,
   - “push down” optimization (move processing closer to data).
4. **Execution plan generation**
5. **Execute it**
6. **Result**

## Connections
- [[mvcc-multi-version-concurrency-control]] — MVCC explains concurrency control for the “execute” stage and snapshot reads

## Open Questions
- My “execution plan generation” section is literally “god knows” in notes. I should capture a concrete example (e.g. `EXPLAIN ANALYZE` on a query) in a follow-up ingest.

## Sources
- Per raw/notion-exports/database-learnings.md, sections “Data Processing” and “Query processing”.