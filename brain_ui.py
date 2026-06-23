import os
import sys
import json
import re
import glob
import base64
import time
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import urllib.parse

# g4f is only needed for the AI-powered /run endpoint. Import it lazily so the
# dashboard, file explorer, and editor all work even if g4f isn't installed.
# We pin a specific no-auth provider (PollinationsAI) because g4f's default
# RetryProvider chain routes to providers that now demand API keys or cookies.
# Ordered fallback chain of no-auth providers, verified to respond without
# API keys or cookies. The first one serves the dropdown models; if it's down,
# we fall through to the next using that provider's own default model.
# The list lives in providers.json (written by probe_providers.py) so it can be
# refreshed without editing code; this is the built-in default if that's absent.
DEFAULT_PROVIDER_NAMES = ["PollinationsAI", "Yqcloud", "WeWordle", "OperaAria", "Felo"]
PROVIDERS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "providers.json")

def load_provider_names():
    """Read the provider order from providers.json, falling back to defaults."""
    try:
        with open(PROVIDERS_JSON, encoding="utf-8") as f:
            names = json.load(f).get("providers")
        if isinstance(names, list) and names:
            return names
    except Exception:
        pass
    return DEFAULT_PROVIDER_NAMES

try:
    # pyrefly: ignore [missing-import]
    from g4f.client import Client
    # pyrefly: ignore [missing-import]
    import g4f.Provider as _g4f_providers
    G4F_AVAILABLE = True
except ImportError:
    Client = None
    _g4f_providers = None
    G4F_AVAILABLE = False

PROVIDER_NAMES = []
PROVIDER_CHAIN = []
DEFAULT_PROVIDER = None

def rebuild_provider_chain():
    """(Re)build the provider chain from providers.json. Safe to call anytime;
    a background refresh calls this after re-probing so changes take effect
    without a restart."""
    global PROVIDER_NAMES, PROVIDER_CHAIN, DEFAULT_PROVIDER
    if not G4F_AVAILABLE:
        return
    PROVIDER_NAMES = load_provider_names()
    PROVIDER_CHAIN = [
        (name, getattr(_g4f_providers, name))
        for name in PROVIDER_NAMES if hasattr(_g4f_providers, name)
    ]
    DEFAULT_PROVIDER = PROVIDER_CHAIN[0][1] if PROVIDER_CHAIN else None

rebuild_provider_chain()

# PORT where the dashboard will be hosted
PORT = 5080

# DEFAULT SKILL DEFINITIONS
# These will be automatically generated in your vault if missing
DEFAULT_COMMANDS = {
    "ingest": {
        "description": "Ingest new files from raw/ into wiki/.",
        "hint": "optional limit (e.g. 5)",
        "prompt": """---
description: Ingest new files from raw/ into wiki/.
argument-hint: (optional) number of sources to process this run
---

You are ingesting new source files from `raw/` into the wiki. Follow the rules in CLAUDE.md exactly.

**Step 1 — Discover unread sources**
Scan all subfolders of `raw/` for files. Cross-reference `wiki/log.md` to identify which files have already been ingested (they will have a log entry). Build a list of files that have not yet been processed.

If `wiki/log.md` has no ingest entries (only its header), treat this as the first run: assume every file in `raw/` is new and proceed without asking the user to confirm. Do not stall asking which files are new when the log is empty.

**Step 2 — Decide how many to process**
If $ARGUMENTS is provided, process that many sources. Otherwise process 5-10, prioritising the most recently added files. If there is nothing new, say so and stop.

**Step 3 — For each source file, in order:**
1. Read the file carefully.
2. Write a `source-summary` page in `wiki/` that captures the key points, using the frontmatter format from CLAUDE.md.
3. Create or update `concept`, `project`, or `person` pages as appropriate — one idea per page, atomic.
4. Cross-link pages using `[[page-name]]` syntax. When you link to a page that does not exist yet, note it as a stub opportunity in the `## Open Questions` section but do not create empty placeholder files.
5. Update `wiki/index.md` — add any new pages to the correct section of the catalog.
6. Append a timestamped entry to `wiki/log.md` in this format:
   ```
   ## YYYY-MM-DD
   - Ingested `raw/<path>` -> created `wiki/<path>`, updated `wiki/<path>`
   ```

**Voice and tone**
These pages are the future data source for the user's portfolio website, so they should read like the user actually wrote them, not like a generated summary.

Before writing any prose, read `wiki/meta/voice-profile.md`. That file is the living description of how the user writes, refined over time by the `/voice` command. Follow it as your style guide for every page. Honour its "How to render this for the wiki and portfolio" section: keep the user's voice, rhythm, and honesty, but clean up quick-message shorthand for public pages.

If the voice profile does not exist yet, fall back to these defaults:

- First person. This is the user's own learning, so write "I figured out", "what tripped me up was". Not "the user learned that".
- Direct and casual, the way a sharp student explains something to a friend who already knows the field. Contractions are good. Short sentences are good.
- Plain words over jargon. Don't pad the page with buzzwords.
- No em dashes anywhere. Use a comma, a full stop, or a new sentence instead.
- Go very light on bold. If a page has more than two or three bold spans, that is too many.
- No filler openers. Start with the actual point.
- Keep the honesty. If something was confusing, say it was confusing.

The structured frontmatter and headings still apply. It is the prose inside that should sound human and natural. If this run ingested a meaningful amount of the user's own first-party writing, suggest at the end that they run /voice to recalibrate the voice profile.

**Constraints**
- Never modify, rename, or delete anything in `raw/`.
- Every wiki page must have complete frontmatter (title, type, sources, related, created, last-updated).
- Attribute every non-obvious claim to its source file.
- If two sources contradict each other, flag it explicitly. Do not silently pick one side."""
    },
    "query": {
        "description": "Synthesise an answer from the wiki.",
        "hint": "the question to answer",
        "prompt": """---
description: Synthesise an answer from the wiki.
argument-hint: the question to answer
---

You are answering a question using only what is in the wiki. The question is:

$ARGUMENTS

**Step 1 — Orient**
Read `wiki/index.md` to get a map of all available pages.

**Step 2 — Gather relevant pages**
Identify and read every wiki page that is likely relevant to the question. When in doubt, read it — a broader read is better than a missed source.

**Step 3 — Synthesise**
Write a clear, direct answer grounded in what the wiki actually says. For every claim you make:
- Cite the wiki page it comes from, e.g. "(-> [[page-name]])"
- If two pages disagree on a point, state both positions explicitly and flag the contradiction rather than silently resolving it.

**Step 4 — Flag gaps**
If the wiki does not have enough information to answer the question fully, say so clearly. Identify which raw sources might fill the gap if they were ingested.

**Step 5 — Propose updates (do not write them)**
If answering revealed a connection between pages that is not yet cross-linked, or a concept that deserves its own page, propose the update in a `## Proposed Wiki Updates` section at the end. Do not create or modify any wiki pages without explicit confirmation."""
    },
    "lint": {
        "description": "Run a health check on the wiki.",
        "hint": "none",
        "prompt": """---
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
List every wiki page whose `last-updated` date is 30 or more days before today.

**Check 5 — Contradictions**
Scan for pages that make conflicting claims about the same topic. Flag any you find with the specific conflicting statements.

**Output format**
Report findings as a structured list grouped by check. End with a one-line summary of total issues found, then ask whether to proceed with fixes and which categories to address first."""
    },
    "log": {
        "description": "Append a timestamped note to wiki/log.md.",
        "hint": "the thought or note to capture",
        "prompt": """---
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
Re-read the note and identify whether it mentions a project, person, or concept that has a page in `wiki/`. If a matching page exists, update it — add the note content under the most relevant section, update `last-updated` in its frontmatter, and cross-link back to related pages where appropriate.

**Step 3 — Do not create new pages**
If the note mentions something that does not yet have a wiki page, do not create one. Note it as a stub opportunity on the same log entry line:
```
- Note: ... (stub opportunity: [[new-topic]])
```"""
    },
    "module": {
        "description": "Build wiki project pages for my NUS modules.",
        "hint": "optional module code (e.g. CS2103T)",
        "prompt": """---
description: Build wiki project pages for my NUS modules.
argument-hint: (optional) a specific module code, e.g. CS2103T
---

You are building or updating wiki pages for the user's NUS modules. Each module page is a `project`-type hub: it pairs the official NUSMods scaffold with links to the user's own learnings. Follow CLAUDE.md exactly.

**Step 1 — Find the module data**
Look in `raw/nusmods/` for module files (e.g. `raw/nusmods/CS2103T.md`), the official NUSMods exports written by fetch_modules.py. If $ARGUMENTS names a specific module code, only process that one. Otherwise process every module file in `raw/nusmods/`.

If `raw/nusmods/` is empty, stop and tell the user to add codes to `my-modules.md` and run `./env/bin/python fetch_modules.py` first. Do not invent module data.

**Step 2 — For each module, build the hub page**
Write to `wiki/projects/<code>-<slug>.md` with frontmatter (title, type: project, sources include the raw/nusmods file, related, created, last-updated) and these sections:
- `## Summary` — one or two lines on what the module is, in the user's voice.
- `## Official Overview` — the factual scaffold from NUSMods (aims, topics, workload, prerequisites). Neutral and attributed to NUSMods. Do not restyle it as the user's words.
- `## What I Learned` — a hub, not a dump. Link to the atomic concept pages from the user's notes, each with a one-line note on how it connects to this module. If there are no learnings on file yet, say so and leave a stub.
- `## Open Questions` — gaps and things that confused the user.
- `## Sources` — prose attribution: the NUSMods file plus any notes that fed the learnings.

**Step 3 — Link, don't duplicate**
To fill "What I Learned", scan `wiki/concepts/` and `wiki/source-summaries/` for pages whose topics match this module's syllabus, and link them with `[[page-name]]`. Never copy concept content into the module page. If a relevant concept should exist but doesn't, note it as a stub opportunity in Open Questions.

**Step 4 — Voice**
Read `wiki/meta/voice-profile.md` first. Summary, What I Learned, and Open Questions are the user's own words, so follow the profile (first person, no em dashes, light on bold). The Official Overview is NUSMods' words, so keep it factual and attributed.

**Step 5 — Update catalog and log**
Add each new page to the Projects section of `wiki/index.md`, and append a timestamped entry to `wiki/log.md`.

**Constraints**
- Never modify anything in `raw/`.
- Every page needs complete frontmatter (type: project).
- Attribute official content to NUSMods; attribute learnings to the user's notes."""
    },
    "voice": {
        "description": "Refine the voice profile from my own writing.",
        "hint": "optional file count (e.g. 10)",
        "prompt": """---
description: Refine the voice profile from my own writing.
argument-hint: (optional) number of source files to learn from this run
---

You are refining `wiki/meta/voice-profile.md`, the living description of how the user writes. The goal is for it to get sharper over time as more of the user's real writing comes in, so `/ingest` can make wiki pages sound like the user.

**Step 1 — Read the current profile**
Read `wiki/meta/voice-profile.md`. You are refining it, not starting over. Note the current `samples-seen` count and `confidence` level.

**Step 2 — Gather first-party writing only**
Only the user's own words count as voice signal. Collect:
- The user's own messages from `raw/claude-exports/`, `raw/chatgpt-exports/`, `raw/gemini-exports/`. Use only the user/human turns. Ignore the assistant's replies entirely.
- The user's notes in `raw/notes/`.
- The user's own spoken lines in `raw/fathom/`, weighted lower since speaking is not writing.

Do NOT learn voice from `raw/articles/`, `raw/pdfs/`, or `raw/youtube-transcripts/`. Those are other people's words and would corrupt the profile.

If $ARGUMENTS is a number, limit to that many source files this run.

**Step 3 — Observe, do not invent**
Look for concrete, evidence-backed patterns: sentence length and rhythm, punctuation habits, recurring words and openers, tone, and field-specific vocabulary. Pull a few short real quotes as evidence. Never fabricate a pattern you cannot point to in a real sample.

**Step 4 — Merge into the profile**
Update `wiki/meta/voice-profile.md`. Confirm patterns the new samples support, correct ones they contradict, add genuinely new patterns, and refresh the example quotes. Keep the "How to render this for the wiki and portfolio" section intact. Update the frontmatter: bump `samples-seen`, raise `confidence` as the evidence base grows, set `last-updated` to today, and add a dated line to the `## Calibration log`.

**Step 5 — Report**
Summarise what you learned, what changed, and the new confidence level. If the profile barely moved, say so. That means the voice is stabilising.

**Constraints**
- Never modify, rename, or delete anything in `raw/`.
- No em dashes in the profile itself.
- Be honest about confidence."""
    }
}

def initialize_vault():
    """Ensures necessary directories and boilerplate files exist."""
    folders = ["raw", "wiki", ".claude/commands"]
    for f in folders:
        os.makedirs(f, exist_ok=True)
        
    # Generate default CLAUDE.md if not existing
    if not os.path.exists("CLAUDE.md"):
        with open("CLAUDE.md", "w", encoding="utf-8") as f:
            f.write("# Second Brain System Rules\nKeep pages cleanly formatted using standard markdown. Cross-reference related files using Obsidian-style double brackets `[[wiki-link]]`.\n")
            
    # Generate default wiki/index.md if not existing
    if not os.path.exists("wiki/index.md"):
        with open("wiki/index.md", "w", encoding="utf-8") as f:
            f.write("# Wiki Index\nWelcome to your Second Brain. Use /ingest to import raw logs.\n\n## Content Map\n- [[log]]\n")

    # Generate default wiki/log.md if not existing
    if not os.path.exists("wiki/log.md"):
        with open("wiki/log.md", "w", encoding="utf-8") as f:
            f.write("# Activity Log\n*Vault initialized.*")

    # Generate default commands
    for name, cmd in DEFAULT_COMMANDS.items():
        cmd_path = f".claude/commands/{name}.md"
        if not os.path.exists(cmd_path):
            with open(cmd_path, "w", encoding="utf-8") as f:
                f.write(cmd["prompt"])

VAULT_ROOT = os.path.abspath(".")

# Recognised raw/ subfolders, used to populate the upload destination picker.
RAW_SUBFOLDERS = [
    "claude-exports", "chatgpt-exports", "gemini-exports", "notion-exports",
    "notes", "articles", "fathom", "youtube-transcripts", "pdfs", "nusmods",
]

def safe_vault_path(path):
    """Resolve a path and confirm it stays inside the vault root.
    Returns the absolute path, or None if it escapes the boundary."""
    if not path:
        return None
    candidate = os.path.abspath(os.path.join(VAULT_ROOT, path))
    # Must be the vault root itself or live underneath it
    if candidate == VAULT_ROOT or candidate.startswith(VAULT_ROOT + os.sep):
        return candidate
    return None

def read_file(path):
    try:
        safe_path = safe_vault_path(path)
        if safe_path is None:
            return "Error reading file: path outside vault boundaries."
        if os.path.exists(safe_path) and os.path.isfile(safe_path):
            with open(safe_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
    return ""

def write_file(path, content):
    try:
        # Sanitize paths to prevent directory traversal
        safe_path = safe_vault_path(path)
        if safe_path is None:
            return False, "Security Block: File path outside vault boundaries."

        parent = os.path.dirname(safe_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        rel_path = os.path.relpath(safe_path, VAULT_ROOT)
        return True, f"Successfully wrote {rel_path}"
    except Exception as e:
        return False, str(e)

def safe_filename(name):
    """Reduce an uploaded filename to a single safe basename — no directory
    parts, no leading dots, only sensible characters."""
    name = os.path.basename((name or "").strip().replace("\\", "/"))
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(". ")
    return name

def write_binary_file(path, data_bytes):
    try:
        safe_path = safe_vault_path(path)
        if safe_path is None:
            return False, "Security Block: File path outside vault boundaries."
        parent = os.path.dirname(safe_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(safe_path, "wb") as f:
            f.write(data_bytes)
        rel_path = os.path.relpath(safe_path, VAULT_ROOT)
        return True, rel_path
    except Exception as e:
        return False, str(e)

def unique_path(rel_path):
    """If rel_path already exists in the vault, append -1, -2, ... before the
    extension so uploads never silently overwrite existing sources."""
    safe_path = safe_vault_path(rel_path)
    if safe_path is None or not os.path.exists(safe_path):
        return rel_path
    base, ext = os.path.splitext(rel_path)
    i = 1
    while True:
        candidate = f"{base}-{i}{ext}"
        if not os.path.exists(safe_vault_path(candidate)):
            return candidate
        i += 1

class BrainAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress automatic console printing of GET/POST requests to keep dashboard output clean
        pass

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Serve Frontend Dashboard
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_UI.encode('utf-8'))
            return

        # Fetch entire Vault directory and list commands
        elif path == '/api/vault':
            vault_structure = {
                "raw": [],
                "wiki": [],
                "commands": [],
                "raw_subfolders": RAW_SUBFOLDERS
            }
            # List raw files
            for root, _, files in os.walk("raw"):
                for file in files:
                    vault_structure["raw"].append(os.path.join(root, file).replace("\\", "/"))
            
            # List wiki files
            for root, _, files in os.walk("wiki"):
                for file in files:
                    vault_structure["wiki"].append(os.path.join(root, file).replace("\\", "/"))
                    
            # List slash command configurations
            for root, _, files in os.walk(".claude/commands"):
                for file in files:
                    if file.endswith(".md"):
                        vault_structure["commands"].append(file[:-3])
                        
            self.send_json(vault_structure)
            return

        # Read specific file endpoint
        elif path == '/api/file':
            filepath = query.get('path', [None])[0]
            if not filepath:
                self.send_json({"error": "No file path provided"}, 400)
                return
            
            content = read_file(filepath)
            self.send_json({"path": filepath, "content": content})
            return

        # 404 handler
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data.decode('utf-8'))
        except Exception:
            self.send_json({"error": "Invalid JSON"}, 400)
            return

        # Save/Write file from internal editor
        if path == '/api/save':
            filepath = body.get('path')
            content = body.get('content')
            if not filepath or content is None:
                self.send_json({"error": "Missing path or content"}, 400)
                return
            
            success, msg = write_file(filepath, content)
            if success:
                self.send_json({"message": msg})
            else:
                self.send_json({"error": msg}, 400)
            return

        # Execute a command Skill utilizing gpt4free
        elif path == '/api/run':
            command_name = body.get('command')
            arguments = body.get('arguments', '')
            model_selected = body.get('model', 'openai')

            if not G4F_AVAILABLE:
                self.send_json({
                    "error": "g4f is not installed. Run `pip install -U g4f` to enable AI commands.",
                    "logs": ["🚨 g4f module not found — AI commands are disabled."],
                    "output": "Install g4f to run commands: pip install -U g4f"
                }, 503)
                return

            command_file = f".claude/commands/{command_name}.md"
            if not os.path.exists(command_file):
                self.send_json({"error": f"Command /{command_name} not found"}, 404)
                return

            # Read guidelines & target command
            system_rules = read_file("CLAUDE.md")
            command_prompt = read_file(command_file)

            # Substitute input arguments in prompt
            command_prompt = command_prompt.replace("$ARGUMENTS", arguments)

            # Package directory contents directly as system context for the model
            local_logs = []
            local_logs.append(f"📦 Assembling vault directory contexts...")
            vault_context = "### CURRENT VAULT ARCHIVE ###\n"
            
            # Loop recursively in raw and wiki to form contextual environment
            for filepath in glob.glob("raw/**/*", recursive=True) + glob.glob("wiki/**/*", recursive=True):
                if os.path.isfile(filepath):
                    file_body = read_file(filepath)
                    vault_context += f"\n--- FILE: {filepath} ---\n{file_body}\n"
            
            full_user_prompt = f"{vault_context}\n\n### TASK INSTRUCTIONS ###\n{command_prompt}"
            if arguments:
                full_user_prompt += f"\n\nActive arguments provided by controller: {arguments}"

            system_message = (
                f"{system_rules}\n\nYou are an automated workspace assistant. Return your outputs using standard markdown. "
                f"If you need to write, create, update, or edit files in the vault, you MUST wrap the complete, full content of each modified file inside a codeblock clearly labeled with 'write:filepath' like this:\n"
                f"```write:wiki/filename.md\n"
                f"[complete file content goes here]\n"
                f"```\n"
                f"Do NOT output partial files or diffs; write the full file contents. Avoid using placeholders inside file blocks."
            )
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": full_user_prompt},
            ]

            # Try each no-auth provider in order. The first uses the selected
            # model; if a provider is down we fall through to the next, which
            # uses its own default model. This survives any single provider
            # going offline.
            ai_output = None
            used_provider = None
            last_error = None
            for idx, (pname, prov) in enumerate(PROVIDER_CHAIN):
                model_to_use = model_selected if idx == 0 else (getattr(prov, "default_model", None) or model_selected)
                local_logs.append(f"🧠 Trying {pname} (model '{model_to_use}')...")
                try:
                    client = Client(provider=prov)
                    response = client.chat.completions.create(model=model_to_use, messages=messages, timeout=120)
                    ai_output = response.choices[0].message.content
                    if not ai_output or not ai_output.strip():
                        raise ValueError("empty response")
                    used_provider = pname
                    local_logs.append(f"⚡ {pname} responded. Analyzing for file edits...")
                    break
                except Exception as e:
                    last_error = e
                    local_logs.append(f"⚠️ {pname} failed ({type(e).__name__}). Trying next provider...")
                    continue

            if ai_output is None:
                local_logs.append(f"🚨 All {len(PROVIDER_CHAIN)} providers failed. Last error: {last_error}")
                self.send_json({
                    "error": f"All providers failed. Last error: {last_error}",
                    "logs": local_logs,
                    "output": "Execution aborted: every g4f provider in the fallback chain is unreachable right now. Try again shortly."
                }, 502)
                return

            # Apply any file writes the model requested
            written_files = []
            file_blocks = re.findall(r"```write:(.*?)\n(.*?)```", ai_output, re.DOTALL)
            for path_str, file_content in file_blocks:
                dest_path = path_str.strip()
                file_content_clean = file_content.strip()
                local_logs.append(f"✍️ AI requested change to: {dest_path}")
                ok, msg = write_file(dest_path, file_content_clean)
                if ok:
                    written_files.append(dest_path)
                    local_logs.append(f"✔️ Saved update: {dest_path}")
                else:
                    local_logs.append(f"❌ Failed to write {dest_path}: {msg}")

            self.send_json({
                "output": ai_output,
                "logs": local_logs,
                "changed": written_files,
                "provider": used_provider
            })
            return

        # Upload one or more files straight into a raw/ subfolder
        elif path == '/api/upload':
            folder = body.get('folder', '')
            files = body.get('files', [])

            if folder not in RAW_SUBFOLDERS:
                self.send_json({"error": f"Unknown destination folder: {folder}"}, 400)
                return
            if not files:
                self.send_json({"error": "No files provided"}, 400)
                return

            saved, failed = [], []
            for item in files:
                raw_name = item.get('name', '')
                data_field = item.get('data', '')
                clean_name = safe_filename(raw_name)
                if not clean_name:
                    failed.append({"name": raw_name, "reason": "invalid filename"})
                    continue
                # data may be a bare base64 string or a data: URL — strip any prefix
                if ',' in data_field and data_field.strip().startswith('data:'):
                    data_field = data_field.split(',', 1)[1]
                try:
                    file_bytes = base64.b64decode(data_field)
                except Exception:
                    failed.append({"name": clean_name, "reason": "could not decode file data"})
                    continue

                dest = unique_path(f"raw/{folder}/{clean_name}")
                ok, result = write_binary_file(dest, file_bytes)
                if ok:
                    saved.append(result)
                else:
                    failed.append({"name": clean_name, "reason": result})

            self.send_json({"saved": saved, "failed": failed})
            return

        self.send_response(404)
        self.end_headers()

HTML_UI = """<!DOCTYPE html>
<html lang="en" class="h-full bg-slate-950 text-slate-100">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Second Brain Dashboard</title>
    <!-- Tailwind -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <!-- Marked Markdown -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        .custom-scroll::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        .custom-scroll::-webkit-scrollbar-track {
            background: #020617;
        }
        .custom-scroll::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 4px;
        }
        .custom-scroll::-webkit-scrollbar-thumb:hover {
            background: #475569;
        }
        /* Custom markdown styling to look clean in dark mode */
        .markdown-output h1 { font-size: 1.5rem; font-weight: bold; margin-top: 1.25rem; margin-bottom: 0.5rem; color: #f8fafc; border-bottom: 1px solid #334155; padding-bottom: 0.25rem; }
        .markdown-output h2 { font-size: 1.25rem; font-weight: bold; margin-top: 1rem; margin-bottom: 0.5rem; color: #f1f5f9; }
        .markdown-output h3 { font-size: 1.1rem; font-weight: bold; margin-top: 0.75rem; margin-bottom: 0.25rem; color: #e2e8f0; }
        .markdown-output p { margin-bottom: 0.75rem; line-height: 1.6; color: #cbd5e1; }
        .markdown-output ul { list-style-type: disc; padding-left: 1.5rem; margin-bottom: 0.75rem; }
        .markdown-output ol { list-style-type: decimal; padding-left: 1.5rem; margin-bottom: 0.75rem; }
        .markdown-output li { margin-bottom: 0.25rem; }
        .markdown-output code { background-color: #1e293b; padding: 0.125rem 0.25rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.9em; color: #f43f5e; }
        .markdown-output pre { background-color: #0f172a; padding: 0.75rem; border-radius: 0.5rem; overflow-x: auto; margin-bottom: 1rem; border: 1px solid #1e293b; }
        .markdown-output pre code { background-color: transparent; padding: 0; color: #e2e8f0; }
        .markdown-output a { color: #38bdf8; text-decoration: underline; }
        .markdown-output a:hover { color: #7dd3fc; }
        .markdown-output blockquote { border-left: 4px solid #3b82f6; padding-left: 1rem; color: #94a3b8; font-style: italic; margin-bottom: 0.75rem; }
    </style>
</head>
<body class="h-full flex flex-col font-sans overflow-hidden">

    <!-- Top Navigation Bar -->
    <header class="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between z-10 shrink-0">
        <div class="flex items-center gap-3">
            <div class="bg-indigo-600 text-white p-2 rounded-lg">
                <i data-lucide="brain" class="w-6 h-6"></i>
            </div>
            <div>
                <h1 class="text-lg font-bold tracking-tight">Second Brain Local UI</h1>
                <p class="text-xs text-slate-400">Powered by gpt4free & local filesystem integrations</p>
            </div>
        </div>
        <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse"></span>
                <span class="text-xs font-semibold text-slate-300">Local Engine Active</span>
            </div>
            <select id="modelSelector" class="bg-slate-800 border border-slate-700 text-xs text-slate-100 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500">
                <option value="openai" selected>OpenAI GPT (Default)</option>
                <option value="claude">Claude Sonnet</option>
                <option value="claude-large">Claude Opus</option>
                <option value="gemini">Gemini Flash</option>
                <option value="deepseek">DeepSeek</option>
                <option value="grok">Grok</option>
                <option value="llama">Llama</option>
            </select>
        </div>
    </header>

    <!-- Main Workspace Layout -->
    <main class="flex-1 flex overflow-hidden">
        
        <!-- Left Sidebar: Vault Navigator & Local Files -->
        <aside class="w-72 bg-slate-900/50 border-r border-slate-800 flex flex-col shrink-0">
            <!-- Header for explorer -->
            <div class="p-4 border-b border-slate-800 flex items-center justify-between">
                <span class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                    <i data-lucide="folder-open" class="w-4 h-4 text-indigo-400"></i> Vault Explorer
                </span>
                <button onclick="refreshVault()" class="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200 transition-colors" title="Reload Folders">
                    <i data-lucide="refresh-cw" class="w-4 h-4"></i>
                </button>
            </div>
            
            <!-- Vault Files Tree -->
            <div class="flex-1 overflow-y-auto p-4 custom-scroll space-y-4">

                <!-- Ingest drop zone: route uploads into a raw/ subfolder -->
                <div class="space-y-2">
                    <label class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                        <i data-lucide="download-cloud" class="w-3.5 h-3.5 text-indigo-400"></i> Add to raw/
                    </label>
                    <select id="upload-folder" class="w-full bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500">
                        <!-- options injected from /api/vault -->
                    </select>
                    <div id="drop-zone"
                         class="group relative border-2 border-dashed border-slate-700 hover:border-indigo-500/70 rounded-xl px-3 py-5 text-center cursor-pointer transition-all bg-slate-950/40 hover:bg-indigo-950/10">
                        <input type="file" id="upload-input" multiple class="hidden">
                        <div class="flex flex-col items-center gap-1.5 pointer-events-none">
                            <i data-lucide="upload-cloud" class="w-6 h-6 text-slate-500 group-hover:text-indigo-400 transition-colors"></i>
                            <p class="text-[11px] text-slate-400 leading-tight">
                                <span class="font-semibold text-slate-200">Drop files</span> or click to browse
                            </p>
                            <p class="text-[10px] text-slate-600" id="drop-target-label">→ raw/notes</p>
                        </div>
                    </div>
                    <div id="upload-progress" class="hidden text-[10px] text-slate-400 font-mono"></div>
                </div>

                <div class="border-t border-slate-800/60"></div>

                <!-- raw/ folder -->
                <div>
                    <h3 class="text-xs font-semibold text-slate-300 flex items-center gap-2 mb-2">
                        <i data-lucide="file-text" class="w-4 h-4 text-amber-500"></i> raw/ <span class="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.2 rounded-full font-normal" id="raw-count">0</span>
                    </h3>
                    <div id="raw-list" class="space-y-1 pl-4 border-l border-slate-800">
                        <p class="text-xs text-slate-500 italic">No raw sources found.</p>
                    </div>
                </div>

                <!-- wiki/ folder -->
                <div>
                    <h3 class="text-xs font-semibold text-slate-300 flex items-center gap-2 mb-2">
                        <i data-lucide="book-open" class="w-4 h-4 text-emerald-500"></i> wiki/ <span class="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.2 rounded-full font-normal" id="wiki-count">0</span>
                    </h3>
                    <div id="wiki-list" class="space-y-1 pl-4 border-l border-slate-800">
                        <p class="text-xs text-slate-500 italic">No wiki pages found.</p>
                    </div>
                </div>
            </div>

            <!-- Bottom utility settings -->
            <div class="p-4 border-t border-slate-800 bg-slate-900/80 space-y-2">
                <button onclick="openNewFileModal()" class="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 active:scale-98 text-white rounded-lg py-2 text-xs font-semibold shadow-md transition-all">
                    <i data-lucide="clipboard-paste" class="w-4 h-4"></i> Paste a Note
                </button>
            </div>
        </aside>

        <!-- Right Workspace: Interactive Command Hub & Live Editor -->
        <section class="flex-1 flex flex-col md:flex-row overflow-hidden">
            
            <!-- Mid-Panel: Interactive Slash Command Executor -->
            <div class="flex-1 flex flex-col border-r border-slate-800 overflow-hidden bg-slate-950">
                <!-- Tabs and Command selection -->
                <div class="p-4 border-b border-slate-800 flex flex-col gap-3 shrink-0">
                    <div class="flex items-center justify-between">
                        <h2 class="text-sm font-semibold text-slate-200 uppercase tracking-wide flex items-center gap-2">
                            <i data-lucide="terminal" class="w-4 h-4 text-indigo-400"></i> Action Control Console
                        </h2>
                        <span class="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-2 py-0.5 rounded-full" id="active-command-display">No Skill Selected</span>
                    </div>

                    <!-- Command Button Grid -->
                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-2">
                        <button onclick="selectCommand('ingest', 'Process unread raw files to create wiki summaries')" class="cmd-btn border border-slate-800 bg-slate-900/50 hover:bg-indigo-950/20 hover:border-indigo-500/50 p-3 rounded-lg text-left transition-all flex flex-col gap-1 focus:outline-none" id="btn-ingest">
                            <span class="text-xs font-bold text-indigo-400 flex items-center gap-1">
                                <span class="bg-indigo-950 text-indigo-400 px-1.5 py-0.5 rounded text-[10px] font-mono">/ingest</span>
                            </span>
                            <span class="text-[10px] text-slate-400 line-clamp-2">Ingest & summarize unread raw source materials.</span>
                        </button>
                        
                        <button onclick="selectCommand('query', 'Query the brain and synthesize an answer')" class="cmd-btn border border-slate-800 bg-slate-900/50 hover:bg-indigo-950/20 hover:border-indigo-500/50 p-3 rounded-lg text-left transition-all flex flex-col gap-1 focus:outline-none" id="btn-query">
                            <span class="text-xs font-bold text-indigo-400 flex items-center gap-1">
                                <span class="bg-indigo-950 text-indigo-400 px-1.5 py-0.5 rounded text-[10px] font-mono">/query</span>
                            </span>
                            <span class="text-[10px] text-slate-400 line-clamp-2">Synthesize grounded answers using index pages.</span>
                        </button>

                        <button onclick="selectCommand('lint', 'Run sanity audits and link checks on your wiki')" class="cmd-btn border border-slate-800 bg-slate-900/50 hover:bg-indigo-950/20 hover:border-indigo-500/50 p-3 rounded-lg text-left transition-all flex flex-col gap-1 focus:outline-none" id="btn-lint">
                            <span class="text-xs font-bold text-indigo-400 flex items-center gap-1">
                                <span class="bg-indigo-950 text-indigo-400 px-1.5 py-0.5 rounded text-[10px] font-mono">/lint</span>
                            </span>
                            <span class="text-[10px] text-slate-400 line-clamp-2">Perform health checks, link audits, and contradictions.</span>
                        </button>

                        <button onclick="selectCommand('log', 'Quick append thoughts into wiki/log.md')" class="cmd-btn border border-slate-800 bg-slate-900/50 hover:bg-indigo-950/20 hover:border-indigo-500/50 p-3 rounded-lg text-left transition-all flex flex-col gap-1 focus:outline-none" id="btn-log">
                            <span class="text-xs font-bold text-indigo-400 flex items-center gap-1">
                                <span class="bg-indigo-950 text-indigo-400 px-1.5 py-0.5 rounded text-[10px] font-mono">/log</span>
                            </span>
                            <span class="text-[10px] text-slate-400 line-clamp-2">Direct logging to timestamp activity archives.</span>
                        </button>

                        <button onclick="selectCommand('voice', 'Learn my writing voice from chat exports and notes')" class="cmd-btn border border-slate-800 bg-slate-900/50 hover:bg-indigo-950/20 hover:border-indigo-500/50 p-3 rounded-lg text-left transition-all flex flex-col gap-1 focus:outline-none" id="btn-voice">
                            <span class="text-xs font-bold text-indigo-400 flex items-center gap-1">
                                <span class="bg-indigo-950 text-indigo-400 px-1.5 py-0.5 rounded text-[10px] font-mono">/voice</span>
                            </span>
                            <span class="text-[10px] text-slate-400 line-clamp-2">Refine the voice profile from your own writing.</span>
                        </button>

                        <button onclick="selectCommand('module', 'Build wiki project pages for my NUS modules')" class="cmd-btn border border-slate-800 bg-slate-900/50 hover:bg-indigo-950/20 hover:border-indigo-500/50 p-3 rounded-lg text-left transition-all flex flex-col gap-1 focus:outline-none" id="btn-module">
                            <span class="text-xs font-bold text-indigo-400 flex items-center gap-1">
                                <span class="bg-indigo-950 text-indigo-400 px-1.5 py-0.5 rounded text-[10px] font-mono">/module</span>
                            </span>
                            <span class="text-[10px] text-slate-400 line-clamp-2">Build NUS module pages from raw/nusmods + your notes.</span>
                        </button>
                    </div>

                    <!-- Argument Input Section -->
                    <div class="flex items-center gap-2 mt-1">
                        <div class="relative flex-1">
                            <input type="text" id="commandArgument" placeholder="Choose a command above to specify argument parameters..." disabled class="w-full bg-slate-900 border border-slate-800 text-sm text-slate-100 rounded-lg pl-3 pr-10 py-2 focus:outline-none focus:border-indigo-500 disabled:opacity-50 transition-all">
                            <span class="absolute right-3 top-2.5 text-[10px] font-mono text-slate-500" id="arg-hint"></span>
                        </div>
                        <button onclick="executeCommand()" id="execute-btn" disabled class="bg-indigo-600 hover:bg-indigo-500 active:scale-95 disabled:opacity-40 text-white font-semibold text-xs px-5 py-2.5 rounded-lg flex items-center gap-2 shadow-lg transition-all focus:outline-none">
                            <i data-lucide="play" class="w-4 h-4"></i> Run
                        </button>
                    </div>
                </div>

                <!-- Execution Terminal / Logs Output Panel -->
                <div class="flex-1 flex flex-col overflow-hidden">
                    <!-- Tabs for output display -->
                    <div class="bg-slate-900/30 px-4 py-2 border-b border-slate-800 flex items-center justify-between text-xs font-semibold text-slate-400">
                        <div class="flex items-center gap-4">
                            <button id="tab-response-btn" class="text-indigo-400 border-b-2 border-indigo-500 pb-1.5 focus:outline-none">AI Response Output</button>
                        </div>
                        <span id="loader-spinner" class="hidden items-center gap-2 text-indigo-400 animate-pulse text-[11px]">
                            <span class="w-2 h-2 bg-indigo-500 rounded-full animate-ping"></span> Thinking...
                        </span>
                    </div>

                    <!-- Output Screens Container -->
                    <div class="flex-1 overflow-y-auto p-6 custom-scroll space-y-6 bg-slate-950/60" id="terminal-content">
                        <!-- Welcome instructions -->
                        <div id="default-screen" class="h-full flex flex-col items-center justify-center text-center p-8 space-y-4">
                            <div class="w-16 h-16 bg-slate-900 border border-slate-800 text-indigo-400 flex items-center justify-center rounded-2xl shadow-xl">
                                <i data-lucide="sparkles" class="w-8 h-8"></i>
                            </div>
                            <div class="max-w-md">
                                <h3 class="font-bold text-slate-200 mb-1">Interactive Command Space</h3>
                                <p class="text-xs text-slate-400">Select any command above, fill in potential arguments or instructions, and run. Your local system files will automatically be fed into your workspace model for reading and writing.</p>
                            </div>
                        </div>

                        <!-- Main AI Output area (initially hidden) -->
                        <div id="ai-response-area" class="hidden space-y-6">
                            <!-- Diagnostic step logs -->
                            <div class="bg-slate-900 border border-slate-800/80 rounded-lg p-3 space-y-1.5 font-mono text-[11px] text-slate-400">
                                <div class="text-xs font-bold text-slate-300 pb-1 border-b border-slate-800/60 flex items-center gap-1.5">
                                    <i data-lucide="activity" class="w-3.5 h-3.5 text-indigo-400"></i> Operation Logs
                                </div>
                                <div id="log-feed" class="space-y-1"></div>
                            </div>

                            <!-- Markdown response window -->
                            <div class="bg-slate-900/20 border border-slate-800 rounded-xl p-6 shadow-sm">
                                <div class="text-xs font-bold text-slate-400 mb-3 uppercase tracking-wider flex items-center gap-2">
                                    <i data-lucide="brain-circuit" class="w-4 h-4 text-emerald-400"></i> Synthesized Markdown Result
                                </div>
                                <div id="rendered-output" class="markdown-output text-sm"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right-Panel: Code / Markdown file editor -->
            <div class="w-full md:w-96 bg-slate-900/30 flex flex-col border-t md:border-t-0 border-slate-800 overflow-hidden">
                <div class="p-4 border-b border-slate-800 flex items-center justify-between shrink-0 bg-slate-900/40">
                    <span class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                        <i data-lucide="edit-3" class="w-4 h-4 text-indigo-400"></i> Local File Editor
                    </span>
                    <button onclick="saveCurrentFile()" id="save-editor-btn" disabled class="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors focus:outline-none">
                        <i data-lucide="save" class="w-3.5 h-3.5"></i> Save Changes
                    </button>
                </div>

                <!-- Editor Workspace Area -->
                <div class="flex-1 flex flex-col overflow-hidden bg-slate-950">
                    <div id="editor-placeholder" class="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-500">
                        <i data-lucide="file-edit" class="w-8 h-8 mb-2 opacity-50"></i>
                        <p class="text-xs">Select any file from the explorer on the left to read or edit its contents.</p>
                    </div>

                    <div id="editor-workarea" class="hidden flex-1 flex flex-col overflow-hidden">
                        <div class="bg-slate-900 px-4 py-2 border-b border-slate-800 text-xs text-slate-400 font-mono truncate" id="editor-filepath-label">
                            No file open
                        </div>
                        <textarea id="editor-textarea" class="flex-1 p-4 bg-slate-950 font-mono text-xs text-slate-300 focus:outline-none resize-none custom-scroll" placeholder="Write file contents here..."></textarea>
                    </div>
                </div>
            </div>

        </section>

    </main>

    <!-- Modal dialogue for file creation -->
    <div id="new-file-modal" class="hidden fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div class="flex items-center gap-3">
                <div class="p-2 bg-indigo-900/50 rounded-lg text-indigo-400">
                    <i data-lucide="clipboard-paste" class="w-6 h-6"></i>
                </div>
                <div>
                    <h3 class="font-bold text-slate-100 text-sm">Paste a New Note</h3>
                    <p class="text-xs text-slate-400">Pick a folder, name it, paste your text. Saved as a markdown file.</p>
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                    <label class="block text-slate-400 font-medium mb-1">Destination folder</label>
                    <select id="new-file-folder" class="w-full bg-slate-950 border border-slate-800 text-slate-100 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500">
                        <!-- options injected from /api/vault -->
                    </select>
                </div>
                <div>
                    <label class="block text-slate-400 font-medium mb-1">File name</label>
                    <input type="text" id="new-file-name" placeholder="my-note (.md added if omitted)" class="w-full bg-slate-950 border border-slate-800 text-slate-100 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500">
                </div>
            </div>

            <div class="text-xs">
                <label class="block text-slate-400 font-medium mb-1">Content</label>
                <textarea id="new-file-content" rows="12" placeholder="Paste your markdown or notes here..." class="w-full bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500 resize-y custom-scroll"></textarea>
                <p class="text-[10px] text-slate-500 mt-1" id="new-file-preview">Will save to raw/notes/</p>
            </div>

            <div class="flex items-center justify-end gap-2 text-xs pt-1">
                <button onclick="closeNewFileModal()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-lg">Cancel</button>
                <button onclick="submitNewFile()" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow flex items-center gap-1.5"><i data-lucide="save" class="w-3.5 h-3.5"></i> Save Note</button>
            </div>
        </div>
    </div>

    <!-- Interactive Toast Alerts -->
    <div id="toast-container" class="fixed bottom-4 right-4 z-50 space-y-2 pointer-events-none"></div>

    <script>
        // Active selection trackers
        let activeCommand = "";
        let openEditingPath = "";
        // Remembers which folders are collapsed so the tree keeps its state across refreshes
        const collapsedFolders = new Set();
        // raw/ subfolders, refreshed from the API, used to fill the paste-note destination picker
        let rawSubfolders = [];

        document.addEventListener("DOMContentLoaded", () => {
            lucide.createIcons();
            refreshVault();
            initUploader();
        });

        function updateDropTargetLabel() {
            const folder = document.getElementById("upload-folder").value;
            document.getElementById("drop-target-label").innerText = `→ raw/${folder}`;
        }

        function initUploader() {
            const zone = document.getElementById("drop-zone");
            const input = document.getElementById("upload-input");
            const folderSelect = document.getElementById("upload-folder");

            folderSelect.addEventListener("change", updateDropTargetLabel);
            zone.addEventListener("click", () => input.click());
            input.addEventListener("change", () => {
                if (input.files.length) uploadFiles(Array.from(input.files));
                input.value = ""; // allow re-selecting the same file
            });

            // Drag highlight
            ["dragenter", "dragover"].forEach(ev =>
                zone.addEventListener(ev, e => {
                    e.preventDefault();
                    zone.classList.add("border-indigo-500", "bg-indigo-950/30");
                }));
            ["dragleave", "drop"].forEach(ev =>
                zone.addEventListener(ev, e => {
                    e.preventDefault();
                    zone.classList.remove("border-indigo-500", "bg-indigo-950/30");
                }));
            zone.addEventListener("drop", e => {
                const files = Array.from(e.dataTransfer.files || []);
                if (files.length) uploadFiles(files);
            });
        }

        function readAsBase64(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result.split(",")[1]);
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
        }

        async function uploadFiles(files) {
            const folder = document.getElementById("upload-folder").value;
            const progress = document.getElementById("upload-progress");
            progress.classList.remove("hidden");
            progress.innerText = `Reading ${files.length} file(s)...`;

            try {
                const payload = await Promise.all(files.map(async f => ({
                    name: f.name,
                    data: await readAsBase64(f)
                })));

                progress.innerText = `Uploading to raw/${folder}...`;
                const res = await fetch("/api/upload", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ folder, files: payload })
                });
                const data = await res.json();

                if (res.ok) {
                    const n = (data.saved || []).length;
                    const failed = (data.failed || []).length;
                    progress.innerText = `Added ${n} file(s) to raw/${folder}` + (failed ? `, ${failed} failed` : "");
                    showToast(`Uploaded ${n} file(s) to raw/${folder}` + (failed ? ` (${failed} failed)` : ""), failed ? "error" : "success");
                    refreshVault();
                } else {
                    progress.innerText = `Upload failed: ${data.error || "unknown error"}`;
                    showToast(data.error || "Upload failed", "error");
                }
            } catch (err) {
                progress.innerText = `Upload error: ${err}`;
                showToast("Upload error", "error");
            } finally {
                setTimeout(() => progress.classList.add("hidden"), 4000);
            }
        }

        // Toggle command selections
        function selectCommand(cmd, placeholderText) {
            activeCommand = cmd;
            
            // Set styles
            document.querySelectorAll(".cmd-btn").forEach(btn => {
                btn.classList.remove("border-indigo-500", "bg-indigo-950/30");
            });
            document.getElementById(`btn-${cmd}`).classList.add("border-indigo-500", "bg-indigo-950/30");
            
            // Update UI displays
            const argInput = document.getElementById("commandArgument");
            const hintDisplay = document.getElementById("arg-hint");
            const displayBadge = document.getElementById("active-command-display");

            displayBadge.innerText = `Active: /${cmd}`;
            argInput.disabled = false;
            
            if (cmd === 'ingest') {
                argInput.placeholder = "E.g. 5 (Number of maximum raw documents to process)";
                hintDisplay.innerText = "limit count";
            } else if (cmd === 'query') {
                argInput.placeholder = "Enter query (E.g. What were the key findings in deep work notes?)";
                hintDisplay.innerText = "your question";
            } else if (cmd === 'log') {
                argInput.placeholder = "Type your quick thought or log (E.g. Explored gpt4free backend configurations)";
                hintDisplay.innerText = "your note";
            } else if (cmd === 'lint') {
                argInput.placeholder = "Audit check runs completely autonomously. Click Run.";
                argInput.disabled = true;
                hintDisplay.innerText = "none required";
            } else if (cmd === 'voice') {
                argInput.placeholder = "Optional: max number of files to learn from (e.g. 10). Leave blank to sample broadly.";
                hintDisplay.innerText = "optional file count";
            } else if (cmd === 'module') {
                argInput.placeholder = "Optional: a single module code (e.g. CS2103T). Leave blank to build all fetched modules.";
                hintDisplay.innerText = "optional module code";
            }

            document.getElementById("execute-btn").disabled = false;
        }

        async function executeCommand() {
            if (!activeCommand) return;
            
            const argVal = document.getElementById("commandArgument").value;
            const runBtn = document.getElementById("execute-btn");
            const spinner = document.getElementById("loader-spinner");
            const modelVal = document.getElementById("modelSelector").value;

            // Trigger loaders
            runBtn.disabled = true;
            spinner.classList.remove("hidden");
            spinner.classList.add("flex");
            
            // Clean up old terminal views
            document.getElementById("default-screen").classList.add("hidden");
            document.getElementById("ai-response-area").classList.remove("hidden");
            
            const logsFeed = document.getElementById("log-feed");
            logsFeed.innerHTML = `<div class="text-indigo-400">⚡ Starting /${activeCommand}...</div>`;
            document.getElementById("rendered-output").innerHTML = `<p class="italic text-slate-400">Consulting gpt4free models and parsing vault parameters...</p>`;

            try {
                const response = await fetch('/api/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        command: activeCommand,
                        arguments: argVal,
                        model: modelVal
                    })
                });

                const data = await response.json();
                
                // Write detailed execution logs
                if (data.logs) {
                    logsFeed.innerHTML = "";
                    data.logs.forEach(logLine => {
                        const div = document.createElement("div");
                        div.innerText = logLine;
                        logsFeed.appendChild(div);
                    });
                }

                if (response.ok) {
                    // Update and compile output markdown content
                    const renderedHtml = marked.parse(data.output || "");
                    document.getElementById("rendered-output").innerHTML = renderedHtml;
                    showToast("Command completed successfully!", "success");
                    refreshVault();
                } else {
                    document.getElementById("rendered-output").innerHTML = `<p class="text-rose-500 font-semibold">Error: ${data.error || "An error occurred during execution."}</p>`;
                    showToast("Error executing action", "error");
                }
            } catch (err) {
                logsFeed.innerHTML += `<div class="text-rose-500 font-bold">🚨 Connection loss: ${err}</div>`;
                showToast("Server connection error", "error");
            } finally {
                runBtn.disabled = false;
                spinner.classList.add("hidden");
                spinner.classList.remove("flex");
            }
        }

        // Fetch directory structural mapping
        async function refreshVault() {
            try {
                const res = await fetch('/api/vault');
                const data = await res.json();

                const rawList = document.getElementById("raw-list");
                const wikiList = document.getElementById("wiki-list");

                document.getElementById("raw-count").innerText = data.raw.length;
                document.getElementById("wiki-count").innerText = data.wiki.length;

                // Remember raw subfolders for the paste-note modal
                rawSubfolders = data.raw_subfolders || [];

                // Populate upload destination picker (preserve current selection)
                const folderSelect = document.getElementById("upload-folder");
                const folders = data.raw_subfolders || [];
                if (folderSelect && folders.length && folderSelect.options.length !== folders.length) {
                    const prev = folderSelect.value;
                    folderSelect.innerHTML = "";
                    folders.forEach(f => {
                        const opt = document.createElement("option");
                        opt.value = f;
                        opt.innerText = f;
                        folderSelect.appendChild(opt);
                    });
                    folderSelect.value = folders.includes(prev) ? prev : (folders.includes("notes") ? "notes" : folders[0]);
                    updateDropTargetLabel();
                }

                // Render each area as a collapsible folder tree
                renderTree(rawList, data.raw, "raw/", "file", "text-amber-500", "No raw files.");
                renderTree(wikiList, data.wiki, "wiki/", "book-open", "text-emerald-500", "No wiki pages.");

                lucide.createIcons();
            } catch (err) {
                console.error("Vault listing error:", err);
            }
        }

        // Group a flat list of paths by their first subfolder and render a
        // collapsible tree. Files sitting directly in the root show first,
        // then one collapsible section per subfolder.
        function renderTree(container, files, rootPrefix, fileIcon, iconColor, emptyText) {
            container.innerHTML = "";
            if (!files || files.length === 0) {
                container.innerHTML = `<p class="text-xs text-slate-500 italic">${emptyText}</p>`;
                return;
            }

            const folders = {};
            const rootFiles = [];
            files.forEach(full => {
                const rel = full.substring(rootPrefix.length);
                const slash = rel.indexOf("/");
                if (slash === -1) {
                    rootFiles.push({ full, name: rel });
                } else {
                    const folder = rel.substring(0, slash);
                    const name = rel.substring(slash + 1);
                    (folders[folder] = folders[folder] || []).push({ full, name });
                }
            });

            const makeFileBtn = (f) => {
                const btn = document.createElement("button");
                btn.className = "w-full text-left text-xs text-slate-300 hover:text-white hover:bg-slate-800/60 p-1.5 rounded flex items-center gap-1.5 truncate focus:outline-none";
                btn.innerHTML = `<i data-lucide="${fileIcon}" class="w-3.5 h-3.5 ${iconColor} shrink-0"></i> <span class="truncate">${f.name}</span>`;
                btn.onclick = () => openFile(f.full);
                return btn;
            };

            // Root-level files first, no folder header
            rootFiles.sort((a, b) => a.name.localeCompare(b.name)).forEach(f => container.appendChild(makeFileBtn(f)));

            // Then one collapsible section per subfolder, alphabetical
            Object.keys(folders).sort().forEach(folder => {
                const key = rootPrefix + folder;
                const collapsed = collapsedFolders.has(key);

                const header = document.createElement("button");
                header.className = "w-full text-left text-xs font-medium text-slate-400 hover:text-slate-200 p-1.5 rounded flex items-center gap-1.5 focus:outline-none mt-0.5";
                header.innerHTML =
                    `<span class="chev inline-flex transition-transform duration-150 ${collapsed ? '-rotate-90' : ''}"><i data-lucide="chevron-down" class="w-3.5 h-3.5 shrink-0"></i></span>` +
                    `<i data-lucide="folder" class="w-3.5 h-3.5 text-indigo-400/80 shrink-0"></i>` +
                    `<span class="truncate">${folder}</span>` +
                    `<span class="ml-auto text-[10px] text-slate-600">${folders[folder].length}</span>`;

                const filesWrap = document.createElement("div");
                filesWrap.className = "pl-3 ml-2 border-l border-slate-800/60 space-y-0.5" + (collapsed ? " hidden" : "");
                folders[folder].sort((a, b) => a.name.localeCompare(b.name)).forEach(f => filesWrap.appendChild(makeFileBtn(f)));

                header.onclick = () => {
                    const nowCollapsed = !collapsedFolders.has(key);
                    if (nowCollapsed) collapsedFolders.add(key); else collapsedFolders.delete(key);
                    filesWrap.classList.toggle("hidden", nowCollapsed);
                    header.querySelector(".chev").classList.toggle("-rotate-90", nowCollapsed);
                };

                container.appendChild(header);
                container.appendChild(filesWrap);
            });
        }

        // Open specific file in preview and local editor
        async function openFile(filePath) {
            try {
                const res = await fetch(`/api/file?path=${encodeURIComponent(filePath)}`);
                const data = await res.json();
                
                openEditingPath = filePath;

                // Update UI layout views
                document.getElementById("editor-placeholder").classList.add("hidden");
                document.getElementById("editor-workarea").classList.remove("hidden");
                
                document.getElementById("editor-filepath-label").innerText = filePath;
                document.getElementById("editor-textarea").value = data.content;
                document.getElementById("save-editor-btn").disabled = false;
                
                showToast(`Opened file: ${filePath}`, "info");
            } catch (err) {
                showToast("Failed to load file.", "error");
            }
        }

        async function saveCurrentFile() {
            if (!openEditingPath) return;
            const content = document.getElementById("editor-textarea").value;
            const saveBtn = document.getElementById("save-editor-btn");

            saveBtn.disabled = true;
            try {
                const res = await fetch('/api/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        path: openEditingPath,
                        content: content
                    })
                });

                if (res.ok) {
                    showToast("Saved modifications!", "success");
                    refreshVault();
                } else {
                    showToast("Error updating file contents.", "error");
                }
            } catch (err) {
                showToast("Failed to communicate with server.", "error");
            } finally {
                saveBtn.disabled = false;
            }
        }

        // Utility Modal Handlers
        function openNewFileModal() {
            // Build the destination dropdown: every raw/ subfolder, then wiki areas
            const sel = document.getElementById("new-file-folder");
            const rawOpts = (rawSubfolders.length ? rawSubfolders : ["notes"]).map(f => `raw/${f}/`);
            const wikiOpts = ["wiki/concepts/", "wiki/projects/", "wiki/people/", "wiki/source-summaries/"];
            const all = [...rawOpts, ...wikiOpts];
            sel.innerHTML = "";
            all.forEach(p => {
                const opt = document.createElement("option");
                opt.value = p;
                opt.innerText = p;
                sel.appendChild(opt);
            });
            sel.value = all.includes("raw/notes/") ? "raw/notes/" : all[0];

            sel.onchange = updateNewFilePreview;
            document.getElementById("new-file-name").oninput = updateNewFilePreview;
            updateNewFilePreview();

            document.getElementById("new-file-modal").classList.remove("hidden");
            document.getElementById("new-file-name").focus();
        }

        function closeNewFileModal() {
            document.getElementById("new-file-modal").classList.add("hidden");
            document.getElementById("new-file-name").value = "";
            document.getElementById("new-file-content").value = "";
        }

        // Normalise a filename: trim, default, and ensure a .md extension
        function normalisedFileName() {
            let name = document.getElementById("new-file-name").value.trim();
            if (!name) return "";
            if (!/\\.[a-z0-9]+$/i.test(name)) name += ".md";
            return name;
        }

        function updateNewFilePreview() {
            const folder = document.getElementById("new-file-folder").value;
            const name = normalisedFileName();
            document.getElementById("new-file-preview").innerText =
                name ? `Will save to ${folder}${name}` : `Will save to ${folder}`;
        }

        async function submitNewFile() {
            const folder = document.getElementById("new-file-folder").value;
            const name = normalisedFileName();
            const content = document.getElementById("new-file-content").value;
            if (!name) {
                showToast("Give the file a name", "error");
                return;
            }
            if (!content.trim()) {
                showToast("Paste some content first", "error");
                return;
            }

            const targetPath = `${folder}${name}`;
            try {
                const res = await fetch('/api/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: targetPath, content: content })
                });

                if (res.ok) {
                    showToast(`Saved ${targetPath}`, "success");
                    closeNewFileModal();
                    refreshVault();
                    openFile(targetPath);
                } else {
                    const data = await res.json().catch(() => ({}));
                    showToast(data.error || "Error saving file.", "error");
                }
            } catch (err) {
                showToast("Server error while saving.", "error");
            }
        }

        // Show elegant custom notifications
        function showToast(message, type = "info") {
            const container = document.getElementById("toast-container");
            const toast = document.createElement("div");
            toast.className = `p-3.5 rounded-xl shadow-2xl text-xs font-semibold flex items-center gap-2 border transition-all duration-300 transform translate-y-2 opacity-0 pointer-events-auto max-w-sm `;
            
            if (type === "success") {
                toast.className += "bg-slate-900 border-emerald-500 text-emerald-400";
                toast.innerHTML = `<i data-lucide="check-circle" class="w-4 h-4 shrink-0"></i> <span>${message}</span>`;
            } else if (type === "error") {
                toast.className += "bg-slate-900 border-rose-500 text-rose-400";
                toast.innerHTML = `<i data-lucide="alert-triangle" class="w-4 h-4 shrink-0"></i> <span>${message}</span>`;
            } else {
                toast.className += "bg-slate-900 border-slate-700 text-slate-300";
                toast.innerHTML = `<i data-lucide="info" class="w-4 h-4 shrink-0"></i> <span>${message}</span>`;
            }

            container.appendChild(toast);
            lucide.createIcons();

            // Animate In
            setTimeout(() => {
                toast.classList.remove("translate-y-2", "opacity-0");
            }, 10);

            // Animate Out & Destroy
            setTimeout(() => {
                toast.classList.add("translate-y-2", "opacity-0");
                setTimeout(() => {
                    toast.remove();
                }, 300);
            }, 4000);
        }
    </script>
</body>
</html>
"""

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle each request in its own thread so a slow g4f call
    doesn't freeze the vault explorer or editor."""
    daemon_threads = True
    # Reuse the address so a freshly-stopped server can restart immediately
    # instead of tripping over a lingering TIME_WAIT socket.
    allow_reuse_address = True

PROVIDER_MAX_AGE_DAYS = 7  # auto re-probe when providers.json is older than this

def maybe_refresh_providers():
    """If providers.json is missing or stale, re-probe in the background and
    rebuild the chain when done. Runs in a daemon thread so startup never blocks
    and the dashboard works immediately with whatever list it already has."""
    if not G4F_AVAILABLE:
        return
    try:
        age_days = (time.time() - os.path.getmtime(PROVIDERS_JSON)) / 86400
        if age_days <= PROVIDER_MAX_AGE_DAYS:
            return  # fresh enough
        reason = f"list is {age_days:.0f} days old"
    except OSError:
        reason = "no providers.json yet"

    def worker():
        print(f"🔄 Refreshing provider list in the background ({reason})...")
        try:
            import probe_providers
            if probe_providers.main() == 0:
                rebuild_provider_chain()
                print(f"✅ Provider list refreshed: {', '.join(PROVIDER_NAMES)}")
        except Exception as e:
            print(f"⚠️ Provider auto-refresh failed ({type(e).__name__}); keeping current list.")

    threading.Thread(target=worker, daemon=True).start()

def run_server():
    initialize_vault()
    maybe_refresh_providers()

    server_address = ('', PORT)
    try:
        httpd = ThreadingHTTPServer(server_address, BrainAPIHandler)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"\n⚠️  Port {PORT} is already in use.")
            print(f"   Another Second Brain server is probably still running.")
            print(f"   Find and stop it with:")
            print(f"     lsof -nP -iTCP:{PORT} -sTCP:LISTEN")
            print(f"     kill <PID>")
            print(f"   Or change the PORT value near the top of brain_ui.py.\n")
            sys.exit(1)
        raise

    print("\n" + "="*50)
    print(f"🧠 SECOND BRAIN LOCAL DASHBOARD ENGINE ONLINE")
    print(f"🔗 Navigate to: http://localhost:{PORT}")
    print("="*50 + "\n")
    print("Running background synchronization system. Press Ctrl+C to close.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Local Second Brain server engine.")
        httpd.server_close()

if __name__ == '__main__':
    run_server()