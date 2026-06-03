"""Offline tests for the candidate-file adapter (dir SPEC §2.2/§5.1, §3).

No third-party deps. Run with:
    python3 -m unittest discover -s lint -p 'test_*.py'   # from repo root
"""

import unittest

from candidate import (
    extract_section,
    parse_candidate,
    lint_candidate,
)
from termination_condition import Verdict


GOOD = """---
domain: product-development
---
## Summary
Redesign onboarding to lift activation.

## Problem
Activation is low.

## Termination condition
New-user activation rate >= 40% measured over any trailing 14-day window,
sustained for one full release cycle.

## Non-goals
- Does not cover billing onboarding.
- Does not change the marketing site.

## Constraints
- Cap effort at one quarter.
"""

CODE_COUPLED = """## Summary
Refactor onboarding.

## Termination condition
The onboarding redesign PR is merged and all tests pass.

## Non-goals
- Not billing.
"""

ENUMERATED = """## Termination condition
The following deliverables exist:
- a published migration guide
- a deprecation notice
- a cutover runbook

## Non-goals
- Not the legacy API.
"""

MISSING = """## Summary
A thing.

## Non-goals
- a
- b
"""

NO_NONGOALS = """## Termination condition
Activation rate >= 40% over a trailing 14-day window.
"""

# Present-but-prose Non-goals + prose Constraints, non-enumerated term: no machine-detectable
# anchor → scope_anchored must be None (REVIEW), NOT False (a fabricated non-attribution).
PROSE_NONGOALS = """## Termination condition
New-user activation rate >= 40% over any trailing 14-day window.

## Non-goals
This initiative does not cover billing onboarding and does not change the marketing site.

## Constraints
Effort is capped at one quarter.
"""

# Prose Non-goals but BULLETED Constraints: Constraints is a valid scope anchor (§3.2 prop 3).
ANCHORED_BY_CONSTRAINTS = """## Termination condition
New-user activation rate >= 40% over any trailing 14-day window.

## Non-goals
This does not cover billing onboarding; it does not change the marketing site.

## Constraints
- Cap effort at one quarter.
"""


class TestExtractSection(unittest.TestCase):
    def test_extracts_named_section(self):
        s = extract_section(GOOD, "Termination condition")
        self.assertIn("activation rate", s.lower())
        self.assertNotIn("Non-goals", s)

    def test_absent_section_is_none(self):
        self.assertIsNone(extract_section(MISSING, "Termination condition"))

    def test_stops_at_next_header(self):
        s = extract_section(GOOD, "Problem")
        self.assertIn("Activation is low", s)
        self.assertNotIn("Termination", s)


class TestParseCandidate(unittest.TestCase):
    def test_good_candidate_parses_with_scope_anchor(self):
        inp = parse_candidate(GOOD)
        self.assertIsNotNone(inp)
        self.assertTrue(inp.scope_anchored)            # Non-goals has bullets
        self.assertFalse(inp.enumerated_deliverables)  # prose threshold, not a list

    def test_enumerated_deliverables_detected(self):
        inp = parse_candidate(ENUMERATED)
        self.assertTrue(inp.enumerated_deliverables)

    def test_missing_section_returns_none(self):
        self.assertIsNone(parse_candidate(MISSING))

    def test_no_nongoals_means_scope_unknown(self):
        inp = parse_candidate(NO_NONGOALS)
        self.assertIsNone(inp.scope_anchored)

    def test_prose_nongoals_is_review_not_false(self):
        # Regression: a present-but-prose Non-goals (no other anchor) must yield None
        # (REVIEW), never a fabricated False (which would falsely FAIL valid input).
        inp = parse_candidate(PROSE_NONGOALS)
        self.assertIsNone(inp.scope_anchored)

    def test_constraints_bullets_anchor_scope(self):
        # SPEC §3.2 property 3: Constraints is a valid scope anchor even if Non-goals is prose.
        inp = parse_candidate(ANCHORED_BY_CONSTRAINTS)
        self.assertTrue(inp.scope_anchored)

    def test_parser_never_fabricates_false(self):
        for fx in (GOOD, CODE_COUPLED, ENUMERATED, NO_NONGOALS, PROSE_NONGOALS,
                   ANCHORED_BY_CONSTRAINTS):
            inp = parse_candidate(fx)
            if inp is not None:
                self.assertIsNot(inp.scope_anchored, False,
                                 "parse_candidate must never assert non-attribution (False)")


class TestLintCandidate(unittest.TestCase):
    def test_good_candidate_passes(self):
        cl = lint_candidate(GOOD)
        self.assertFalse(cl.missing_termination_condition)
        self.assertEqual(cl.overall, Verdict.PASS)

    def test_missing_termination_condition_fails(self):
        cl = lint_candidate(MISSING)
        self.assertTrue(cl.missing_termination_condition)
        self.assertEqual(cl.overall, Verdict.FAIL)

    def test_prose_nongoals_lints_review_not_fail(self):
        # The bug: prose Non-goals produced attributable FAIL → overall FAIL with a false
        # "reviewer indicates not tied" message. It must be REVIEW (honest "ask the human").
        cl = lint_candidate(PROSE_NONGOALS)
        self.assertEqual(cl.overall, Verdict.REVIEW)
        attr = next(p for p in cl.result.properties if p.name == "attributable")
        self.assertEqual(attr.verdict, Verdict.REVIEW)
        self.assertNotIn("not tied", attr.note.lower())

    def test_constraints_anchored_candidate_passes(self):
        cl = lint_candidate(ANCHORED_BY_CONSTRAINTS)
        self.assertEqual(cl.overall, Verdict.PASS)

    def test_code_coupled_candidate_fails(self):
        cl = lint_candidate(CODE_COUPLED)
        self.assertFalse(cl.missing_termination_condition)
        self.assertEqual(cl.overall, Verdict.FAIL)

    def test_no_nongoals_candidate_is_review(self):
        # Valid metric+window condition, but attribution unknown without Non-goals.
        cl = lint_candidate(NO_NONGOALS)
        self.assertEqual(cl.overall, Verdict.REVIEW)


if __name__ == "__main__":
    unittest.main(verbosity=2)
