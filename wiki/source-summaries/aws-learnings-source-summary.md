---
title: "Source summary — AWS learnings"
type: source-summary
sources:
  - raw/notion-exports/aws-learnings.md
related:
  - "[[aws-components-from-notes]]"
  - "[[event-broker-vs-message-broker]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# Source summary — AWS learnings

## Summary
This export is a service-by-service mental model for common AWS building blocks. It connects compute (Lambda), API front door (API Gateway), storage (S3), persistent servers (EC2), DB (Aurora), queuing/routing (SQS/EventBridge), and workflow recovery (Temporal).

## Detail
- Lambda event-driven compute with pay-per-use.
- API Gateway as auth/security/rate limiting/routing layer.
- S3 as a big storage/data lake.
- EC2 as persistent servers.
- Aurora DLB as Postgres-compatible managed DB.
- SQS as buffering queue with workers consuming.
- EventBridge as routing based on event payload.
- Temporal as long-running workflow with save states and resume after failures.

## Connections
- [[aws-components-from-notes]] — the same inventory, structured
- [[event-broker-vs-message-broker]] — ties to the SQS/EventBridge split

## Open Questions
- I should add an end-to-end flow example (e.g. “S3 upload → EventBridge → SQS → Lambda → DB”), but the file alone is only inventory-level.

## Sources
- raw/notion-exports/aws-learnings.md