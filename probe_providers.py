#!/usr/bin/env python3
"""Probe g4f no-auth providers and write the working ones to providers.json.

brain_ui.py reads providers.json to build its fallback chain, so re-running
this refreshes which providers the dashboard uses without touching any code.
The free g4f providers rotate constantly, so run this whenever the dashboard
starts failing, or just let brain_ui.py auto-run it in the background when the
list goes stale.

Usage:
    ./env/bin/python probe_providers.py
"""

import os
import sys
import json
import datetime
import warnings
import concurrent.futures as cf

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "providers.json")

# Candidates in priority order. PollinationsAI stays first when it's healthy
# because the UI's model dropdown maps to its model names. The rest are
# fallbacks that use their own default model. Add or reorder freely.
CANDIDATES = [
    "PollinationsAI", "Yqcloud", "WeWordle", "OperaAria", "Felo",
    "OpenRouterFree", "DeepInfra", "Groq", "Nvidia", "Perplexity",
    "PhindAi", "Pi", "Qwen", "EasyChat",
]

PER_PROVIDER_TIMEOUT = 25  # hard cap per provider so one hang can't stall the run
TEST_MESSAGE = [{"role": "user", "content": "Reply with exactly one word: OK"}]


def _probe_one(name):
    """Return True if the provider answers with non-empty text, else raise."""
    import g4f.Provider as P
    from g4f.client import Client
    prov = getattr(P, name, None)
    if prov is None:
        raise ValueError("provider not found in this g4f version")
    # PollinationsAI needs an explicit valid model; others use their default.
    model = "openai" if name == "PollinationsAI" else (getattr(prov, "default_model", None) or "")
    client = Client(provider=prov)
    resp = client.chat.completions.create(model=model, messages=TEST_MESSAGE, timeout=18)
    text = (resp.choices[0].message.content or "").strip()
    if not text:
        raise ValueError("empty response")
    return True


def probe_all(verbose=True):
    """Probe every candidate, preserving priority order. Returns working names."""
    working = []
    seen = set()
    for name in CANDIDATES:
        if name in seen:
            continue
        seen.add(name)
        try:
            with cf.ThreadPoolExecutor(max_workers=1) as ex:
                ex.submit(_probe_one, name).result(timeout=PER_PROVIDER_TIMEOUT)
            working.append(name)
            if verbose:
                print(f"  WORKS  {name}")
        except Exception as e:
            if verbose:
                print(f"  fail   {name} ({type(e).__name__})")
    return working


def main():
    print("Probing g4f no-auth providers (this can take a couple of minutes)...")
    working = probe_all(verbose=True)

    if not working:
        print("\nNo providers responded. Leaving the existing list untouched.")
        return 1

    data = {
        "updated": datetime.datetime.now().isoformat(timespec="seconds"),
        "providers": working,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"\nWrote {len(working)} working providers to {OUT_PATH}:")
    print("  " + ", ".join(working))
    print("Restart brain_ui.py (or wait for its background refresh) to use the new list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
