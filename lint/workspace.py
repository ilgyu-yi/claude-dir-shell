"""Workspace scaffolding, IDs, and config (claude-dir-shell SPEC §7.1–§7.3).

Pure helpers (no filesystem, no clock) so they are offline-testable; the `dir` CLI
(`dir_cli.py`) injects the real filesystem and date. Covers:
  - the §7.1 standalone workspace layout (scaffold file contents),
  - the §7.2 `.dir-shell.yml` config (minimal loader; no PyYAML),
  - the §7.3 ID scheme (batch-id / candidate-id / initiative-id) + record path.

Python 3 stdlib only. See lint/README.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# ---- §7.3 IDs ---------------------------------------------------------------

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def slugify(text: Optional[str]) -> str:
    """Kebab-case slug; empty/None → 'mission-wide' (SPEC §7.3)."""
    if not text:
        return "mission-wide"
    s = _SLUG_STRIP.sub("-", text.strip().lower()).strip("-")
    return s or "mission-wide"


def make_batch_id(date_iso: str, topic: Optional[str]) -> str:
    """`<ISO-date>-<kebab-slug>` (SPEC §7.3). `date_iso` like '2026-06-03'."""
    return f"{date_iso}-{slugify(topic)}"


def dedupe_batch_id(base: str, existing: set) -> str:
    """Append -2, -3, … on collision within the workspace (SPEC §7.3)."""
    if base not in existing:
        return base
    n = 2
    while f"{base}-{n}" in existing:
        n += 1
    return f"{base}-{n}"


def candidate_id(n: int) -> str:
    """Zero-padded sequence, min 2 digits (SPEC §7.3)."""
    if n < 1:
        raise ValueError("candidate sequence starts at 1")
    return f"{n:02d}"


def initiative_id(batch_id: str, cand_id: str) -> str:
    return f"{batch_id}-{cand_id}"


def filing_record_relpath(batch_id: str, init_id: str) -> str:
    return f"initiatives/{batch_id}/filed/{init_id}.md"


def candidate_relpath(batch_id: str, cand_id: str) -> str:
    return f"initiatives/{batch_id}/candidates/{cand_id}.md"


def meta_relpath(batch_id: str) -> str:
    return f"initiatives/{batch_id}/meta.md"


def meta_md(*, mode: str, target_repo: Optional[str], topic: Optional[str],
            timestamp: str, autonomy: str) -> str:
    """Content of a batch `meta.md` (SPEC §7.1)."""
    return (
        f"# batch meta\n\n"
        f"- mode: {mode}\n"
        f"- target-repo: {target_repo or '(standalone)'}\n"
        f"- topic: {topic or 'mission-wide'}\n"
        f"- created-at: {timestamp}\n"
        f"- autonomy: {autonomy}\n"
    )


# ---- §7.2 config ------------------------------------------------------------

@dataclass(frozen=True)
class DirConfig:
    target_repo: Optional[str] = None
    default_topic: Optional[str] = None
    default_n_candidates: int = 5
    autonomy: str = "paired"


_COMMENT = re.compile(r"\s+#.*$")
_BOOL = {"true": True, "false": False}


def _scalar(v: str) -> Optional[str]:
    v = _COMMENT.sub("", v).strip().strip("'\"")
    if v == "" or v.lower() in ("null", "~", "none"):
        return None
    return v


def load_dir_config(text: str) -> DirConfig:
    """Parse `.dir-shell.yml` (SPEC §7.2). Minimal flat loader; unknown keys ignored."""
    target_repo = default_topic = None
    n = 5
    autonomy = "paired"
    for raw in text.splitlines():
        line = _COMMENT.sub("", raw).rstrip()
        if not line.strip() or ":" not in line or line[:1] in "# ":
            # skip blanks, comments, and indented (nested) lines — §7.2 is flat
            if line[:1] == " ":
                continue
            if not line.strip() or ":" not in line:
                continue
        key, _, val = line.partition(":")
        key = key.strip()
        if key == "target_repo":
            target_repo = _scalar(val)
        elif key == "default_topic":
            default_topic = _scalar(val)
        elif key == "default_n_candidates":
            s = _scalar(val)
            if s and s.isdigit():
                n = int(s)
        elif key == "autonomy":
            autonomy = _scalar(val) or "paired"
    return DirConfig(target_repo=target_repo, default_topic=default_topic,
                     default_n_candidates=n, autonomy=autonomy)


# ---- §7.1 scaffold ----------------------------------------------------------

MISSION_TEMPLATE = """# MISSION

<!-- The planning anchor for this standalone workspace (SPEC §2.2 / §7.4). dir-shell
     develops Initiatives that serve a section of this MISSION. Replace this with the
     actual direction. In repo mode the target repo's MISSION.md is used instead. -->

## Direction

(state the direction this workspace plans toward)

## Success looks like

- (observable, planning-tier success criteria — the kind an Initiative's termination
  condition can be evaluated against without reading code)
"""

DIR_CONFIG_TEMPLATE = """# .dir-shell.yml — workspace config (SPEC §7.2)
target_repo:                 # owner/name; leave empty for standalone mode
default_topic:               # null = mission-wide
default_n_candidates: 5      # batch-mode candidate count (§12)
autonomy: paired             # paired | assisted | auto (§5.2)
"""


def scaffold_files(mission_text: Optional[str] = None) -> dict:
    """Relative-path → content for a fresh standalone workspace (SPEC §7.1).

    Creates MISSION.md (the standalone anchor), .dir-shell.yml, and keeps the
    initiatives/ tree present via a .gitkeep. The per-batch subtree is created lazily
    at filing time.
    """
    return {
        "MISSION.md": mission_text if mission_text is not None else MISSION_TEMPLATE,
        ".dir-shell.yml": DIR_CONFIG_TEMPLATE,
        "initiatives/.gitkeep": "",
    }
