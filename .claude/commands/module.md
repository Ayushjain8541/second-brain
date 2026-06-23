---
description: Build wiki project pages for my NUS modules.
argument-hint: (optional) a specific module code, e.g. CS2103T
---

You are building or updating wiki pages for the user's NUS modules. Each module page is a `project`-type hub: it pairs the official NUSMods scaffold with links to the user's own learnings. Follow CLAUDE.md exactly.

**Step 1 — Find the module data**
Look in `raw/nusmods/` for module files (e.g. `raw/nusmods/CS2103T.md`). These are the official NUSMods exports written by `fetch_modules.py`. If $ARGUMENTS names a specific module code, only process that one. Otherwise process every module file in `raw/nusmods/`.

If `raw/nusmods/` is empty or missing, stop and tell the user to add codes to `my-modules.md` and run `./env/bin/python fetch_modules.py` first. Do not invent module data.

**Step 2 — For each module, build the hub page**
Write to `wiki/projects/<code>-<slug>.md` (e.g. `wiki/projects/cs2103t-software-engineering.md`) with this structure:

```
---
title: "CS2103T — Software Engineering"
type: project
sources:
  - raw/nusmods/CS2103T.md
related:
  - "[[some-concept]]"
created: <today>
last-updated: <today>
---

# CS2103T — Software Engineering

## Summary
One or two lines on what this module is and where it sits in my degree. My voice.

## Official Overview
The factual scaffold from NUSMods: module aims, key topics, workload, prerequisites.
Keep this neutral and attribute it to NUSMods. Do not pad it or rewrite it as if it were my own words.

## What I Learned
A hub, not a dump. Link to the atomic concept pages that came from my notes, each with a
one-line note on how it connects to this module. For example:
- [[mvcc-multi-version-concurrency-control]] — how Postgres handles concurrent transactions, came up in the DB portion
- [[authentication-with-jwt-and-refresh-tokens]] — the auth model I dug into alongside this

If I have no learnings on file for this module yet, say so plainly and leave the section as a stub to fill in later.

## Open Questions
Gaps, things that confused me, threads to follow up.

## Sources
Prose attribution: the NUSMods file, plus any of my notes that fed the learnings.
```

**Step 3 — Link, don't duplicate**
To fill "What I Learned", scan `wiki/concepts/` and `wiki/source-summaries/` for pages whose topics match this module's syllabus (from the NUSMods description). Link to them with `[[page-name]]`. Never copy a concept's content into the module page; the concept pages stay the single source for shared ideas. If a relevant concept clearly should exist but doesn't yet, note it as a stub opportunity in Open Questions.

**Step 4 — Voice**
Read `wiki/meta/voice-profile.md` first. The Summary, What I Learned, and Open Questions sections are my own words, so follow the profile (first person, no em dashes, light on bold). The Official Overview is NUSMods' words, so keep it factual and attributed, not styled as mine.

**Step 5 — Update catalog and log**
Add each new page to the Projects section of `wiki/index.md`, and append a timestamped entry to `wiki/log.md` noting what was created or updated.

**Constraints**
- Never modify anything in `raw/`.
- Every page needs complete frontmatter (title, type: project, sources, related, created, last-updated).
- Attribute official content to NUSMods; attribute learnings to my notes.
