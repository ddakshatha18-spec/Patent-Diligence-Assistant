"""
Patent Diligence Assistant — backend prototype.

Run:
    pip install fastapi uvicorn python-multipart --break-system-packages
    uvicorn main:app --reload --port 8000

This is a DEMO/PROTOTYPE. Every output is a plain-language *signal for
human/legal review*, never a clearance determination or legal verdict.
That disclaimer is embedded directly in the API responses, not just the
docs, so it can't be silently dropped by a frontend.
"""

import ast
import asyncio
import re
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from seed_data import SEED_PATENTS
from similarity import best_matches

app = FastAPI(title="Patent Diligence Assistant API", version="0.1.0-demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo only — restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

DISCLAIMER = (
    "These are lexical/similarity SIGNALS for a human or patent attorney to "
    "review — not a legal clearance opinion, not a novelty determination, "
    "and not evidence of infringement."
)

# ---------------------------------------------------------------------------
# In-memory stores (swap for a real DB before this leaves prototype status)
# ---------------------------------------------------------------------------
PATENTS = {p["id"]: p for p in SEED_PATENTS}
SCANS: dict = {}
DRAFTS: dict = {}
DOCS: dict = {}

SAMPLE_REPO = Path(__file__).parent.parent / "sample_repo"

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ScanRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    pr_id: Optional[str] = None


class PatentIn(BaseModel):
    title: str
    abstract: str
    domain: str


class DraftRequest(BaseModel):
    scan_id: str
    code_snippet_ids: list[str] = []
    design_doc_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers — function extraction
# ---------------------------------------------------------------------------
def extract_functions(py_source: str, file_path: str):
    """Pull top-level/nested function defs + docstrings out of a Python file.
    Skips trivial boilerplate (dunder methods, < 3 statements, no docstring
    and short body) to approximate the orchestrator's 'real functions' step.
    """
    out = []
    try:
        tree = ast.parse(py_source)
    except SyntaxError:
        return out

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("__") and node.name.endswith("__"):
                continue
            body_lines = node.end_lineno - node.lineno if node.end_lineno else 0
            docstring = ast.get_docstring(node) or ""
            if body_lines < 3 and not docstring:
                continue  # boilerplate-ish, skip
            snippet = "\n".join(py_source.splitlines()[node.lineno - 1:node.end_lineno])
            out.append({
                "id": f"fn-{uuid.uuid4().hex[:8]}",
                "file_path": file_path,
                "function_name": node.name,
                "docstring": docstring,
                "code_snippet": snippet,
            })
    return out


# ---------------------------------------------------------------------------
# Subagent A — Code Similarity Scanner
# ---------------------------------------------------------------------------
async def subagent_a_code_similarity(functions: list):
    flagged = []
    for fn in functions:
        query_text = f"{fn['function_name']} {fn['docstring']} {fn['code_snippet']}"
        matches = best_matches(query_text, list(PATENTS.values()))
        for score, patent in matches:
            flagged.append({
                "function_id": fn["id"],
                "file_path": fn["file_path"],
                "function_name": fn["function_name"],
                "code_snippet": fn["code_snippet"],
                "matched_patent_id": patent["id"],
                "matched_patent_title": patent["title"],
                "similarity_score": score,
                "rationale": (
                    f"Function '{fn['function_name']}' shares notable "
                    f"terminology with seed abstract '{patent['title']}' "
                    f"(domain: {patent['domain']}). Lexical overlap only — "
                    "not a structural or algorithmic comparison."
                ),
            })
    return flagged


# ---------------------------------------------------------------------------
# Subagent B — License / Dependency Checker
# ---------------------------------------------------------------------------
# Small illustrative table of demo "signal" packages. In production this
# would be backed by an SPDX license DB + a curated patent-encumbrance list.
KNOWN_LICENSE_SIGNALS = {
    "some-codec-lib": ("Proprietary-Codec-1.0", "Historically associated with codec patent pools (demo entry)."),
    "patented-compress": ("Restricted", "Name signals a patent-related compression scheme (demo entry)."),
    "gif-tools": ("LZW-derived", "LZW compression has a well-known patent history, now expired but worth noting (demo entry)."),
}


async def subagent_b_license_check(repo_dir: Path):
    flags = []
    req_file = repo_dir / "requirements.txt"
    if req_file.exists():
        for line in req_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg = re.split(r"[=<>~! ]", line)[0].lower()
            if pkg in KNOWN_LICENSE_SIGNALS:
                license_name, reason = KNOWN_LICENSE_SIGNALS[pkg]
                flags.append({
                    "dependency": pkg,
                    "license": license_name,
                    "flag_reason": reason,
                })
    return flags


# ---------------------------------------------------------------------------
# Subagent C — Design-Doc Prior-Art Checker
# ---------------------------------------------------------------------------
async def subagent_c_design_doc(doc_text: str, doc_id: str):
    flags = []
    # naive section split on blank lines / headings
    sections = [s.strip() for s in re.split(r"\n\s*\n", doc_text) if s.strip()]
    for i, section in enumerate(sections):
        matches = best_matches(section, list(PATENTS.values()), top_k=1)
        for score, patent in matches:
            flags.append({
                "doc_id": doc_id,
                "doc_section": section[:120] + ("..." if len(section) > 120 else ""),
                "matched_patent_id": patent["id"],
                "matched_patent_title": patent["title"],
                "similarity_score": score,
                "note": (
                    f"Section {i+1} shares terminology with seed abstract "
                    f"'{patent['title']}'. Review the described method, not "
                    "just the wording."
                ),
            })
    return flags


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def log_step(scan_id: str, agent: str, action: str, input_ref: str = "", output_ref: str = ""):
    SCANS[scan_id]["audit"].append({
        "agent": agent,
        "action": action,
        "timestamp": time.time(),
        "input_ref": input_ref,
        "output_ref": output_ref,
    })


async def run_pipeline(scan_id: str):
    scan = SCANS[scan_id]
    scan["status"] = "running"
    scan["progress"] = {"A": "pending", "B": "pending", "C": "pending"}

    log_step(scan_id, "orchestrator", "scan_started", input_ref=scan["repo_url"])

    # --- Ask-mode-style step: identify "real" functions in the sample repo ---
    functions = []
    if SAMPLE_REPO.exists():
        for py_file in SAMPLE_REPO.rglob("*.py"):
            functions.extend(extract_functions(py_file.read_text(), str(py_file.relative_to(SAMPLE_REPO))))
    scan["functions"] = {f["id"]: f for f in functions}
    log_step(scan_id, "orchestrator", "identified_candidate_functions", output_ref=f"{len(functions)} functions")

    # --- Dispatch subagents "in parallel" ---
    async def a():
        scan["progress"]["A"] = "running"
        result = await subagent_a_code_similarity(functions)
        scan["flagged_functions"] = result
        scan["progress"]["A"] = "done"
        log_step(scan_id, "subagent_a", "code_similarity_scan", output_ref=f"{len(result)} flags")

    async def b():
        scan["progress"]["B"] = "running"
        result = await subagent_b_license_check(SAMPLE_REPO)
        scan["license_flags"] = result
        scan["progress"]["B"] = "done"
        log_step(scan_id, "subagent_b", "license_dependency_check", output_ref=f"{len(result)} flags")

    async def c():
        scan["progress"]["C"] = "running"
        doc_id = scan.get("design_doc_id")
        if doc_id and doc_id in DOCS:
            result = await subagent_c_design_doc(DOCS[doc_id]["text"], doc_id)
        else:
            result = []
        scan["doc_flags"] = result
        scan["progress"]["C"] = "done"
        log_step(scan_id, "subagent_c", "design_doc_prior_art_check", output_ref=f"{len(result)} flags")

    await asyncio.gather(a(), b(), c())

    # --- Risk memo ---
    scan["summary"] = {
        "disclaimer": DISCLAIMER,
        "flagged_function_count": len(scan.get("flagged_functions", [])),
        "license_flag_count": len(scan.get("license_flags", [])),
        "doc_flag_count": len(scan.get("doc_flags", [])),
        "headline": (
            "No signals found — still recommend a manual pass before release."
            if not (scan.get("flagged_functions") or scan.get("license_flags") or scan.get("doc_flags"))
            else "Signals found — route to a human/legal reviewer before relying on this code path or filing anything."
        ),
    }
    log_step(scan_id, "risk_memo_generator", "memo_compiled")

    scan["status"] = "complete"
    log_step(scan_id, "orchestrator", "scan_complete")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
API = "/api/v1"


@app.post(f"{API}/repos/scan")
async def trigger_scan(req: ScanRequest):
    scan_id = f"scan-{uuid.uuid4().hex[:8]}"
    SCANS[scan_id] = {
        "id": scan_id,
        "repo_url": req.repo_url,
        "branch": req.branch,
        "pr_id": req.pr_id,
        "status": "queued",
        "created_at": time.time(),
        "audit": [],
        "design_doc_id": None,
    }
    asyncio.create_task(run_pipeline(scan_id))
    return {"scan_id": scan_id, "status": "queued"}


@app.get(f"{API}/scans/{{scan_id}}/status")
async def scan_status(scan_id: str):
    scan = SCANS.get(scan_id)
    if not scan:
        raise HTTPException(404, "scan not found")
    return {"status": scan["status"], "progress": scan.get("progress", {"A": "pending", "B": "pending", "C": "pending"})}


@app.get(f"{API}/scans/{{scan_id}}/results")
async def scan_results(scan_id: str):
    scan = SCANS.get(scan_id)
    if not scan:
        raise HTTPException(404, "scan not found")
    if scan["status"] != "complete":
        raise HTTPException(409, f"scan not complete (status: {scan['status']})")
    return {
        "flagged_functions": scan.get("flagged_functions", []),
        "license_flags": scan.get("license_flags", []),
        "doc_flags": scan.get("doc_flags", []),
        "summary": scan.get("summary", {}),
    }


@app.get(f"{API}/patents/seed")
async def list_seed_patents():
    return {"patents": list(PATENTS.values())}


@app.post(f"{API}/patents/seed")
async def add_seed_patent(p: PatentIn):
    pid = f"seed-{uuid.uuid4().hex[:8]}"
    PATENTS[pid] = {"id": pid, "title": p.title, "abstract": p.abstract, "domain": p.domain, "source": "seed"}
    return {"id": pid}


@app.post(f"{API}/docs/upload")
async def upload_doc(file: UploadFile = File(...)):
    raw = await file.read()
    try:
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        text = ""
    doc_id = f"doc-{uuid.uuid4().hex[:8]}"
    DOCS[doc_id] = {"id": doc_id, "filename": file.filename, "text": text}
    return {"doc_id": doc_id}


@app.post(f"{API}/drafts/provisional")
async def generate_draft(req: DraftRequest):
    scan = SCANS.get(req.scan_id)
    if not scan:
        raise HTTPException(404, "scan not found")

    snippets = []
    for fid in req.code_snippet_ids:
        fn = scan.get("functions", {}).get(fid)
        if fn:
            snippets.append(fn)

    title = "Provisional Patent Application Skeleton (DRAFT — attorney review required)"
    field = "Field of the Invention\n\nThis disclosure relates generally to software systems for " \
            "[team to complete: describe the technical domain, e.g. 'remote patient monitoring']."
    background = "Background\n\nExisting approaches in this space [team to complete: summarize prior art " \
                 "landscape and the specific gap this invention addresses]."
    functions_desc = "\n".join(f"- `{s['function_name']}` ({s['file_path']})" for s in snippets) or "- [no functions selected]"
    description = f"Detailed Description\n\nThe following implementation elements are proposed as novel:\n{functions_desc}\n\n" \
                  "[team to complete: describe the technical mechanism in prose, independent of the code itself]."
    claims_draft = "Draft Claims (attorney must rewrite — this is placeholder scaffolding only)\n\n" \
                   "1. A method comprising: [step one]; [step two]; [step three].\n" \
                   "2. The method of claim 1, wherein [further limitation]."

    draft_id = f"draft-{uuid.uuid4().hex[:8]}"
    DRAFTS[draft_id] = {
        "id": draft_id,
        "scan_id": req.scan_id,
        "format": "md",
        "sections": {
            "title": title,
            "field": field,
            "background": background,
            "claims_draft": claims_draft,
            "description": description,
        },
        "disclaimer": (
            "This is an unreviewed drafting aid, not a filed or filable "
            "document. Route to a registered patent attorney before any "
            "filing decision."
        ),
    }
    log_step(req.scan_id, "provisional_patent_drafter", "draft_generated", output_ref=draft_id)
    return {"draft_id": draft_id, "sections": DRAFTS[draft_id]["sections"]}


@app.get(f"{API}/drafts/{{draft_id}}")
async def get_draft(draft_id: str):
    draft = DRAFTS.get(draft_id)
    if not draft:
        raise HTTPException(404, "draft not found")
    return draft


@app.get(f"{API}/audit/{{scan_id}}")
async def get_audit(scan_id: str):
    scan = SCANS.get(scan_id)
    if not scan:
        raise HTTPException(404, "scan not found")
    return {"steps": scan["audit"]}


@app.get(f"{API}/health")
async def health():
    return {"status": "ok", "seed_patents": len(PATENTS)}
