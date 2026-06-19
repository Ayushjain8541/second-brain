---
title: "JWT authentication + refresh tokens (and why middleware can verify locally)"
type: concept
sources:
  - raw/notion-exports/backend-learnings.md
related:
  - "[[auth0-and-cognito]]"
created: 2026-06-19
last-updated: 2026-06-19
---
# JWT authentication + refresh tokens (and why middleware can verify locally)

## Summary
I learned why JWT exists: it lets the server verify identity locally (by checking signature + expiry) instead of querying the DB on every request. The notes also cover the common access/refresh token setup: short-lived access token, longer-lived refresh token, and HttpOnly cookies for the refresh token.

## Detail
## The “DB every request” problem
- If auth is only “check username/password in DB every time”, the server needs to hit the DB per request, which is slow.

## Stateful auth vs JWT
### Stateful authentication (sessions)
- Browser stores session id in cookie.
- Server keeps an active session record, so it remembers the user.
- Tradeoff: server must maintain state.

### JWT (JSON Web Token)
JWT has 3 parts:
- **Header**: algorithm info used for signing
- **Payload**: user data (userid, role etc)
- **Signature**: cryptographic hash computed using a server secret

### Flow from the notes
1. First login:
   - verify credentials (by checking DB hash using bcrypt.compare)
   - issue **access token** (JWT) and **refresh token**
   - access token: short TTL (notes: ~15 mins)
   - refresh token: longer TTL (notes: ~30 days)
   - refresh token stored securely (notes: HttpOnly cookie) and server keeps refresh token in DB so it can invalidate/logout.
2. Subsequent requests:
   - client sends `Authorization: Bearer <token>`
   - middleware verifies JWT with `jwt.verify(token, SECRET_KEY)` and checks expiry.
3. If access token expires:
   - client calls a refresh endpoint using the refresh token in cookies.
   - server checks refresh token exists in DB, then signs a new access token.
4. If refresh token expires too:
   - user must login again.

## Connections
- [[auth0-and-cognito]] — outsourcing token issuance + public-key verification

## Open Questions
- My notes don’t specify exact claims (audience/issuer/roles mapping). If I end up using Auth0, I should store those claim requirements in a separate page.

## Sources
- Per raw/notion-exports/backend-learnings.md, sections “Auth”, “Authentication”, “Persistent authentication”, “JWT”, and the step-by-step access/refresh flow.