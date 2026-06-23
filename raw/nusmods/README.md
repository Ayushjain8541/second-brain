# raw/nusmods/

Official NUS module info pulled from the NUSMods API. Unlike the other raw/
folders, you don't fill this one by hand. It's populated automatically by
`fetch_modules.py`.

## How it works

1. List the modules you've taken in `my-modules.md` (at the vault root), one code per line.
2. Run the fetcher:
   ```
   ./env/bin/python fetch_modules.py
   ```
   It writes one file per module here (e.g. `CS2103T.md`) with the official title,
   description, syllabus, workload, and prerequisites from NUSMods.
3. Run `/module` to build the wiki project pages, which combine this official
   scaffold with links to your own learnings.

Each file notes its NUSMods source URL and fetch date. Re-running the fetcher
refreshes them.
