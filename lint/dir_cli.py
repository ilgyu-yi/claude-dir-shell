"""`dir` CLI — workspace scaffolder + filing entry point (claude-dir-shell SPEC §5, §7).

Two commands:
  - `dir init-workspace <path>`  — scaffold the §7.1 standalone workspace layout.
  - `dir file <candidate>`       — run the §5.4 filing gate (lint/filing.py) and, on pass,
                                   write the §7.3 record (standalone) or `gh issue create`
                                   (repo mode). Produces an `initiative`-labelled Issue that
                                   `orch evaluate` then surfaces as an R1 handoff.

The core (`run_init_workspace`, `run_file`) takes an injected `writer` (and `issuer`/clock),
so it is offline-testable without touching the filesystem or `gh`. `main` wires the real
filesystem, `gh`, and the clock.

Python 3 stdlib only. See lint/README.md.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Callable, Optional

from filing import Action, file_candidate
from workspace import (
    DirConfig, candidate_id, candidate_relpath, dedupe_batch_id, filing_record_relpath,
    initiative_id, load_dir_config, make_batch_id, meta_md, meta_relpath, scaffold_files,
)

Writer = Callable[[str, str], None]      # (relpath, content) -> None


# ---- init-workspace ---------------------------------------------------------

def run_init_workspace(*, mission_text: Optional[str] = None, writer: Writer) -> list:
    """Write the §7.1 scaffold via `writer`; returns the relpaths written."""
    files = scaffold_files(mission_text=mission_text)
    for rel, content in files.items():
        writer(rel, content)
    return sorted(files)


# ---- file -------------------------------------------------------------------

def run_file(candidate_text: str, *, mode: str, target_repo: Optional[str],
             topic: Optional[str], now_iso: str, existing_batches: set,
             writer: Writer, cand_seq: int = 1, at_cap: bool = False,
             autonomy: str = "paired", issuer=None) -> dict:
    """Filing flow over an injected workspace (SPEC §5.4–§5.5, §7.1–§7.3).

    Always archives the candidate draft + batch meta (so a PARKed candidate remains a
    workspace draft, §5.5). On FILE / FILE_WITH_CONCERNS, also writes the §7.3 record
    (standalone) or files an Issue via `issuer` (repo).
    """
    today = now_iso[:10]
    batch_id = dedupe_batch_id(make_batch_id(today, topic), existing_batches)
    cand_id = candidate_id(cand_seq)
    init_id = initiative_id(batch_id, cand_id)

    written = []
    def _w(rel, content):
        writer(rel, content)
        written.append(rel)

    # Archive the candidate draft + meta regardless of outcome (§5.5).
    _w(candidate_relpath(batch_id, cand_id), candidate_text)
    _w(meta_relpath(batch_id),
       meta_md(mode=mode, target_repo=target_repo, topic=topic, timestamp=now_iso, autonomy=autonomy))

    result = file_candidate(
        candidate_text, batch_id=batch_id, candidate_id=cand_id, initiative_id=init_id,
        filed_at=now_iso, mode=mode, target_repo=target_repo, at_cap=at_cap, issuer=issuer,
    )

    filed = result.decision.action in (Action.FILE, Action.FILE_WITH_CONCERNS)
    if filed:
        _w(filing_record_relpath(batch_id, init_id), result.record)

    return {
        "batch_id": batch_id, "initiative_id": init_id, "mode": mode,
        "action": result.decision.action, "reasons": list(result.decision.reasons),
        "filed": filed, "title": result.title, "written": written,
    }


# ---- real IO wiring ---------------------------------------------------------

def _fs_writer(base: str) -> Writer:
    def w(rel: str, content: str) -> None:
        full = os.path.join(base, rel)
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(content)
    return w


def _gh_issuer(repo: str):
    def issue(title: str, body: str, labels: list) -> dict:
        cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body]
        for lbl in labels:
            cmd += ["--label", lbl]
        url = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
        num = int(url.rstrip("/").split("/")[-1])
        return {"number": num, "url": url}
    return issue


def _existing_batches(workspace: str) -> set:
    d = os.path.join(workspace, "initiatives")
    if not os.path.isdir(d):
        return set()
    return {name for name in os.listdir(d) if os.path.isdir(os.path.join(d, name))}


def _load_config(workspace: str) -> DirConfig:
    p = os.path.join(workspace, ".dir-shell.yml")
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            return load_dir_config(fh.read())
    return DirConfig()


# ---- CLI --------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dir", description="dir-shell: develop & file Initiatives.")
    sub = p.add_subparsers(dest="command", required=True)

    iw = sub.add_parser("init-workspace", help="Scaffold a standalone workspace (SPEC §7.1).")
    iw.add_argument("path", help="Workspace directory to create/populate.")
    iw.add_argument("--mission", default=None, help="Path to a MISSION.md to seed (else a template).")

    fl = sub.add_parser("file", help="Run the filing gate and file an Initiative (SPEC §5.4).")
    fl.add_argument("candidate", help="Path to the candidate file.")
    fl.add_argument("--workspace", default=".", help="Workspace root (default: cwd).")
    fl.add_argument("--topic", default=None, help="Batch topic (else config default / mission-wide).")
    fl.add_argument("--repo", default=None, help="Target repo owner/name → repo mode (else standalone).")
    fl.add_argument("--candidate-seq", type=int, default=1, help="Candidate sequence number (default 1).")
    fl.add_argument("--at-cap", action="store_true", help="Model the §5.5 revision cap (file readiness concerns).")
    return p


def main(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "init-workspace":
        os.makedirs(args.path, exist_ok=True)
        mission_text = None
        if args.mission:
            with open(args.mission, encoding="utf-8") as fh:
                mission_text = fh.read()
        written = run_init_workspace(mission_text=mission_text, writer=_fs_writer(args.path))
        print(f"initialized workspace at {args.path}")
        for rel in written:
            print(f"  + {rel}")
        return 0

    if args.command == "file":
        with open(args.candidate, encoding="utf-8") as fh:
            candidate_text = fh.read()
        cfg = _load_config(args.workspace)
        target_repo = args.repo or cfg.target_repo
        mode = "repo" if target_repo else "standalone"
        topic = args.topic or cfg.default_topic
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        issuer = _gh_issuer(target_repo) if mode == "repo" else None

        res = run_file(
            candidate_text, mode=mode, target_repo=target_repo, topic=topic, now_iso=now_iso,
            existing_batches=_existing_batches(args.workspace), writer=_fs_writer(args.workspace),
            cand_seq=args.candidate_seq, at_cap=args.at_cap, autonomy=cfg.autonomy, issuer=issuer,
        )

        print(f"batch {res['batch_id']} · {res['mode']} · decision={res['action'].value}")
        for r in res["reasons"]:
            print(f"  - {r}")
        for rel in res["written"]:
            print(f"  + {rel}")
        if res["filed"]:
            print(f"FILED: {res['title']}")
            return 0
        print(f"NOT FILED ({res['action'].value}) — candidate archived as a workspace draft.")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
