---
title: "Microservices and why load balancers show up"
type: concept
sources:
  - raw/notion-exports/backend-learnings.md
related:
  - "[[http-request-lifecycle-and-components]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# Microservices and why load balancers show up

## Summary
I learned the scaling storyline: as traffic increases, we add more server instances (horizontal scaling), so we need a load balancer to choose which instance handles each request. Then microservices are the next decoupling step, splitting a “giant server” into specialized services so one subsystem failing doesn’t take everything down.

## Detail
## Horizontal scaling and the load balancer
- When traffic grows, create multiple versions of the server.
- A question appears: which server should receive a user request?
- **Load balancer** sits between client and servers:
  - picks a server using algorithms like round robin / weighted variants / least connections.
  - forwards the request.

## Sticky sessions
- If a user is initially routed to server B, “sticky sessions” try to route the same user back to B for subsequent requests.

## Microservices
- Even after scaling, code can still be a single giant block.
- Microservices split that monolith into specialized independent services:
  - one service does payments
  - another does video processing
  - another handles analytics
- Failure isolation idea: if video processing crashes, payments can still work.

## Connections
- [[http-request-lifecycle-and-components]] — the request pipeline that gets routed to different handlers/services

## Open Questions
- My notes mention API Gateway but don’t fill in its responsibilities beyond “see backend learnings”. I should ingest AWS learnings later to connect the dots cleanly.

## Sources
- Per raw/notion-exports/backend-learnings.md, sections “Load balancers”, “Algorithms”, “Sticky sessions”, and “Microservices”.