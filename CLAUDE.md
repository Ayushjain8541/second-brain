# Second Brain — Claude Instructions

## 1. Project Structure

This vault has two ownership zones:

- **`raw/`** — source documents owned by the user. Never modify, rename, or delete anything here. Treat it as read-only input.
- **`wiki/`** — knowledge pages owned by Claude. Create, update, and cross-link pages here based on what you find in `raw/`.
- **`journal/`** — daily notes (Part 2, not yet active).
- **`content/`** — content pipeline (Part 2, not yet active).

### raw/ subfolders

| Folder | Contents |
|--------|----------|
| `claude-exports/` | Conversation exports from Claude |
| `chatgpt-exports/` | Conversation exports from ChatGPT |
| `gemini-exports/` | Conversation exports from Gemini |
| `notion-exports/` | Page and database exports from Notion |
| `notes/` | Freeform notes from any source |
| `articles/` | Saved articles, essays, newsletters |
| `fathom/` | Meeting transcripts and summaries from Fathom |
| `youtube-transcripts/` | Transcripts from YouTube videos |
| `pdfs/` | Books, papers, reports |
| `nusmods/` | Official NUS module info, auto-fetched from NUSMods by `fetch_modules.py`. Not hand-filled. |

### wiki/ structure

| Path | Purpose |
|------|---------|
| `wiki/index.md` | Master catalog of every wiki page. Update it whenever a page is created or significantly changed. |
| `wiki/log.md` | Append-only activity log. Add an entry for every wiki action taken (create, update, delete). Never edit past entries. |
| `wiki/concepts/` | Concept and topic pages — ideas, frameworks, mental models |
| `wiki/projects/` | Project pages — goals, decisions, status, open questions |
| `wiki/people/` | People dossiers — who they are, shared context, relationship history |
| `wiki/meta/` | System pages about the vault itself. Currently holds `voice-profile.md`. |

### The voice profile

`wiki/meta/voice-profile.md` is a living description of how the user writes. The wiki is the future data source for the user's portfolio site, so pages should sound like the user, not like generated summaries. Two commands keep this working:

- `/voice` refines the profile from the user's own first-party writing (their turns in chat exports, and their notes). It ignores articles, PDFs, YouTube transcripts, and the assistant's half of conversations, since those are not the user's voice.
- `/ingest` reads the profile before writing any prose and follows it as the style guide.

The profile separates the user's raw quick-message habits (lowercase "i", dropped apostrophes) from how pages should render in public (keep the voice and rhythm, clean up the shorthand).

### NUS modules

The user is an NUS student, and module learnings should flow into the wiki automatically. The flow has two deterministic stages plus synthesis:

1. The user maintains `my-modules.md` at the vault root (one module code per line, outside `raw/` so `/ingest` skips it).
2. `fetch_modules.py` reads that list and pulls each module's official info from the NUSMods API into `raw/nusmods/<CODE>.md`.
3. `/module` turns each into a `project`-type hub page in `wiki/projects/`: the official NUSMods scaffold (neutral, attributed) plus a "What I Learned" section that links out to the atomic concept pages `/ingest` builds from the user's notes. It does not duplicate concept content; shared concepts stay single pages.

---

## 2. Page Conventions

### Frontmatter

Every wiki page must open with YAML frontmatter containing these exact fields:

```yaml
---
title: "Page Title"
type: concept          # one of: concept | entity | source-summary | comparison | project | person | meta
sources:
  - raw/articles/2026-06-19-example.md
related:
  - "[[other-page]]"
created: 2026-06-19
last-updated: 2026-06-19
---
```

- `type` must be exactly one of the seven values above — no other values. `meta` is reserved for system pages like the voice profile.
- `sources` lists the raw/ files this page was synthesized from. Always populate it; never leave it empty. `meta` pages may instead note where their content came from in parentheses.
- `related` lists wiki-link references to related pages.
- Update `last-updated` every time the page content changes.

### Wiki links

Use `[[page-name]]` syntax to link between wiki pages. The link target should match the filename without the `.md` extension. When you create a link to a page that doesn't exist yet, note it as a stub opportunity but do not create empty placeholder files.

### Atomicity

One idea per page. If a page is covering two distinct concepts, split it. A page should answer one question clearly, not be an exhaustive dump of everything related to a topic.

### Heading structure

```
# Title                  ← matches the frontmatter title field
## Summary               ← 2-4 sentences, the core claim of this page
## Detail                ← supporting content, broken into subsections as needed
## Connections           ← explicit links to related pages with a one-line reason
## Open Questions        ← unresolved threads, contradictions, things to investigate
## Sources               ← prose attribution — which raw file said what
```

Not every section is required on every page, but `# Title`, `## Summary`, and `## Sources` are mandatory.

---

## 3. Style Guide

- **Prose:** Clear and concise. Write for someone who knows the domain but is reading cold. Avoid filler phrases ("it is important to note that…").
- **Structure:** Prefer bullet points over dense paragraphs for lists of facts, attributes, or steps. Use paragraphs for explanations and arguments.
- **Attribution:** Every non-obvious claim must trace back to a source. Use inline attribution ("per the Fathom transcript from 2026-06-15…") or the `## Sources` section.
- **Contradictions:** If two sources disagree, say so explicitly. Do not silently resolve contradictions by picking one side. Flag them: "Source A says X; Source B says Y — unresolved."
- **Tone:** Neutral and factual. Do not editorialize unless the user explicitly asked for analysis.
- **Dates:** Always ISO 8601 (`YYYY-MM-DD`).
- **Filenames:** Lowercase, hyphen-separated, no spaces. Match the page title closely (`mental-models-for-prioritization.md`).

---

## 4. Domain Context

The user is a Computer Science student at NUS building toward a career as a forward-deployed engineer or AI engineer. The vault will accumulate knowledge across two parallel tracks: software engineering with an emphasis on systems architecture, and applied AI. Day-to-day material includes university modules (CS and math), notes on professors and academic content, learnings from CCAs, side projects built for resume and skill development, and internship experiences. When synthesizing wiki pages, treat NUS modules and professors as `project` and `person` pages respectively, and bias concept pages toward practical, applied understanding over pure theory. Contradictions between academic teaching and real-world practice encountered in internships or projects are worth flagging explicitly — they are signal, not noise.
