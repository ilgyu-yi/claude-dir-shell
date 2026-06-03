"""Initiative filing gate + filer (claude-dir-shell SPEC §4, §5.4–§5.5, §2.3, §7.3).

The deterministic, load-bearing core of the development lifecycle (§5): given a
developed candidate, decide whether it may be FILED, and if so emit the filed
Initiative body (§2.3) and the filing record (§7.3). The LLM survival/commitment
*reviewers* (§5.3/§5.4 rubric) are non-deterministic and live elsewhere; this module
enforces the parts that must hold mechanically:

  - the dir→eng **contract completeness** check (§4.1: required fields present), and
  - the **non-skippable termination-condition evaluability gate** (§3.4) — an Initiative
    with an invalid termination condition is **never filed**; it is PARKED (§5.5).

Reuses the termination-condition linter (`candidate.py` / `termination_condition.py`).
Filesystem writes and `gh issue create` are kept out (injected `issuer`) so this is
pure and offline-testable.

Python 3 stdlib only. See lint/README.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from candidate import extract_section, lint_candidate
from termination_condition import Verdict


# Fields the dir→eng contract requires in a filed Initiative (§4.1 + §2.2 required).
# Domain may come from frontmatter (`domain:`) or a `## Domain` section.
REQUIRED_SECTIONS = (
    "Summary", "Problem", "Current state", "MISSION fit",
    "Termination condition", "Non-goals", "Constraints",
)
# Termination-condition properties that are INTRINSIC to the condition (§3.2): if any
# of these fail, the condition itself is invalid → PARK (§5.5). `attributable` depends
# on scope/Non-goals → treated as a commitment-readiness concern, not an intrinsic fault.
_INTRINSIC_PROPS = ("decidable", "code_independent", "bounded")

_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


class Action(str, Enum):
    FILE = "file"                          # passes the gate → emit body + record (§5.4)
    PARK = "park"                          # termination condition invalid → never file (§3.4/§5.5)
    FILE_WITH_CONCERNS = "file_with_concerns"  # only readiness concerns at cap (§5.5 first bullet)
    NEEDS_REVIEW = "needs_review"          # linter REVIEW; human gate must ratify (§3.4)
    BLOCKED_INCOMPLETE = "blocked_incomplete"  # missing a contract-required field (§4.1)


@dataclass(frozen=True)
class FilingDecision:
    action: Action
    reasons: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()


def _domain(text: str) -> Optional[str]:
    m = _FRONTMATTER.search(text)
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            if k.strip().lower() == "domain" and v.strip():
                return v.strip().strip("'\"")
    sec = extract_section(text, "Domain")
    return sec.strip() if sec else None


def _missing_required(text: str) -> tuple[str, ...]:
    missing = [s for s in REQUIRED_SECTIONS if not extract_section(text, s)]
    if _domain(text) is None:
        missing.append("Domain")
    return tuple(missing)


def evaluate_for_filing(text: str, *, at_cap: bool = False) -> FilingDecision:
    """Decide whether a candidate may be filed (§4.1 + §3.4 + §5.5).

    `at_cap=True` models the §5.5 end-of-loop rule: when only commitment-readiness
    concerns remain (the termination condition itself is valid), the Initiative is
    filed with an `## Unresolved concerns` note rather than blocking forever.
    """
    missing = _missing_required(text)
    if missing:
        return FilingDecision(
            Action.BLOCKED_INCOMPLETE,
            reasons=(f"missing contract-required field(s): {', '.join(missing)} (§4.1)",),
            missing_fields=missing,
        )

    cl = lint_candidate(text)
    if cl.missing_termination_condition:
        return FilingDecision(Action.PARK,
                              reasons=("no `## Termination condition` section (§2.2/§3.4)",))

    props = {p.name: p.verdict for p in cl.result.properties}
    intrinsic_fail = [n for n in _INTRINSIC_PROPS if props.get(n) is Verdict.FAIL]
    if intrinsic_fail:
        # The termination condition itself is invalid → never filed (§3.4/§5.5).
        return FilingDecision(
            Action.PARK,
            reasons=tuple(f"termination condition fails `{n}` (§3.2) — parked, never filed"
                          for n in intrinsic_fail),
        )

    intrinsic_review = [n for n in _INTRINSIC_PROPS if props.get(n) is Verdict.REVIEW]
    if intrinsic_review:
        # Not proven invalid, but the linter can't confirm the condition is valid →
        # the human §3.4 gate must ratify. Never auto-file an unconfirmed condition.
        return FilingDecision(
            Action.NEEDS_REVIEW,
            reasons=tuple(f"termination condition `{n}` is unconfirmed — human gate must ratify (§3.4)"
                          for n in intrinsic_review),
        )

    # Intrinsic properties confirmed. Remaining concerns are commitment-readiness (e.g.
    # `attributable` REVIEW/FAIL) — a non-blocking class at the cap (§5.5 first bullet).
    readiness = [p for p in cl.result.properties
                 if p.name not in _INTRINSIC_PROPS and p.verdict is not Verdict.PASS]
    if not readiness:
        return FilingDecision(Action.FILE, reasons=("commitment-bar gate: all four properties pass (§3.4)",))

    if at_cap:
        return FilingDecision(
            Action.FILE_WITH_CONCERNS,
            reasons=tuple(f"unresolved readiness concern on `{p.name}`: {p.note}" for p in readiness),
        )
    return FilingDecision(
        Action.NEEDS_REVIEW,
        reasons=tuple(f"`{p.name}` is {p.verdict.value} — human gate must ratify (§3.4): {p.note}"
                      for p in readiness),
    )


# ---- filed-artifact emission (§2.3 body, §7.3 record) -----------------------

_FILED_ORDER = ("Summary", "Domain", "Problem", "Current state", "MISSION fit",
                "Termination condition", "Success signals", "Non-goals", "Constraints", "Evidence")
_OPTIONAL = {"Success signals", "Evidence"}


@dataclass(frozen=True)
class FilingMeta:
    initiative_id: str
    batch_id: str
    candidate_id: str
    filed_at: str               # ISO-8601; supplied by caller (deterministic tests)
    mode: str                   # "repo" | "standalone"
    domain: Optional[str] = None
    target_repo: Optional[str] = None
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None


def build_filed_body(text: str, *, batch_id: str, candidate_id: str,
                     unresolved_concerns: tuple[str, ...] = ()) -> str:
    """Render the §2.3 filed Initiative body from a candidate, in the canonical order."""
    parts: list[str] = []
    for name in _FILED_ORDER:
        if name == "Domain":
            dom = _domain(text)
            if dom:
                parts.append(f"## Domain\n{dom}")
            continue
        body = extract_section(text, name)
        if body:
            parts.append(f"## {name}\n{body}")
        elif name not in _OPTIONAL:
            # required sections were validated earlier; guard anyway
            parts.append(f"## {name}\n(missing)")
    if unresolved_concerns:
        parts.append("## Unresolved concerns\n" + "\n".join(f"- {c}" for c in unresolved_concerns))
    parts.append(
        f"---\n\n*Filed from batch `{batch_id}`, candidate `{candidate_id}`. "
        f"Audit trail in workspace `initiatives/{batch_id}/`.*"
    )
    return "\n\n".join(parts)


def build_filing_record(meta: FilingMeta, body: str) -> str:
    """Render the §7.3 filing record (YAML frontmatter + filed body)."""
    fm = [
        "---",
        f"initiative-id: {meta.initiative_id}",
        f"batch-id: {meta.batch_id}",
        f"candidate-id: {meta.candidate_id}",
    ]
    if meta.domain:
        fm.append(f"domain: {meta.domain}")
    fm += [
        f"filed-at: {meta.filed_at}",
        f"mode: {meta.mode}",
    ]
    if meta.mode == "repo":
        fm.append(f"target-repo: {meta.target_repo}")
        if meta.issue_number is not None:
            fm.append(f"issue-number: {meta.issue_number}")
        if meta.issue_url:
            fm.append(f"issue-url: {meta.issue_url}")
    fm.append("termination-condition-evaluability: pass")  # always pass for a filed Initiative (§3.4)
    fm.append("---")
    return "\n".join(fm) + "\n\n" + body


def title_of(text: str) -> str:
    """`initiative: <summary first line, <=80 chars>` (§2.3)."""
    summary = extract_section(text, "Summary") or ""
    first = summary.strip().splitlines()[0] if summary.strip() else "untitled"
    first = first.strip()
    if len(first) > 80:
        first = first[:79].rstrip() + "…"
    return f"initiative: {first}"


# issuer(title, body, labels) -> {"number": int, "url": str}  (injected; e.g. gh issue create)
Issuer = Callable[[str, str, list], dict]


@dataclass(frozen=True)
class FilingResult:
    decision: FilingDecision
    title: Optional[str] = None
    body: Optional[str] = None
    record: Optional[str] = None


def file_candidate(text: str, *, batch_id: str, candidate_id: str, initiative_id: str,
                   filed_at: str, mode: str = "standalone", target_repo: Optional[str] = None,
                   at_cap: bool = False, issuer: Optional[Issuer] = None) -> FilingResult:
    """Run the gate and, if fileable, emit the filed body + record (§5.4, §2.3, §7.3).

    standalone mode: returns the filing record (caller writes it under filed/).
    repo mode: calls `issuer` (e.g. gh issue create) and records the Issue number/url.
    Non-fileable decisions (PARK / NEEDS_REVIEW / BLOCKED_INCOMPLETE) return no artifacts.
    """
    decision = evaluate_for_filing(text, at_cap=at_cap)
    if decision.action not in (Action.FILE, Action.FILE_WITH_CONCERNS):
        return FilingResult(decision=decision)

    concerns = decision.reasons if decision.action is Action.FILE_WITH_CONCERNS else ()
    body = build_filed_body(text, batch_id=batch_id, candidate_id=candidate_id,
                            unresolved_concerns=concerns)
    title = title_of(text)

    issue_number = issue_url = None
    if mode == "repo":
        if issuer is None:
            raise ValueError("repo mode requires an `issuer` (e.g. gh issue create)")
        res = issuer(title, body, ["initiative"])  # Active immediately; no status:* (§2.3)
        issue_number, issue_url = res.get("number"), res.get("url")

    meta = FilingMeta(initiative_id=initiative_id, batch_id=batch_id, candidate_id=candidate_id,
                      filed_at=filed_at, mode=mode, domain=_domain(text), target_repo=target_repo,
                      issue_number=issue_number, issue_url=issue_url)
    record = build_filing_record(meta, body)
    return FilingResult(decision=decision, title=title, body=body, record=record)
