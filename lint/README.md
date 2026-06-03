# lint/ — dir-shell evaluability + filing tooling (Tier-2)

dir-shell's flat Python module dir. It holds the **termination-condition evaluability
linter** (the assistant to the §3.4 gate), the **candidate-file adapter**, and the
**filing gate + filer** (`filing.py`) — the deterministic, load-bearing core of the
development lifecycle (SPEC §5.4–§5.5): it enforces the dir→eng contract-completeness check
(§4.1) and the non-skippable termination-condition gate, and on pass emits the filed body
(§2.3) and filing record (§7.3). The non-deterministic survival/commitment LLM *reviewers*
(§5.3/§5.4 rubric) and the interactive draft→ground→revise loop are not here — those come
later.

## The linter — a heuristic assistant to the gate

A heuristic **assistant** to the commitment-bar gate (claude-dir-shell [SPEC.md](../SPEC.md)
§3.4) that checks a proposed **termination condition** against the four required properties
(SPEC §3.2): **decidable, code-independent, attributable, bounded**.

## It assists the gate; it does not replace it

The gate is a reviewer/human judgment that records a pass/fail per property plus a written
evaluation procedure (SPEC §3.4). This linter catches the *obvious* failures — the forbidden
forms of SPEC §3.3 — and surfaces what still needs human judgment. So it has a third verdict,
`REVIEW`, and **never auto-passes a property whose truth needs context it can't see**.
A linter `PASS` is advisory; the §3.4 gate ratifies. Aggregation is conservative: overall
`FAIL` if any property fails, `REVIEW` if any needs judgment, `PASS` only if all four pass.

## What it checks

| Property | FAIL when… | PASS when… |
|---|---|---|
| **decidable** | a vague verb (improve/explore/optimize/…) with no threshold/checklist/decision/experiment signal | a numeric threshold, enumerated deliverables, a decision-recorded form, or an experiment-concluded form is present |
| **code_independent** | a code-coupled form ("PR merged", "tests pass", "refactored", "code reviewed", a code path / `:L` line ref) | no code-coupled form detected |
| **attributable** | reviewer hint `scope_anchored=False` | reviewer hint `scope_anchored=True`; **`REVIEW`** when the hint is omitted (attribution needs the Initiative's Non-goals / enumerated deliverables, which the text alone doesn't reveal) |
| **bounded** | an unbounded marker (forever/ongoing/continuously/…) with no window/closed set | a window (over N days/weeks/release/cycle, by `YYYY-MM-DD`) or an enumerated deliverable set |

## Candidate-file adapter (`candidate.py`)

`candidate.py` is the dir-side analogue of the orchestrator's `fetch.py` (real artifact →
tested core). It extracts the `## Termination condition` section from a candidate file
(SPEC §2.2/§5.1) and derives the linter's hints from the rest of the file:

- `parse_candidate(text)` → `TerminationConditionInput | None` (None when the section is
  absent). `scope_anchored` ← whether `## Non-goals` has ≥1 bullet (None → REVIEW when
  Non-goals is absent); `enumerated_deliverables` ← whether the termination section lists
  ≥2 items.
- `lint_candidate(text)` → `CandidateLintResult` (`missing_termination_condition` → overall
  FAIL, per SPEC §2.2/§3.4; otherwise the `LintResult`).

```sh
cd lint && python3 candidate.py    # demo: good candidate + missing-section candidate
```

## Filing gate + filer (`filing.py`)

The deterministic core of the development lifecycle (SPEC §5.4–§5.5). Given a developed
candidate, it decides whether the Initiative may be filed and, if so, emits the artifacts.

- `evaluate_for_filing(text, at_cap=False)` → `FilingDecision` with an `Action`:
  - **`FILE`** — contract-complete (§4.1) and all four termination-condition properties
    confirmed (§3.4).
  - **`PARK`** — the termination condition itself is invalid (an intrinsic property —
    decidable / code-independent / bounded — fails, or the section is missing). **Never
    filed**, even `at_cap` (§3.4/§5.5).
  - **`NEEDS_REVIEW`** — an intrinsic property is *unconfirmed* (linter `REVIEW`), or a
    commitment-readiness concern remains; the human §3.4 gate must ratify. Not auto-filed.
  - **`FILE_WITH_CONCERNS`** — `at_cap=True` and only *readiness* concerns remain (the
    termination condition is valid): filed with an `## Unresolved concerns` note (§5.5).
  - **`BLOCKED_INCOMPLETE`** — a contract-required field is missing (§4.1).
- `file_candidate(text, …, mode, issuer=None)` → `FilingResult`. **standalone**: returns the
  §7.3 filing record (caller writes it under `filed/`). **repo**: calls the injected
  `issuer(title, body, ["initiative"])` (e.g. `gh issue create` — Active immediately, no
  `status:*`, §2.3) and records the Issue number/url. `build_filed_body` renders the §2.3
  canonical order; `build_filing_record` renders the §7.3 record.

The LLM review steps and the interactive draft→ground→revise loop (§5.1–§5.3) are **not**
implemented here — only the parts that must hold mechanically (the contract + the gate).

## `dir` CLI + workspace scaffolder (`dir_cli.py`, `workspace.py`, `bin/dir`)

Makes filing runnable end-to-end against a workspace (SPEC §5, §7).

```sh
./bin/dir init-workspace ./planning           # scaffold the §7.1 standalone layout
./bin/dir file ./planning/cand.md --workspace ./planning --topic "activation rate"
#   standalone → writes initiatives/<batch>/filed/<id>.md  (§7.3 record)
#   --repo owner/name → repo mode: `gh issue create` (Active, label `initiative`),
#       which `orch evaluate` then surfaces as an R1 handoff (the cross-shell demo)
```

- `workspace.py` — pure §7.3 IDs (`make_batch_id`/`dedupe_batch_id`/`candidate_id`/
  `initiative_id`), the §7.2 `.dir-shell.yml` loader, and the §7.1 scaffold contents.
- `dir_cli.py` — `run_init_workspace` / `run_file` take an injected `writer` (and
  `issuer`/clock), so the flow is offline-tested without the filesystem or `gh`; `main`
  wires the real IO. A PARKed candidate is still archived as a workspace draft (§5.5); the
  filed record is written only on FILE / FILE_WITH_CONCERNS.

## Usage

```python
from termination_condition import TerminationConditionInput, lint, render
print(render(lint(TerminationConditionInput(
    "New-user activation rate >= 40% over any trailing 14-day window.",
    scope_anchored=True))))
```

`TerminationConditionInput(text, scope_anchored=None, enumerated_deliverables=False)`:
- `text` — the termination-condition statement.
- `scope_anchored` — reviewer's confirmation it's tied to this Initiative's scope (True /
  False / None=unknown→REVIEW).
- `enumerated_deliverables` — set True when the condition is a closed deliverable checklist
  (supports decidable + bounded without a numeric threshold).

## Verify

```sh
python3 -m unittest discover -s lint -p 'test_*.py'   # from repo root — 62 tests
cd lint && python3 -m unittest test_termination_condition -v   # linter (19)
cd lint && python3 -m unittest test_candidate -v               # candidate adapter (11)
cd lint && python3 -m unittest test_filing -v                  # filing gate + filer (15)
cd lint && python3 -m unittest test_workspace -v               # IDs / config / scaffold (10)
cd lint && python3 -m unittest test_dir_cli -v                 # CLI core, injected IO (7)
cd lint && python3 termination_condition.py                    # linter demo
cd lint && python3 candidate.py                                # candidate demo
```

`test_filing.py` (15) pins the gate (good→FILE; missing field→BLOCKED_INCOMPLETE; missing/
code-coupled termination→PARK, never filed even at cap; unconfirmed→NEEDS_REVIEW), the §2.3
body order + provenance footer + `## Unresolved concerns`, the §7.3 record (standalone vs
repo), and `file_candidate` (standalone record; repo-mode injected `issuer`; parked → no
artifacts).

`test_termination_condition.py` (19) pins: the SPEC §3.2/§3.3 good example (PASS with a scope
hint; REVIEW without — honest about attribution), each forbidden form failing the right
property, threshold/window/decision/enumerated forms passing, the scope-hint behavior,
conservative aggregation, and validation. `test_candidate.py` (11) pins section extraction,
hint derivation, missing-section → FAIL, and a parse→lint end-to-end path.

## Known limitations

Heuristic on text — it cannot truly judge "decidable" or "bounded"; it catches the common
failure phrasings and otherwise returns `REVIEW`. The real gate remains the human/reviewer
judgment (SPEC §3.4). Regex tuning points: `_CODE_DEPENDENT`, `_VAGUE_VERB`, `_UNBOUNDED`,
`_WINDOW`, `_THRESHOLD`.

## Notes

- **Provisional Python 3 stdlib** (consistent with the orchestrator `routing/` and res
  `validation/` units; zero deps; offline-testable). Reversible.
- A thin adapter to extract the `## Termination condition` section from a candidate file and
  feed this linter is left for when the dir development flow ships (SPEC §5).
