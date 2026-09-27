# Patent Diligence Assistant — Prototype

A working scaffold of the tool described in the build prompt: scans code for
similarity to a seed patent set, flags license/dependency signals, cross-checks
a design doc, and drafts a provisional patent skeleton — all framed as
**signals for human/legal review, never a legal verdict.**

## What's here

```
backend/
  main.py         FastAPI app — all endpoints from the API contract
  seed_data.py    10 synthetic seed patents (health + disaster-alert domains)
  similarity.py   Dependency-free lexical-overlap scorer (swap for real
                  embeddings later — see "Known simplifications" below)
sample_repo/
  monitoring.py   Demo repo with one boilerplate function (should NOT be
                  flagged) and two functions deliberately worded to echo
                  seed patent abstracts (SHOULD be flagged)
  requirements.txt  Includes one demo "license signal" dependency
frontend/
  index.html      Dashboard + Risk Memo screens (React via CDN, no build
                  step needed) — open directly in a browser once the
                  backend is running
```

## Run it

```bash
cd backend
pip install fastapi uvicorn python-multipart --break-system-packages
uvicorn main:app --reload --port 8000
```

Then open `frontend/index.html` directly in a browser (double-click it, or
`python3 -m http.server` from the `frontend/` folder). Click **Run diligence
scan** on the Dashboard tab, then switch to **Risk Memo** to watch it
complete and generate a draft.

I verified the core logic (function extraction, similarity scoring, license
flagging) runs correctly against the sample repo in this environment — see
the two test runs above. I couldn't install FastAPI here (no network
access), so the live server itself is untested end-to-end; a run on your
machine should confirm the API layer.

## Confirmed working (tested against the sample repo)

- `detect_fall_event` → correctly matched to the seed "wearable fall-detection" patent (33% overlap)
- `dedupe_alert_batch` → correctly matched to the seed "message deduplication" patent (29% overlap)
- `_clamp` (trivial boilerplate) → correctly **not** flagged
- `gif-tools` in requirements.txt → correctly flagged as a license signal

## Known simplifications (flagged honestly, not hidden)

1. **Similarity scoring is lexical (word-overlap), not embeddings.** This
   keeps the prototype dependency-free and inspectable, but it will miss
   conceptual similarity that uses different vocabulary, and can
   false-positive on shared common terms. Swap `similarity.py`'s `score()`
   for a real embedding call (Anthropic API, a local sentence-transformer,
   or a patent-search API) before this leaves demo status.
2. **The scan always runs against the bundled `sample_repo`**, regardless of
   the repo URL entered in the Dashboard — there's no real git-clone step
   yet. Wire that in via a job queue (Celery/RQ) once you're past the demo.
3. **Seed patents are synthetic**, written for this prototype — not real
   USPTO filings. Swap in a real patent-search feed before any real
   diligence work relies on this.
4. **License-signal table is a small hardcoded demo list** (`gif-tools`,
   etc.), not a real SPDX/patent-encumbrance database.
5. **Storage is in-memory** (dicts) — scans disappear on server restart.
   Swap for SQLite/Postgres before this is used by more than one person.
6. **No auth** — the API contract's auth stub was left out entirely for
   this pass; add before deploying anywhere reachable.
7. **Provisional draft is Markdown only** — `.docx` export via
   `python-docx` was scoped out of this pass; the API already returns a
   `format` field so it's a small addition later.

## Next steps toward the full build prompt

- Add the pre-commit/pre-merge hook described in the build prompt's step 3.
- Add the "upload design doc" flow to the Dashboard (backend endpoint
  `/docs/upload` and Subagent C already work — just needs a file-picker UI
  and a way to attach the resulting `doc_id` to a scan).
- Add "Export as Word" for the provisional draft using `python-docx`
  (the API already returns a `format` field for this).
- Replace lexical similarity with real embeddings once you're ready to move
  past the zero-dependency demo.

## Frontend screens (all four now built)

- **Dashboard** — connect a repo, trigger a scan, see recent scans
- **Risk Memo** — live subagent progress, flagged functions/license/doc
  signals, provisional draft generator
- **Audit Trail** — chronological, expandable log of every orchestrator and
  subagent step for the active scan
- **Seed Patents** — table of the current seed set + a form to add new
  synthetic entries
