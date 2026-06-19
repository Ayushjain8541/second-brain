---
description: Append a timestamped note to wiki/log.md.
argument-hint: the thought or note to capture
---

You are capturing a quick note into the wiki log. The note is:

$ARGUMENTS

**Step 1 — Append to log**
Open `wiki/log.md` and append an entry at the bottom in this format:

```
## YYYY-MM-DD
- Note: <the note text>
```

Use today's date. Never edit any existing entries — this log is append-only.

**Step 2 — Check for page references**
Re-read the note and identify whether it mentions:
- A **project** that has a page in `wiki/projects/`
- A **person** that has a page in `wiki/people/`
- A **concept** that has a page in `wiki/concepts/`

If a matching page exists, update it — add the note content under the most relevant section, update `last-updated` in its frontmatter, and cross-link back to related pages where appropriate.

**Step 3 — Do not create new pages**
If the note mentions something that does not yet have a wiki page, do not create one. Note it as a stub opportunity on the same log entry line:
```
- Note: ... (stub opportunity: [[new-topic]])
```
