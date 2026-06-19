---
title: "Source summary — Backend learnings"
type: source-summary
sources:
  - raw/notion-exports/backend-learnings.md
related:
  - "[[http-request-lifecycle-and-core-components]]"
  - "[[microservices-and-load-balancing-context]]"
  - "[[event-broker-vs-message-broker]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# Source summary — Backend learnings

## Summary
This Notion export is a big “systems architecture starter pack” in my casual voice: HTTP fundamentals (URL/origin/endpoint, methods, headers vs body, status codes), web auth (sessions vs JWT access/refresh), and backend architecture primitives (load balancers, microservices, event brokers, caching strategies, CORS, and websockets vs pub/sub). The through-line is how to reason about requests end-to-end and where reliability/performance tradeoffs appear.

## Detail
- Request pipeline vocabulary:
  - clients/servers, addressing (IP/domain/DNS/ports), origin CORS comparison, endpoint routing, request/response, headers vs body.
- HTTP methods + status code cheat sheet.
- Auth:
  - bcrypt credential check
  - session-based stateful auth
  - JWT access token + refresh token flow, HttpOnly refresh cookie, local `jwt.verify` verification.
  - notes also mention Auth0/Cognito as an outsourced auth layer.
- Architecture:
  - horizontal scaling + load balancer algorithms and sticky sessions
  - microservices as failure isolation
  - event broker vs message broker
  - caching patterns (cache-aside) and write strategies
- Networking patterns:
  - CORS flow with preflight OPTIONS
  - webhook polling vs webhook delivery
  - websockets persistent connection problem with load balancers, solution via sticky sessions + pub/sub.

## Connections
- [[http-request-lifecycle-and-core-components]] — vocabulary for HTTP request/response pieces
- [[microservices-and-load-balancing-context]] — load balancers + microservices story
- [[event-broker-vs-message-broker]] — command vs fact event design
- [[cache-aside-and-cache-write-strategies]] — cache-aside read and write strategies
- [[authentication-with-jwt-and-refresh-tokens]] — JWT verification + refresh flow

## Open Questions
- This file has lots of sections that end with “bla bla bla” (TLS) or are less actionable (“Router”, “Handlers/Controllers”, “Pub/sub”). Next ingest could turn those into more specific checklists/examples.

## Sources
- raw/notion-exports/backend-learnings.md