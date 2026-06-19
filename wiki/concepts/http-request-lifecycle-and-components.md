---
title: "HTTP request lifecycle and core components"
type: concept
sources:
  - raw/notion-exports/backend-learnings.md
related:
  - "[[microservices]]"
  - "[[api-gateway]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# HTTP request lifecycle and core components

## Summary
I learned to think of a web request as a pipeline: client builds a request (URL + headers + optional body), server routes it through middleware (auth, rate limits, etc), runs a handler/controller function, then returns a response (status code + headers + body). The “core” terms that keep showing up are URL/origin/endpoint, HTTP methods, and headers vs body.

## Detail
## The participants
- **Client**: anything that sends a request, browser/mobile app/another service.
- **Server**: waits for requests, does work, responds.
- **Browser**: a client that renders HTML/CSS/JS.

## Addressing basics
- **IP address**: numeric machine address.
- **Domain**: human name that maps to IP.
- **DNS**: phone book from domain → IP.
- **Port**: a “door” on a machine, used to run multiple services.
- **Localhost**: your own machine.
- **URL**: full address of a specific resource (protocol + domain + port + path).
- **Origin**: protocol + domain + port, what CORS compares.
- **Endpoint**: specific path that does something on the server.

## The HTTP “conversation”
- **HTTP**: agreed format for client/server communication.
- **HTTPS**: HTTP + TLS encryption in transit.
- **Request**: message from client to server.
- **Response**: message from server to client.
- **Header**: metadata (example: `Content-Type`, `Authorization`).
- **Body**: actual payload (JSON etc).

## HTTP methods I keep using
- **GET**: fetch data, no body sent (per notes)
- **POST**: create something new
- **PUT**: replace a resource
- **PATCH**: partially update a resource
- **DELETE**: remove a resource

## Auth-related storage primitives (browser-side)
- **Cookie**: server tells browser to store it, browser attaches it automatically.
- **localStorage**: JS-accessible storage (contrasted with HttpOnly cookies).
- **Session**: server-side record of logged-in user, identified by session id in cookie.

## Status codes (what I should map to what went wrong)
- **200**: success
- **201**: created
- **400**: bad request
- **401**: not authenticated
- **403**: authenticated but not authorized
- **404**: resource not found
- **500**: server crashed

## Connections
- [[microservices]] — why requests get routed to specialized services
- [[api-gateway]] — where routing + auth/rate limiting often gets centralized

## Open Questions
- In my notes, TLS is “bla bla bla”, I should add what I actually need (e.g. handshake, certificates, what gets encrypted).

## Sources
- Per the Notion page “Backend learnings” (raw/notion-exports/backend-learnings.md), plus its sections on Addressing, HTTP conversation, HTTP methods, Storage, Status Codes, and the request pipeline.