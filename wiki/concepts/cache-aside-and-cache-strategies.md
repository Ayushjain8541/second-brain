---
title: "Cache-aside and cache write strategies"
type: concept
sources:
  - raw/notion-exports/backend-learnings.md
related:
  - "[[rate-limiting]]"
  - "[[microservices]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# Cache-aside and cache write strategies

## Summary
I learned the practical caching pattern I’ll actually use: **cache-aside**, where reads hit Redis first and fall back to the DB on a miss, then backfill the cache. For writes, there are multiple strategies (write-through, write-behind, write-around) with different tradeoffs around latency and risk.

## Detail
## Cache-aside (reading pattern)
- On request, my controller checks Redis first.
- **Cache-hit**: controller returns cached JSON immediately.
- **Cache-miss**: controller queries the DB, then saves the result into Redis with a **TTL** via a background write.

## Write strategies
### Write-through
- Write request goes to Redis first.
- Redis writes to DB.
- Success is only shown once DB write completes.
- Tradeoff: safer, but slower for the user.

### Write-behind
- Write request goes to Redis.
- Redis writes to DB concurrently.
- Tradeoff: user gets success fast, but risky, if DB write fails the data can “vanish”.

### Write-around
- Skip Redis on writes.
- Write directly to the DB.
- Tradeoff: simpler, but relies on cache invalidation behavior for consistency.

## Connections
- [[rate-limiting]] — caching and throttling often show up together in API middleware
- [[microservices]] — caching is often used to protect shared services/databases

## Open Questions
- My notes don’t specify concrete invalidation policies (e.g. which event updates Redis) beyond the idea of invalidating on UPDATE/DELETE, so I should turn that into a more actionable checklist next.

## Sources
- Per raw/notion-exports/backend-learnings.md, sections “Cache”, “How it works”, and the three write strategies (write-through, write-behind, write-around).