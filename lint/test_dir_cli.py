"""Offline tests for the dir CLI core (dir SPEC §5, §7). Writer/issuer injected."""

import unittest

from dir_cli import run_init_workspace, run_file, build_parser
from filing import Action


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

## Constraints
- Cap effort at one quarter.
"""

CODE_COUPLED = GOOD.replace(
    "New-user activation rate >= 40% measured over any trailing 14-day window, sustained\nfor one full release cycle.",
    "The onboarding PR is merged and all tests pass.",
)

NOW = "2026-06-03T14:32:01Z"


class Collect:
    def __init__(self):
        self.files = {}
    def __call__(self, rel, content):
        self.files[rel] = content


class TestInitWorkspace(unittest.TestCase):
    def test_writes_scaffold(self):
        w = Collect()
        written = run_init_workspace(writer=w)
        self.assertEqual(set(written), {"MISSION.md", ".dir-shell.yml", "initiatives/.gitkeep"})
        self.assertEqual(set(w.files), set(written))


class TestRunFileStandalone(unittest.TestCase):
    def test_good_candidate_files_and_writes_record(self):
        w = Collect()
        res = run_file(GOOD, mode="standalone", target_repo=None, topic="activation rate",
                       now_iso=NOW, existing_batches=set(), writer=w)
        self.assertEqual(res["action"], Action.FILE)
        self.assertTrue(res["filed"])
        self.assertEqual(res["batch_id"], "2026-06-03-activation-rate")
        self.assertEqual(res["initiative_id"], "2026-06-03-activation-rate-01")
        rec = "initiatives/2026-06-03-activation-rate/filed/2026-06-03-activation-rate-01.md"
        self.assertIn(rec, w.files)
        self.assertIn("mode: standalone", w.files[rec])
        self.assertIn("initiative-id: 2026-06-03-activation-rate-01", w.files[rec])
        # candidate + meta archived
        self.assertIn("initiatives/2026-06-03-activation-rate/candidates/01.md", w.files)
        self.assertIn("initiatives/2026-06-03-activation-rate/meta.md", w.files)

    def test_parked_candidate_archived_but_no_record(self):
        w = Collect()
        res = run_file(CODE_COUPLED, mode="standalone", target_repo=None, topic="x",
                       now_iso=NOW, existing_batches=set(), writer=w)
        self.assertEqual(res["action"], Action.PARK)
        self.assertFalse(res["filed"])
        self.assertIn("initiatives/2026-06-03-x/candidates/01.md", w.files)   # archived
        self.assertFalse(any("/filed/" in p for p in w.files))                # no record

    def test_batch_id_deduped(self):
        w = Collect()
        res = run_file(GOOD, mode="standalone", target_repo=None, topic="activation rate",
                       now_iso=NOW, existing_batches={"2026-06-03-activation-rate"}, writer=w)
        self.assertEqual(res["batch_id"], "2026-06-03-activation-rate-2")


class TestRunFileRepo(unittest.TestCase):
    def test_repo_mode_invokes_issuer_and_records_issue(self):
        w = Collect()
        calls = {}
        def issuer(title, body, labels):
            calls["labels"] = labels
            return {"number": 47, "url": "https://github.com/o/n/issues/47"}
        res = run_file(GOOD, mode="repo", target_repo="o/n", topic="activation",
                       now_iso=NOW, existing_batches=set(), writer=w, issuer=issuer)
        self.assertTrue(res["filed"])
        self.assertEqual(calls["labels"], ["initiative"])
        rec = w.files["initiatives/2026-06-03-activation/filed/2026-06-03-activation-01.md"]
        self.assertIn("mode: repo", rec)
        self.assertIn("target-repo: o/n", rec)
        self.assertIn("issue-number: 47", rec)


class TestParser(unittest.TestCase):
    def test_file_parses(self):
        ns = build_parser().parse_args(["file", "cand.md", "--repo", "o/n", "--topic", "t"])
        self.assertEqual(ns.repo, "o/n")
        self.assertEqual(ns.topic, "t")

    def test_init_parses(self):
        ns = build_parser().parse_args(["init-workspace", "./ws"])
        self.assertEqual(ns.path, "./ws")


if __name__ == "__main__":
    unittest.main(verbosity=2)
