"""Offline tests for the Initiative filing gate + filer (dir SPEC §4, §5.4–§5.5, §2.3, §7.3).

No third-party deps, no gh, no filesystem. Run with:
    python3 -m unittest discover -s lint -p 'test_*.py'   # from repo root
"""

import unittest

from filing import (
    Action,
    evaluate_for_filing,
    build_filed_body,
    build_filing_record,
    file_candidate,
    title_of,
    FilingMeta,
)


GOOD = """---
domain: product-development
---
## Summary
Lift new-user activation via an onboarding redesign.

## Problem
Activation is low; three of five recent cohorts stalled at first-value.

## Current state
No guided onboarding exists; analytics dashboard is instrumented.

## MISSION fit
Serves MISSION § "Activation".

## Termination condition
New-user activation rate >= 40% measured over any trailing 14-day window, sustained
for one full release cycle.

## Non-goals
- Does not cover billing onboarding.
- Does not change the marketing site.

## Constraints
- Cap effort at one quarter.
"""

CODE_COUPLED = GOOD.replace(
    "New-user activation rate >= 40% measured over any trailing 14-day window, sustained\nfor one full release cycle.",
    "The onboarding redesign PR is merged and all tests pass.",
)

VAGUE_UNCONFIRMED = GOOD.replace(
    "New-user activation rate >= 40% measured over any trailing 14-day window, sustained\nfor one full release cycle.",
    "Onboarding is in good shape across the funnel.",
)

MISSING_PROBLEM = GOOD.replace("## Problem\nActivation is low; three of five recent cohorts stalled at first-value.\n\n", "")

MISSING_TC = GOOD.replace(
    "## Termination condition\nNew-user activation rate >= 40% measured over any trailing 14-day window, sustained\nfor one full release cycle.\n\n",
    "",
)


class TestGate(unittest.TestCase):
    def test_good_candidate_files(self):
        self.assertEqual(evaluate_for_filing(GOOD).action, Action.FILE)

    def test_missing_required_field_blocks(self):
        d = evaluate_for_filing(MISSING_PROBLEM)
        self.assertEqual(d.action, Action.BLOCKED_INCOMPLETE)
        self.assertIn("Problem", d.missing_fields)

    def test_missing_termination_condition_parks(self):
        # Missing TC is also a missing required field; the gate reports it as incomplete
        # (either way it is never filed). Assert it is NOT fileable.
        d = evaluate_for_filing(MISSING_TC)
        self.assertIn(d.action, (Action.PARK, Action.BLOCKED_INCOMPLETE))
        self.assertNotIn(d.action, (Action.FILE, Action.FILE_WITH_CONCERNS))

    def test_code_coupled_termination_parks(self):
        d = evaluate_for_filing(CODE_COUPLED)
        self.assertEqual(d.action, Action.PARK)
        self.assertTrue(any("code_independent" in r for r in d.reasons))

    def test_unconfirmed_termination_needs_review_not_file(self):
        # "in good shape" — no threshold/forbidden-form → decidable REVIEW (intrinsic).
        d = evaluate_for_filing(VAGUE_UNCONFIRMED)
        self.assertEqual(d.action, Action.NEEDS_REVIEW)

    def test_park_is_never_filed_even_at_cap(self):
        # §5.5: an invalid termination condition is never filed, even at the cap.
        d = evaluate_for_filing(CODE_COUPLED, at_cap=True)
        self.assertEqual(d.action, Action.PARK)


class TestFiledBody(unittest.TestCase):
    def test_body_has_canonical_order_and_footer(self):
        body = build_filed_body(GOOD, batch_id="2026-06-03-activation", candidate_id="01")
        for sec in ("## Summary", "## Domain", "## Problem", "## Current state",
                    "## MISSION fit", "## Termination condition", "## Non-goals", "## Constraints"):
            self.assertIn(sec, body)
        self.assertLess(body.index("## Summary"), body.index("## Termination condition"))
        self.assertLess(body.index("## Termination condition"), body.index("## Non-goals"))
        self.assertIn("product-development", body)          # domain rendered from frontmatter
        self.assertIn("Filed from batch `2026-06-03-activation`", body)

    def test_unresolved_concerns_appended(self):
        body = build_filed_body(GOOD, batch_id="b", candidate_id="01",
                                unresolved_concerns=("readiness: tighten Non-goals",))
        self.assertIn("## Unresolved concerns", body)
        self.assertIn("tighten Non-goals", body)

    def test_title(self):
        self.assertEqual(title_of(GOOD), "initiative: Lift new-user activation via an onboarding redesign.")


class TestFilingRecord(unittest.TestCase):
    def test_standalone_record(self):
        meta = FilingMeta(initiative_id="b-01", batch_id="b", candidate_id="01",
                          filed_at="2026-06-03T14:00:00Z", mode="standalone")
        rec = build_filing_record(meta, "BODY")
        self.assertIn("initiative-id: b-01", rec)
        self.assertIn("mode: standalone", rec)
        self.assertIn("termination-condition-evaluability: pass", rec)
        self.assertNotIn("target-repo:", rec)
        self.assertTrue(rec.endswith("BODY"))

    def test_repo_record_has_issue_fields(self):
        meta = FilingMeta(initiative_id="b-01", batch_id="b", candidate_id="01",
                          filed_at="2026-06-03T14:00:00Z", mode="repo",
                          target_repo="o/n", issue_number=47, issue_url="https://x/47")
        rec = build_filing_record(meta, "BODY")
        self.assertIn("target-repo: o/n", rec)
        self.assertIn("issue-number: 47", rec)
        self.assertIn("issue-url: https://x/47", rec)


class TestFileCandidate(unittest.TestCase):
    def test_standalone_returns_record_and_body(self):
        r = file_candidate(GOOD, batch_id="b", candidate_id="01", initiative_id="b-01",
                           filed_at="2026-06-03T14:00:00Z", mode="standalone")
        self.assertEqual(r.decision.action, Action.FILE)
        self.assertIsNotNone(r.record)
        self.assertTrue(r.title.startswith("initiative: "))
        self.assertIn("mode: standalone", r.record)
        self.assertIn("domain: product-development", r.record)   # §7.3 record carries domain

    def test_repo_mode_invokes_issuer(self):
        calls = {}
        def issuer(title, body, labels):
            calls["title"], calls["labels"] = title, labels
            return {"number": 99, "url": "https://github.com/o/n/issues/99"}
        r = file_candidate(GOOD, batch_id="b", candidate_id="01", initiative_id="b-01",
                           filed_at="2026-06-03T14:00:00Z", mode="repo", target_repo="o/n",
                           issuer=issuer)
        self.assertEqual(calls["labels"], ["initiative"])      # Active immediately, no status:* (§2.3)
        self.assertIn("issue-number: 99", r.record)
        self.assertIn("issue-url: https://github.com/o/n/issues/99", r.record)

    def test_repo_mode_requires_issuer(self):
        with self.assertRaises(ValueError):
            file_candidate(GOOD, batch_id="b", candidate_id="01", initiative_id="b-01",
                           filed_at="t", mode="repo", target_repo="o/n", issuer=None)

    def test_parked_candidate_emits_no_artifacts(self):
        r = file_candidate(CODE_COUPLED, batch_id="b", candidate_id="01", initiative_id="b-01",
                           filed_at="t", mode="standalone")
        self.assertEqual(r.decision.action, Action.PARK)
        self.assertIsNone(r.record)
        self.assertIsNone(r.body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
