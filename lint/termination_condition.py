"""Termination-condition evaluability linter (claude-dir-shell SPEC §3).

Heuristic ASSISTANT to the commitment-bar gate (SPEC §3.4). It checks a proposed
termination condition against the four required properties (SPEC §3.2):

    1. decidable        - yields a clear done/not-done verdict
    2. code_independent - assessable without reading source code
    3. attributable     - tied to this Initiative's scope
    4. bounded          - a reachable, stably-true end-state (not a treadmill)

IMPORTANT: this linter does NOT replace the gate. The gate is a reviewer/human
judgment that must record a pass/fail per property and a written evaluation
procedure (SPEC §3.4). The linter catches *obvious* failures (the forbidden forms
of SPEC §3.3) and surfaces what still needs human judgment. It therefore returns
a third verdict, REVIEW, and never auto-passes a property whose truth depends on
context it cannot see (e.g. attribution needs the Initiative's Non-goals /
enumerated deliverables). A linter PASS still requires the human gate to ratify.

No third-party dependencies; Python 3 stdlib only. See lint/README.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Verdict(str, Enum):
    PASS = "pass"        # heuristically satisfies the property
    FAIL = "fail"        # heuristically violates the property (an obvious forbidden form)
    REVIEW = "review"    # cannot decide from the text alone — needs the human gate


# ---- property 2: code-dependent forms (SPEC §3.3 "may not be") --------------
# These require code knowledge to evaluate and belong below the contract boundary.
_LINKING = r"(?:is\s+|was\s+|are\s+|has\s+been\s+|have\s+been\s+|been\s+)?"
_CODE_DEPENDENT = re.compile(
    r"\b("
    r"pr\s+" + _LINKING + r"merged|pull\s+request\s+" + _LINKING + r"merged|merge\s+the\s+pr|"
    r"tests?\s+(?:pass|passing|green)|test\s+suite|all\s+tests|"
    r"refactor(?:ed|ing)?|"
    r"code\s+review(?:ed)?|"
    r"ci\s+(?:green|pass(?:es|ing)?)|build\s+(?:pass(?:es|ing)?|green)|"
    r"(?:code\s+)?coverage|lint(?:ing|s|ed)?\s+pass|"
    r"function\s+\w+|class\s+\w+\s+(?:added|removed|refactored)|"
    r"endpoint\s+implemented"
    r")\b",
    re.I,
)
# code paths / line refs (a source-file citation is inherently code-coupled)
_CODE_PATH = re.compile(r"(?<![\w./])[\w./\-]+\.(?:py|js|ts|go|rs|java|rb|c|cc|cpp|sh)\b", re.I)
_LINE_REF = re.compile(r":L\d+\b")

# ---- property 1: vague / non-decidable verbs without a target ---------------
_VAGUE_VERB = re.compile(
    r"\b(improve|explore|investigate|enhance|optimi[sz]e|better|strengthen|"
    r"streamline|moderni[sz]e|research|understand|look\s+into|work\s+on|"
    r"make\s+\w+\s+(?:faster|better|easier|simpler))\b",
    re.I,
)
# concrete decidability signals
_THRESHOLD = re.compile(
    r"(≥|≤|>=|<=|>|<|=|\bat\s+least\b|\bno\s+more\s+than\b|\bunder\b|\bbelow\b|"
    r"\babove\b|\bexactly\b|\bat\s+most\b)\s*\d|\b\d+(\.\d+)?\s*%|\bp\d{2,3}\b",
    re.I,
)
_DECISION_FORM = re.compile(
    r"\b(decision\s+" + _LINKING + r"(?:recorded|reached|documented)|decided\s+(?:and\s+)?recorded)\b", re.I)
_EXPERIMENT_FORM = re.compile(r"\b(experiment\s+(?:concluded|run|completed)|pre-?registered|verdict\s+against)\b", re.I)
_CHECKLIST_FORM = re.compile(r"\b(all\s+of\b|each\s+of\b|the\s+following\s+\w+\s+exist|checklist|every\s+\w+\s+(?:responds|exists|published))\b", re.I)

# ---- property 4: unbounded / treadmill markers ------------------------------
_UNBOUNDED = re.compile(
    r"\b(forever|ongoing|on\s+an\s+ongoing\s+basis|continuously|continual(?:ly)?|"
    r"always|perpetual(?:ly)?|indefinitely|at\s+all\s+times|keep\s+\w+ing)\b",
    re.I,
)
# bound / window signals
_WINDOW = re.compile(
    r"\b(over|within|trailing|for)\b[^.]*\b("
    r"day|days|week|weeks|month|months|quarter|quarters|release|releases|"
    r"cycle|cycles|window|sprint|sprints"
    r")\b|\bby\s+\d{4}-\d{2}-\d{2}\b|\bby\s+(?:end\s+of\s+)?\w+\s+\d{4}\b",
    re.I,
)


@dataclass(frozen=True)
class TerminationConditionInput:
    """What the linter inspects. `text` is the termination-condition statement.
    Hints carry the small bits of context the text alone cannot reveal — supplied
    by the reviewer when known; left None to get an honest REVIEW."""

    text: str
    # Is the condition tied to the Initiative's scope (Non-goals / enumerated
    # deliverables)? The reviewer knows this from the rest of the Initiative.
    scope_anchored: Optional[bool] = None
    # Is the condition expressed as a closed/enumerated deliverable set? (helps
    # bounded + decidable when there is no numeric threshold)
    enumerated_deliverables: bool = False


@dataclass(frozen=True)
class PropertyResult:
    name: str
    verdict: Verdict
    note: str


@dataclass(frozen=True)
class LintResult:
    overall: Verdict
    properties: tuple[PropertyResult, ...]

    def failures(self) -> tuple[PropertyResult, ...]:
        return tuple(p for p in self.properties if p.verdict is Verdict.FAIL)

    def reviews(self) -> tuple[PropertyResult, ...]:
        return tuple(p for p in self.properties if p.verdict is Verdict.REVIEW)


def _decidable(inp: TerminationConditionInput) -> PropertyResult:
    t = inp.text
    has_signal = bool(
        _THRESHOLD.search(t) or _DECISION_FORM.search(t) or _EXPERIMENT_FORM.search(t)
        or _CHECKLIST_FORM.search(t) or inp.enumerated_deliverables
    )
    has_vague = bool(_VAGUE_VERB.search(t))
    if has_vague and not has_signal:
        m = _VAGUE_VERB.search(t)
        return PropertyResult("decidable", Verdict.FAIL,
                              f"vague verb {m.group(0)!r} with no threshold / checklist / decision / "
                              f"experiment signal — not a clear done/not-done verdict")
    if has_signal:
        return PropertyResult("decidable", Verdict.PASS,
                              "a concrete threshold / enumerated / decision / experiment signal is present")
    return PropertyResult("decidable", Verdict.REVIEW,
                          "no obvious vague verb, but also no explicit threshold/checklist — confirm a "
                          "clear done/not-done verdict exists")


def _code_independent(inp: TerminationConditionInput) -> PropertyResult:
    t = inp.text
    m = _CODE_DEPENDENT.search(t) or _CODE_PATH.search(t) or _LINE_REF.search(t)
    if m:
        return PropertyResult("code_independent", Verdict.FAIL,
                              f"code-coupled form {m.group(0)!r} — evaluating it requires reading code "
                              f"(belongs below the contract boundary, SPEC §3.3)")
    return PropertyResult("code_independent", Verdict.PASS,
                          "no code-coupled form detected — appears assessable from observable outcomes")


def _attributable(inp: TerminationConditionInput) -> PropertyResult:
    if inp.scope_anchored is True:
        return PropertyResult("attributable", Verdict.PASS,
                              "reviewer confirms the condition is tied to the Initiative's scope")
    if inp.scope_anchored is False:
        return PropertyResult("attributable", Verdict.FAIL,
                              "reviewer indicates the condition is not tied to this Initiative's scope — "
                              "an unrelated change could satisfy it")
    return PropertyResult("attributable", Verdict.REVIEW,
                          "attribution depends on Non-goals / enumerated deliverables the linter cannot "
                          "see — confirm the condition is scoped to THIS Initiative (pass scope_anchored)")


def _bounded(inp: TerminationConditionInput) -> PropertyResult:
    t = inp.text
    has_window = bool(_WINDOW.search(t) or inp.enumerated_deliverables)
    m = _UNBOUNDED.search(t)
    if m and not has_window:
        return PropertyResult("bounded", Verdict.FAIL,
                              f"unbounded marker {m.group(0)!r} with no window / closed deliverable set — "
                              f"a treadmill, not a reachable end-state")
    if has_window:
        return PropertyResult("bounded", Verdict.PASS,
                              "a window / closed deliverable set bounds the condition to a reachable end-state")
    return PropertyResult("bounded", Verdict.REVIEW,
                          "no unbounded marker, but also no explicit window — confirm the end-state is "
                          "reachable and stably true")


def _aggregate(props: tuple[PropertyResult, ...]) -> Verdict:
    if any(p.verdict is Verdict.FAIL for p in props):
        return Verdict.FAIL
    if any(p.verdict is Verdict.REVIEW for p in props):
        return Verdict.REVIEW
    return Verdict.PASS


def lint(inp: TerminationConditionInput) -> LintResult:
    """Lint a termination condition against the four properties (SPEC §3.2).

    Conservative aggregation: FAIL if any property fails; REVIEW if any needs human
    judgment; PASS only if all four pass. A PASS is advisory — the §3.4 gate ratifies.
    """
    if not inp.text or not inp.text.strip():
        raise ValueError("termination condition text is empty")
    props = (
        _decidable(inp),
        _code_independent(inp),
        _attributable(inp),
        _bounded(inp),
    )
    return LintResult(_aggregate(props), props)


def render(result: LintResult) -> str:
    lines = [f"Termination-condition lint: {result.overall.value.upper()}",
             "(advisory — the SPEC §3.4 commitment-bar gate ratifies; a linter PASS is not the gate)"]
    for p in result.properties:
        lines.append(f"  [{p.verdict.value:6}] {p.name}: {p.note}")
    return "\n".join(lines)


if __name__ == "__main__":
    samples = [
        ("SPEC good example",
         TerminationConditionInput(
             "New-user activation rate >= 40% measured over any trailing 14-day window, "
             "sustained for one full release cycle.",
             scope_anchored=True)),
        ("forbidden: PR merged",
         TerminationConditionInput("The onboarding redesign PR merged and tests pass.",
                                   scope_anchored=True)),
        ("vague, unbounded",
         TerminationConditionInput("Continuously improve onboarding to make it better.",
                                   scope_anchored=True)),
        ("decision form",
         TerminationConditionInput(
             "A vendor decision is recorded with rationale in docs/decisions/vendor.md by 2026-09-30.",
             scope_anchored=True)),
    ]
    for label, s in samples:
        print(f"### {label}")
        print(render(lint(s)))
        print()
