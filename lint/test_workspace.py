"""Offline tests for workspace IDs / config / scaffold (dir SPEC §7.1–§7.3)."""

import unittest

from workspace import (
    DirConfig, candidate_id, dedupe_batch_id, filing_record_relpath, initiative_id,
    load_dir_config, make_batch_id, scaffold_files, slugify,
)


class TestIds(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Activation Rate"), "activation-rate")
        self.assertEqual(slugify("  X/Y & Z!! "), "x-y-z")
        self.assertEqual(slugify(None), "mission-wide")
        self.assertEqual(slugify(""), "mission-wide")

    def test_make_batch_id(self):
        self.assertEqual(make_batch_id("2026-06-03", "activation rate"), "2026-06-03-activation-rate")
        self.assertEqual(make_batch_id("2026-06-03", None), "2026-06-03-mission-wide")

    def test_dedupe(self):
        self.assertEqual(dedupe_batch_id("b", set()), "b")
        self.assertEqual(dedupe_batch_id("b", {"b"}), "b-2")
        self.assertEqual(dedupe_batch_id("b", {"b", "b-2"}), "b-3")

    def test_candidate_id(self):
        self.assertEqual(candidate_id(1), "01")
        self.assertEqual(candidate_id(12), "12")
        with self.assertRaises(ValueError):
            candidate_id(0)

    def test_initiative_id_and_path(self):
        bid = "2026-06-03-activation-rate"
        iid = initiative_id(bid, "01")
        self.assertEqual(iid, "2026-06-03-activation-rate-01")
        self.assertEqual(filing_record_relpath(bid, iid),
                         "initiatives/2026-06-03-activation-rate/filed/2026-06-03-activation-rate-01.md")


class TestConfig(unittest.TestCase):
    def test_parse(self):
        c = load_dir_config("target_repo: o/n\ndefault_topic: ~\ndefault_n_candidates: 7\nautonomy: auto\n")
        self.assertEqual(c.target_repo, "o/n")
        self.assertIsNone(c.default_topic)
        self.assertEqual(c.default_n_candidates, 7)
        self.assertEqual(c.autonomy, "auto")

    def test_defaults_when_empty(self):
        c = load_dir_config("")
        self.assertIsNone(c.target_repo)
        self.assertEqual(c.default_n_candidates, 5)
        self.assertEqual(c.autonomy, "paired")

    def test_comments_and_blank_target(self):
        c = load_dir_config("# header\ntarget_repo:   # empty -> standalone\nautonomy: paired\n")
        self.assertIsNone(c.target_repo)


class TestScaffold(unittest.TestCase):
    def test_default_files(self):
        files = scaffold_files()
        self.assertEqual(set(files), {"MISSION.md", ".dir-shell.yml", "initiatives/.gitkeep"})
        self.assertIn("autonomy: paired", files[".dir-shell.yml"])
        self.assertIn("# MISSION", files["MISSION.md"])

    def test_mission_override(self):
        files = scaffold_files(mission_text="# Custom\n")
        self.assertEqual(files["MISSION.md"], "# Custom\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
