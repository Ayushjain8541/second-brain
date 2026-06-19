---
title: "AWS building blocks (from my notes)"
type: concept
sources:
  - raw/notion-exports/aws-learnings.md
related:
  - "[[event-broker-vs-message-broker]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# AWS building blocks (from my notes)

## Summary
I summarized a few AWS services in a consistent mental map: **Lambda** for event-driven compute, **API Gateway** as the front door (auth/security/rate limiting/routing), **S3** for large file storage, **EC2** for persistent servers/webhooks, and managed equivalents for DB, queues, routing events, and long-running workflows.

## Detail
## Compute and API entry
- **Lambda**
  - run code only when triggered,
  - pay only for compute,
  - AWS handles scaling/load balancing (event-driven).
- **Amazon API Gateway**
  - sits between user and microservices,
  - handles auth/security, rate limiting, routing to microservices.

## Storage and persistence
- **S3**
  - massive data lake for big files, videos, etc.
- **EC2**
  - persistent server you keep running for webhooks and long-running services (per notes).

## Database
- **Aurora DLB**
  - managed PostgreSQL-compatible database (per notes).

## Queues and routing
- **SQS**
  - queue/buffer for microservices,
  - avoids flooding services with too many requests at once.
  - workers (often lambdas) pull from the queue.
- **EventBridge**
  - router for events to microservices based on event calls/payload.

## Long-running workflows
- **Temporal**
  - breaks a very long process into “save states” so it can resume after failures.
  - it restarts from the saved state instead of starting from scratch.

## Connections
- [[event-broker-vs-message-broker]] — the AWS queue/router split in my notes (SQS vs EventBridge)

## Open Questions
- I should write separate pages for how Lambda, SQS, and EventBridge connect in a real flow, instead of keeping this as a bullet inventory.

## Sources
- Per raw/notion-exports/aws-learnings.md, sections Lambda, API gateway, S3, EC2, Aurora DLB, SQS, Eventbridge, Temporal.