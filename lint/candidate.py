"""Candidate-file adapter — extract a termination condition (and scope hints) from
a dir candidate file and feed the linter (claude-dir-shell SPEC §2.2/§5.1, §3).

A candidate file is markdown with `## <Section>` headers (SPEC §2.2). This adapter
pulls the `## Termination condition` section and derives the linter's context hints
from the rest of the file, then runs `lint()`. It is the dir-side analogue of the
orchestrator's `fetch.py` (gh JSON -> routing core): real-artifact -> tested core.

Absence of the `## Termination condition` section is itself a gate failure (an
Active Initiative must carry one, SPEC §2.2/§3.4) — reported as `missing`.

Python 3 stdlib only. See lint/README.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from termination_condition import (
    LintResult,
    TerminationConditionInput,
    Verdict,
    lint,
    render as render_lint,
)


def extract_section(text: str, name: str) -> Optional[str]:
    """Return the body of a `## <name>` (or `### <name>`) section, or None if absent.

    Captures everything after the header line until the next markdown header
    (levels 1–3) or end of file.
    """
    pat = re.compile(
        r"^#{2,3}\s+" + re.escape(name) + r"\s*$(.*?)(?=^#{1,3}\s|\Z)",
        re.I | re.M | re.S,
    )
    m = pat.search(text)
    if not m:
        return None
    body = m.group(1).strip()
    return body or None


def _count_list_items(section: Optional[str]) -> int:
    if not section:
        return 0
    return len(re.findall(r"^\s*(?:[-*]|\d+\.)\s+\S", section, re.M))


def parse_candidate(text: str) -> Optional[TerminationConditionInput]:
    """Build a linter input from a candidate file, or None if the termination
    condition section is missing/empty.

    Hints derived from the file (SPEC §2.2):
    - scope_anchored: True when a `## Non-goals` section has ≥1 bullet (scope is
      bounded enough to attribute the condition); None (→ REVIEW) when Non-goals is
      absent — honest, since absence is a separate malformedness, not proof of
      non-attribution.
    - enumerated_deliverables: True when the termination section itself lists ≥2
      items (a closed deliverable checklist, SPEC §3.3).
    """
    term = extract_section(text, "Termination condition")
    if not term:
        return None

    nongoals = extract_section(text, "Non-goals")
    scope_anchored: Optional[bool]
    if nongoals is None:
        scope_anchored = None
    else:
        scope_anchored = _count_list_items(nongoals) >= 1

    enumerated = _count_list_items(term) >= 2
    return TerminationConditionInput(
        text=term,
        scope_anchored=scope_anchored,
        enumerated_deliverables=enumerated,
    )


@dataclass(frozen=True)
class CandidateLintResult:
    missing_termination_condition: bool
    result: Optional[LintResult]   # None iff missing_termination_condition

    @property
    def overall(self) -> Verdict:
        if self.missing_termination_condition:
            return Verdict.FAIL
        assert self.result is not None
        return self.result.overall


def lint_candidate(text: str) -> CandidateLintResult:
    """Parse a candidate file and lint its termination condition (SPEC §3)."""
    inp = parse_candidate(text)
    if inp is None:
        return CandidateLintResult(missing_termination_condition=True, result=None)
    return CandidateLintResult(missing_termination_condition=False, result=lint(inp))


def render(cl: CandidateLintResult) -> str:
    if cl.missing_termination_condition:
        return ("Termination-condition lint: FAIL\n"
                "  [fail  ] present: no `## Termination condition` section found — "
                "an Active Initiative must carry one (SPEC §2.2/§3.4)")
    assert cl.result is not None
    return render_lint(cl.result)


if __name__ == "__main__":
    good = """---
domain: product-development
---
## Summary
Redesign onboarding.

## Termination condition
New-user activation rate >= 40% measured over any trailing 14-day window.

## Non-goals
- Does not cover billing onboarding.
- Does not change the marketing site.
"""
    print("### good candidate")
    print(render(lint_candidate(good)))
    print()
    missing = "## Summary\nSomething.\n\n## Non-goals\n- x\n- y\n"
    print("### missing termination condition")
    print(render(lint_candidate(missing)))
