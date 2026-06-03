"""Offline tests for the termination-condition evaluability linter (dir SPEC §3).

No third-party deps, no network. Run with:
    python3 -m unittest discover -s lint -p 'test_*.py'   # from repo root
    cd lint && python3 -m unittest test_termination_condition -v
"""

import unittest

from termination_condition import (
    TerminationConditionInput,
    Verdict,
    lint,
)


def verdict_of(result, prop_name):
    for p in result.properties:
        if p.name == prop_name:
            return p.verdict
    raise AssertionError(f"no property {prop_name}")


class TestGoodExample(unittest.TestCase):
    def test_spec_good_example_passes_with_scope_hint(self):
        # SPEC §3.2/§3.3 canonical metric-threshold example.
        inp = TerminationConditionInput(
            "New-user activation rate >= 40% measured over any trailing 14-day window, "
            "sustained for one full release cycle.",
            scope_anchored=True,
        )
        r = lint(inp)
        self.assertEqual(verdict_of(r, "decidable"), Verdict.PASS)
        self.assertEqual(verdict_of(r, "code_independent"), Verdict.PASS)
        self.assertEqual(verdict_of(r, "attributable"), Verdict.PASS)
        self.assertEqual(verdict_of(r, "bounded"), Verdict.PASS)
        self.assertEqual(r.overall, Verdict.PASS)

    def test_good_example_without_scope_hint_is_review_not_pass(self):
        # Honest: attribution can't be judged from the text alone.
        inp = TerminationConditionInput(
            "New-user activation rate >= 40% over any trailing 14-day window.")
        r = lint(inp)
        self.assertEqual(verdict_of(r, "attributable"), Verdict.REVIEW)
        self.assertEqual(r.overall, Verdict.REVIEW)


class TestCodeIndependentFailures(unittest.TestCase):
    def test_pr_merged_fails(self):
        r = lint(TerminationConditionInput("The redesign PR is merged.", scope_anchored=True))
        self.assertEqual(verdict_of(r, "code_independent"), Verdict.FAIL)
        self.assertEqual(r.overall, Verdict.FAIL)

    def test_tests_pass_fails(self):
        r = lint(TerminationConditionInput("All tests pass on the new module.", scope_anchored=True))
        self.assertEqual(verdict_of(r, "code_independent"), Verdict.FAIL)

    def test_refactored_fails(self):
        r = lint(TerminationConditionInput("The auth module is refactored.", scope_anchored=True))
        self.assertEqual(verdict_of(r, "code_independent"), Verdict.FAIL)

    def test_code_reviewed_fails(self):
        r = lint(TerminationConditionInput("The change is code reviewed and approved.", scope_anchored=True))
        self.assertEqual(verdict_of(r, "code_independent"), Verdict.FAIL)

    def test_code_path_fails(self):
        r = lint(TerminationConditionInput("server/handler.py implements the endpoint.", scope_anchored=True))
        self.assertEqual(verdict_of(r, "code_independent"), Verdict.FAIL)


class TestDecidableFailures(unittest.TestCase):
    def test_improve_without_threshold_fails(self):
        r = lint(TerminationConditionInput("Improve onboarding.", scope_anchored=True))
        self.assertEqual(verdict_of(r, "decidable"), Verdict.FAIL)

    def test_explore_fails(self):
        r = lint(TerminationConditionInput("Explore better activation strategies.", scope_anchored=True))
        self.assertEqual(verdict_of(r, "decidable"), Verdict.FAIL)

    def test_vague_verb_with_threshold_passes_decidable(self):
        # "improve ... to >= 40%" — the threshold rescues decidability.
        r = lint(TerminationConditionInput(
            "Improve activation rate to >= 40% over a trailing 14-day window.",
            scope_anchored=True))
        self.assertEqual(verdict_of(r, "decidable"), Verdict.PASS)


class TestBoundedFailures(unittest.TestCase):
    def test_forever_without_window_fails(self):
        r = lint(TerminationConditionInput(
            "Keep p95 latency under 200ms forever.", scope_anchored=True))
        self.assertEqual(verdict_of(r, "bounded"), Verdict.FAIL)

    def test_ongoing_without_window_fails(self):
        r = lint(TerminationConditionInput(
            "Maintain >= 99% uptime on an ongoing basis.", scope_anchored=True))
        self.assertEqual(verdict_of(r, "bounded"), Verdict.FAIL)

    def test_threshold_with_window_is_bounded(self):
        r = lint(TerminationConditionInput(
            "p95 latency < 200ms sustained over one full release cycle.", scope_anchored=True))
        self.assertEqual(verdict_of(r, "bounded"), Verdict.PASS)


class TestAttributable(unittest.TestCase):
    def test_scope_anchored_false_fails(self):
        r = lint(TerminationConditionInput(
            "Activation rate >= 40% over 14 days.", scope_anchored=False))
        self.assertEqual(verdict_of(r, "attributable"), Verdict.FAIL)

    def test_scope_anchored_none_is_review(self):
        r = lint(TerminationConditionInput(
            "Activation rate >= 40% over 14 days."))
        self.assertEqual(verdict_of(r, "attributable"), Verdict.REVIEW)


class TestNonNumericForms(unittest.TestCase):
    def test_decision_form_is_decidable_and_bounded(self):
        r = lint(TerminationConditionInput(
            "A vendor decision is recorded with rationale in the decision log by 2026-09-30.",
            scope_anchored=True))
        self.assertEqual(verdict_of(r, "decidable"), Verdict.PASS)
        self.assertEqual(verdict_of(r, "bounded"), Verdict.PASS)
        self.assertEqual(r.overall, Verdict.PASS)

    def test_enumerated_deliverables_hint_supports_decidable_and_bounded(self):
        r = lint(TerminationConditionInput(
            "The following exist: a migration guide, a deprecation notice, a cutover runbook.",
            scope_anchored=True, enumerated_deliverables=True))
        self.assertEqual(verdict_of(r, "decidable"), Verdict.PASS)
        self.assertEqual(verdict_of(r, "bounded"), Verdict.PASS)
        self.assertEqual(r.overall, Verdict.PASS)


class TestAggregationAndValidation(unittest.TestCase):
    def test_overall_fail_dominates(self):
        # vague + code-coupled + unbounded -> FAIL
        r = lint(TerminationConditionInput(
            "Continuously improve until tests pass.", scope_anchored=True))
        self.assertEqual(r.overall, Verdict.FAIL)
        self.assertGreaterEqual(len(r.failures()), 2)

    def test_empty_text_rejected(self):
        with self.assertRaises(ValueError):
            lint(TerminationConditionInput("   "))


if __name__ == "__main__":
    unittest.main(verbosity=2)
