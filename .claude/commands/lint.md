---
description: Run a health check on the wiki.
---

You are running a structural health check on the wiki. Do not fix anything — report only, then ask for permission before making any changes.

**Check 1 — Broken wiki-links**
Scan every `.md` file in `wiki/` for `[[link]]` references. For each one, verify that a file with that name exists in `wiki/`. List every broken link with the file it appears in.

**Check 2 — Orphan pages**
Find every wiki page that is not linked to from any other wiki page and is not listed in `wiki/index.md`. These are orphans.

**Check 3 — Missing or incomplete frontmatter**
Every wiki page must have all six frontmatter fields: `title`, `type`, `sources`, `related`, `created`, `last-updated`. List every page that is missing any field, or where `type` is not one of the seven valid values (concept, entity, source-summary, comparison, project, person, meta), or where `sources` is empty. Note: `meta` pages such as `wiki/meta/voice-profile.md` may carry a parenthetical source note instead of a raw/ file path, so do not flag those for an empty `sources`.

**Check 4 — Stale pages**
List every wiki page whose `last-updated` date is 30 or more days before today (2026-06-19).

**Check 5 — Contradictions**
Scan for pages that make conflicting claims about the same topic. Flag any you find with the specific conflicting statements.

**Output format**
Report findings as a structured list grouped by check:

```
## Check 1 — Broken wiki-links
- None found  /  - `wiki/foo.md` links to [[bar]] which does not exist

## Check 2 — Orphan pages
...
```

End with a one-line summary of total issues found, then ask whether to proceed with fixes and which categories to address first.
