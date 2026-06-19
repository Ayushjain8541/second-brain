---
title: "Event broker vs message broker"
type: concept
sources:
  - raw/notion-exports/backend-learnings.md
related:
  - "[[lambda]]"
  - "[[aws-eventbridge]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# Event broker vs message broker

## Summary
I learned the distinction like this: a **message broker** is optimized for commands (“do this”), while an **event broker** is optimized for facts (“this happened”) and keeps an append-only log so consumers can replay. That difference changes retention, debuggability, and failure recovery.

## Detail
## Message broker (command style)
- Example: RabbitMQ, AWS SQS (per notes)
- “Destructive” queue:
  - consumer pulls the message,
  - broker deletes it once read.
- Retention tends to be transient.

## Event broker (fact style)
- Example: Apache Kafka, AWS Kinesis (per notes)
- Append-only stream:
  - written sequentially to disk,
  - event stays on disk.
- Consumer tracks its own offset, so it can replay from older points if needed (time machine vibe from notes).

## Extra mental model from AWS architecture notes
- AWS splits responsibilities:
  - **SQS**: dumb buffer/mailbox (holds messages, no routing brain).
  - **EventBridge**: router (inspects JSON payload, content-based filtering, routes copies into SQS queues).

## Connections
- [[lambda]] — event-driven compute that consumes queued work
- [[aws-eventbridge]] — routing layer between events and queues/services

## Open Questions
- My notes contrast brokers, but don’t go deep on ordering/guarantees (at-least-once, exactly-once). I should capture which guarantees I care about.

## Sources
- Per raw/notion-exports/backend-learnings.md, section “Event brokers” and the “Message Broker vs Event Broker” comparison.