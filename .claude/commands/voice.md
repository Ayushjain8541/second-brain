---
description: Refine the voice profile from my own writing.
argument-hint: (optional) number of source files to learn from this run
---

You are refining `wiki/meta/voice-profile.md`, the living description of how the user writes. The goal is for the voice profile to get sharper over time as more of the user's real writing comes in, so that `/ingest` can make wiki pages sound like the user.

**Step 1 — Read the current profile**
Read `wiki/meta/voice-profile.md`. This is what we believe about the user's voice so far. You are refining it, not starting over. Note the current `samples-seen` count and `confidence` level.

**Step 2 — Gather first-party writing only**
This is the most important rule. Only the user's own words count as voice signal. Collect:
- The user's own messages from chat exports in `raw/claude-exports/`, `raw/chatgpt-exports/`, `raw/gemini-exports/`. In a conversation export, use only the user/human turns. Ignore the assistant's replies entirely.
- The user's notes in `raw/notes/`.
- The user's own spoken lines in `raw/fathom/` transcripts, but treat these as lower weight since speaking is not writing.

Do NOT learn voice from `raw/articles/`, `raw/pdfs/`, or `raw/youtube-transcripts/`. Those are other people's words. Pulling style from them would corrupt the profile.

If $ARGUMENTS is a number, limit to that many source files this run. Otherwise sample broadly across the available first-party sources.

**Step 3 — Observe, do not invent**
From the real samples, look for concrete, evidence-backed patterns:
- Sentence length and rhythm. Short and clipped, or long and flowing?
- Punctuation habits. Em dashes, commas, parentheses, capitalisation, apostrophes.
- Recurring words, phrases, and sentence openers.
- Tone. Casual or formal, direct or hedged, opinionated or neutral.
- Vocabulary specific to the user's world (their field, tools, projects).

Pull a few short real quotes as evidence. Never fabricate a pattern you cannot point to in an actual sample.

**Step 4 — Merge into the profile**
Update `wiki/meta/voice-profile.md`:
- Confirm patterns that the new samples support. Correct or remove patterns the new evidence contradicts.
- Add genuinely new patterns. Refresh the real-quote examples with better ones if you find them.
- Keep the "How to render this for the wiki and portfolio" section intact. That is the user's standing rule: keep the voice, clean up quick-message shorthand for public pages.
- Update the frontmatter: bump `samples-seen` by the number of new first-party sources used, raise `confidence` (low to medium to high) as the evidence base grows and patterns stabilise, and set `last-updated` to today.
- Add a dated line to the `## Calibration log` saying what changed and why.

**Step 5 — Report**
Summarise what you learned this run, what changed in the profile, and the new confidence level. If the profile barely moved, say so. That is fine and means the voice is stabilising.

**Constraints**
- Never modify, rename, or delete anything in `raw/`.
- No em dashes in the profile itself.
- Be honest about confidence. A profile built from three messages should not claim high confidence.
