---
title: "MVCC (multi-version concurrency control) as snapshot reads"
type: concept
sources:
  - raw/notion-exports/database-learnings.md
related:
  - "[[database-processing-and-query-layers]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# MVCC (multi-version concurrency control) as snapshot reads

## Summary
I learned MVCC as: instead of locking rows for every transaction, the DB gives each transaction a **snapshot** so reads see a consistent view. Updates create new row versions (old versions remain), and visibility is determined using transaction ids (`xmin`, `xmax`) and the snapshot’s running transaction set.

## Detail
## The locking intuition problem
- If every transaction locks the row, other transactions wait.
- That can get slow, especially as concurrency grows.

## MVCC idea
- Each transaction creates a snapshot of the database with a timestamp-like object (notes: snapshot has an id).
- The transaction reads and writes against a logical view, while old versions stay available.

Git-branch analogy (from notes):
- a transaction works on its own branch until it commits.

## How conflicts are reasoned about
Notes emphasize “merge conflicts” not happening arbitrarily:
- conflicts happen in chained dependency scenarios.
- It’s modelled as a graph problem:
  - only matters when one transaction has **read-write (rw) dependency** on another.

## Tuple/header fields (as captured in notes)
Per notes, tuples store metadata:
- **xmin**: transaction id that created this tuple
- **xmax**: transaction id that deletes the tuple
- **t_ctid**: id of new updated tuple if updated

Update mechanism (as described in notes):
- In Postgres, `UPDATE` doesn’t modify in place.
- It treats it as delete + insert:
  - old tuple’s `xmax` is set
  - new tuple gets new `xmin`

## Snapshot visibility rules (from notes)
When scanning tuples, check:
- Is `xmin` committed? If not, ignore the tuple.
- Is `xmin` newer than my snapshot max? If yes, ignore (it’s from the future).
- Is `xmax` filled in, and did that deleting transaction commit before I started? If yes, ignore.

Notes also include:
- when a transaction reads a visible tuple, it creates a **SIREAD lock**
- if another transaction tries to update and conflicts with that read, the system adds dependency edges in the graph.

## Serialization level mentioned
- Notes call this **serializable snapshot isolation** (what MVCC uses, per notes).

## Connections
- [[database-processing-and-query-layers]] — query execution and snapshot reads tie together here

## Open Questions
- The notes are detailed but still a bit hand-wavy (“if another concurrent transaction comes along… add dependency graphh”).
  - I should later capture the exact Postgres algorithm details for SSI, especially how it detects cycles and decides aborts.

## Sources
- Per raw/notion-exports/database-learnings.md, section “MVCC (Multi version concurrency control)”.