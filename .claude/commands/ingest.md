---
description: Ingest new files from raw/ into wiki/.
argument-hint: (optional) number of sources to process this run
---

You are ingesting new source files from `raw/` into the wiki. Follow the rules in CLAUDE.md exactly.

**Step 1 — Discover unread sources**
Scan all subfolders of `raw/` for files. Cross-reference `wiki/log.md` to identify which files have already been ingested (they will have a log entry). Build a list of files that have not yet been processed.

If `wiki/log.md` has no ingest entries (only its header), treat this as the first run: assume every file in `raw/` is new and proceed without asking the user to confirm. Do not stall asking which files are new when the log is empty.

**Step 2 — Decide how many to process**
If $ARGUMENTS is provided, process that many sources. Otherwise process 5–10, prioritising the most recently added files. If there is nothing new, say so and stop.

**Step 3 — For each source file, in order:**
1. Read the file carefully.
2. Write a `source-summary` page in `wiki/` that captures the key points, using the frontmatter format from CLAUDE.md.
3. Create or update `concept`, `project`, or `person` pages as appropriate — one idea per page, atomic.
4. Cross-link pages using `[[page-name]]` syntax. When you link to a page that does not exist yet, note it as a stub opportunity in the `## Open Questions` section but do not create empty placeholder files.
5. Update `wiki/index.md` — add any new pages to the correct section of the catalog.
6. Append a timestamped entry to `wiki/log.md` in this format:
   ```
   ## YYYY-MM-DD
   - Ingested `raw/<path>` → created `wiki/<path>`, updated `wiki/<path>`
   ```

**Voice and tone**
These pages are the future data source for the user's portfolio website, so they should read like the user actually wrote them, not like a generated summary.

Before writing any prose, read `wiki/meta/voice-profile.md`. That file is the living description of how the user writes, and it gets refined over time by the `/voice` command. Follow it as your style guide for every page you create or update. In particular, honour its "How to render this for the wiki and portfolio" section: keep the user's voice, rhythm, and honesty, but clean up quick-message shorthand for public pages.

If the voice profile does not exist yet, fall back to these defaults:

- First person. This is the user's own learning, so write "I figured out", "what tripped me up was", "the thing I keep forgetting is". Not "the user learned that".
- Direct and casual, the way a sharp student explains something to a friend who already knows the field. Contractions are good. Short sentences are good.
- Plain words over jargon. If a technical term is needed, use it, but don't pad the page with buzzwords.
- No em dashes anywhere. Use a comma, a full stop, or a new sentence instead.
- Go very light on bold. If a page has more than two or three bold spans, that is too many.
- No filler openers like "In today's fast-paced world" or "It is important to note that". Start with the actual point.
- Keep the honesty. If something was confusing, say it was confusing.

The structured frontmatter and headings still apply. It is the prose inside that should sound human and natural.

**Keep the voice profile fresh**
If this run ingested a meaningful amount of the user's own first-party writing (their messages in chat exports, or their notes), suggest at the end that the user run `/voice` to recalibrate the voice profile with the new samples. Do not update the profile yourself here. That is the `/voice` command's job.

**Constraints**
- Never modify, rename, or delete anything in `raw/`.
- Every wiki page must have complete frontmatter (title, type, sources, related, created, last-updated).
- Attribute every non-obvious claim to its source file.
- If two sources contradict each other, flag it explicitly. Do not silently pick one side.
