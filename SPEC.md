# SPEC — claude-dir-shell

Canonical specification for **claude-dir-shell**, the planning tier of the orchestrated
shell system. dir-shell produces **Initiatives**: planning-tier strategic commitments
whose load-bearing property is a **code-independent, evaluable termination condition**.

- **Status**: Specification phase, fresh rewrite. 2026-06-03.
- **Authority**: This SPEC is the source of truth for dir-shell *design*. Progress/state
  is tracked via this repo's Issues and PRs. Where this SPEC and any earlier dir-shell doc
  (the prior 9-phase-pipeline SPEC, ADR-0001) disagree, **this SPEC wins**; the earlier
  docs are retained in git history only.
- **Scope**: the Initiative artifact and its contracts (the headline), dir's development
  lifecycle, dir↔res integration, the dir→eng external contract, modes/substrate, the
  candidate-generation mechanism, post-filing lifecycle, decision record, open items.
  Hooks/enforcement are deferred (§13).

> **Reading order.** §1 (role) → §2 (Initiative artifact) → §3 (termination-condition
> contract — the crux) → §4 (dir→eng contract) → §5 (development lifecycle) → §6 (res
> integration) → the rest. §2–§4 are the contracts other components depend on; treat them
> as frozen interfaces once this SPEC is accepted.

---

## 1. Role in the orchestrated system

The system is three shells coordinated by claude-orch-shell:

```
        MISSION (stated direction; planning-tier SSOT)
            │
   ┌────────▼─────────┐        research request (strategic mode)
   │   dir-shell      │ ───────────────────────────────────────►┐
   │  (planning tier) │ ◄─────────────────────────────────────── │
   └────────┬─────────┘        research document (evidence)      │
            │                                                ┌────▼─────┐
            │ Initiative artifact (the dir→eng contract)     │ res-shell │
            │                                                │ (on-demand│
   ┌────────▼─────────┐        research request (technical)  │ research) │
   │   eng-shell      │ ───────────────────────────────────►│           │
   │ (execution tier) │ ◄───────────────────────────────────└──────────┘
   │   [FROZEN/ext.]  │        research document (evidence)
   └──────────────────┘
```

- **dir produces Initiatives.** An Initiative is a planning-tier strategic commitment,
  filed as an `initiative`-labeled GitHub Issue (repo mode) or a local record (standalone
  mode).
- **dir does not read source code** (§7.4). All grounding comes from planning-tier
  artifacts or from research documents that res produced for dir in **strategic mode**
  (which itself never reads code). This is an invariant, not a guideline.
- **dir and eng connect only through the Initiative artifact** (§4). Neither shell needs
  to know the other exists; claude-orch-shell routes the artifact between them on metadata
  alone. dir's only obligation to eng is to satisfy the §4 contract for every filed
  Initiative.
- **dir calls res as a subroutine** (§6), never the reverse. res returns a document used
  as evidence; res makes no decisions and the call is internal to dir's development of an
  Initiative (claude-orch-shell does not see or route res calls — see claude-orch-shell SPEC).

What dir is **not**: not engineering execution (that's eng-shell), not a code-reading
tool, not a project-management/roadmap tool, not a generic ideation app. dir is scoped to
mission-aligned strategic commitments under critical review, each carrying an evaluable
termination condition.

---

## 2. The Initiative artifact

The Initiative is dir-shell's sole output artifact. Everything else in this SPEC exists to
produce well-formed Initiatives and guarantee their contracts.

### 2.1 Identity and tier

- **Label**: `initiative` (singular, lowercase). Required on every filed Initiative.
- **Tier**: one level above execution. An Initiative parents downstream execution
  artifacts (eng-shell Directives, and analogously experiment-run records, decision
  records, product bets) via the body marker `Parent Initiative: #N`, symmetric to
  eng-shell's `Parent Directive: #N`.
- **Flat tree**: there is **no Initiative-of-Initiatives**. A large commitment splits into
  peer Initiatives, never nested ones.
- **Label exclusivity**: `initiative` and `directive` are mutually exclusive on any one
  Issue. eng-shell's `is_directive_issue` / `is_initiative_issue` predicates depend on
  this (§10, Assumptions about eng-shell).

### 2.2 Required fields (shape)

Every Initiative — candidate draft, filed Issue, or standalone record — carries this
structure. Fields marked **(contract)** are load-bearing for the dir→eng contract (§4) and
may not be empty in a filed Initiative.

| Field | Required | Meaning |
|---|---|---|
| **Title** | yes | `initiative: <summary ≤80 chars>`. |
| **Summary** | yes | One paragraph: the strategic commitment in plain language. |
| **Domain** | yes | One of the four enumerated domains (§8.1). Dispatches the review rubric. |
| **Problem** | yes | The concrete problem, with cited planning-tier evidence (no vacuum-generated claims). |
| **Current state** | yes | Observable present conditions establishing the baseline the Initiative responds to. |
| **MISSION fit** | yes | Which MISSION section / success criterion this serves (one sentence). If MISSION does not cover it, an explicit note that the Initiative may motivate a MISSION amendment. |
| **Termination condition** | yes **(contract)** | The single load-bearing field. A statement that yields a clear done / not-done verdict, assessable **without reading source code** (§3). |
| **Success signals** | optional | Leading indicators of progress (not the gate). Distinct from the termination condition: signals may be partially met while the Initiative is still open. |
| **Non-goals** | yes | ≥2 explicit exclusions. Bounds scope so a future reviewer can adjudicate creep. |
| **Constraints** | yes | ≥1 invariant to preserve (mission alignment, prior commitments, resource bounds, safety/ethical limits). |
| **Evidence** | optional | References to research documents (§6) and planning-tier sources that ground Problem / Current state / Termination condition. |
| **Confidence** | optional | 0–100 self-assessment at filing time. Low values are acceptable; the termination condition must still be evaluable. |

The **Termination condition** is new and primary; **Success signals** is demoted from the
prior spec to an optional leading-indicator field so the two never blur. The gate is the
termination condition alone.

### 2.3 Filed form

**Issue title (repo mode)**: `initiative: <summary ≤80 chars>`.

**Issue body (repo mode) / standalone record body**: the §2.2 fields rendered as markdown
sections in this order — Summary, Domain, Problem, Current state, MISSION fit,
**Termination condition**, Success signals (if any), Non-goals, Constraints, Evidence (if
any), then a provenance footer naming the originating batch/candidate and workspace audit
path (§7.3). When the development loop terminates at its cap with unresolved
commitment-bar concerns (§5.5), an `## Unresolved concerns` section is appended verbatim
from the final review.

**Labels (repo mode)**: `initiative`, and nothing from the `status:*` family — a
pipeline- or development-filed Initiative is **Active immediately** (§9). `status:proposed`
appears only on the manual-filing path (§11).

---

## 3. The termination-condition contract (the crux)

> *The Initiative's reason to exist as a distinct artifact is this contract. eng-shell
> relies on it; dir-shell must guarantee it before filing. If dir cannot produce a
> termination condition meeting all four properties below, the Initiative is not ready to
> file — full stop.*

### 3.1 Definition

A **termination condition** is a written statement that lets an evaluator decide whether
the Initiative is **done**. It is the criterion against which the Initiative's
`Completed` state (§9) is judged.

### 3.2 The four required properties

A termination condition is valid only if it is **all four** of:

1. **Decidable.** It yields a binary done / not-done verdict. "Improve onboarding,"
   "make the system faster," "explore X" are not decidable. "New-user activation rate
   ≥ 40% measured over any trailing 14-day window" is decidable. Open-ended or
   perpetual aspirations are rejected.

2. **Code-independent (observation-based).** The verdict can be reached **without reading
   source code** — from observable outcomes: published metrics, user-visible behavior,
   produced/published artifacts, external world-state, or an explicitly enumerated list of
   deliverables. The evaluator may be a person who has never seen the codebase. This is the
   property that lets dir (which never reads code) author it and lets claude-orch-shell
   route on it without interpreting code.
   - *Heuristic test:* "Could a competent non-engineer with access to the running system,
     its metrics, and its public artifacts decide done/not-done?" If yes → code-independent.
     If deciding requires reading a diff, a test suite, or a function, it fails.

3. **Attributable.** Satisfaction is tied to *this* Initiative's scope (via Non-goals /
   Constraints / enumerated deliverables), so it is unambiguous what work counts toward it
   and what does not. Prevents an unrelated change from "accidentally" satisfying it and
   prevents scope drift from quietly moving the goalposts.

4. **Bounded.** The condition names a reachable end-state, not a treadmill. There exists a
   finite set of outcomes that, once true, are stably true. ("Keep latency low forever" is
   unbounded; "p95 latency < 200ms sustained across one full release cycle" is bounded.)

### 3.3 Forms a termination condition may take

Any of these (or a small conjunction of them) is acceptable so long as §3.2 holds:

- **Metric threshold** — a named metric crosses/holds a stated threshold over a stated
  window. (Most common; inherently observation-based.)
- **Enumerated deliverables** — a closed checklist of observable artifacts/outcomes, each
  individually checkable without code reading (e.g., "a published migration guide exists,"
  "all three partner integrations respond to a documented smoke request").
- **Decision reached** — for `decision-making` Initiatives: a named decision is recorded
  with its rationale in a stated artifact (the artifact's existence + contents is the
  observable).
- **Experiment concluded** — for `experiment-design`/`scientific-methodology`: the
  pre-registered experiment has run and produced a verdict against its pre-registered
  threshold (the verdict, not the code, is the observable).

A termination condition **may not** be: "PR merged," "tests pass," "function refactored,"
"code reviewed" — these require code knowledge to evaluate and belong to eng-shell's
internal Directive/execution layer, below the contract boundary.

### 3.4 How dir guarantees it

The guarantee is procedural, enforced at the **commitment bar** (§5.4):

- The commitment-bar reviewer runs an explicit **evaluability check**: for the proposed
  termination condition, it records a pass/fail against each of the four properties (§3.2)
  with a one-line justification each.
- **Any** property failing blocks filing. The Initiative returns to revision (§5.5).
- The reviewer additionally writes the **evaluation procedure** it would itself use to
  decide done/not-done — a 1–3 step recipe referencing only observables. If the reviewer
  cannot write that procedure without invoking code, property 2 has failed by construction.
- The recorded evaluability check + evaluation procedure are retained in the workspace
  audit trail (§7.3) and the evaluation procedure is carried into the filed Initiative's
  Evidence/Termination sections so a future evaluator inherits it.
- **Tooling assist (advisory, not the gate):** a heuristic linter
  ([`lint/`](lint/), Tier-2) pre-screens a termination condition against the four
  properties and flags the obvious forbidden forms (§3.3) — catching "PR merged"/"tests
  pass" (code-coupled), "improve X" (not decidable), "…forever" (unbounded). It returns
  PASS/FAIL/**REVIEW** and never auto-passes a property needing context it can't see (e.g.
  attribution). The reviewer/human still performs and records the §3.4 judgment; a linter
  PASS is advisory input, not the gate.

This is the *only* gate that may not be skipped, even when the development loop hits its
cap (§5.5): an Initiative with an invalid termination condition is **never filed**. If the
loop caps out with the termination condition still invalid, the candidate is parked
(remains a draft in the workspace, not filed) and the cap-out is logged — contrast with
*other* unresolved concerns, which may be filed with an `## Unresolved concerns` note.

---

## 4. The dir→eng contract (dir's side only)

This section defines, **from dir's side only**, what a filed Initiative must contain so
eng-shell can consume it. eng-shell is a **frozen external system** (§10); this SPEC does
not specify eng's side and must not be read as doing so.

### 4.1 The contract

A filed Initiative that eng may consume **must**:

1. Carry the `initiative` label and **not** the `directive` label (§2.1).
2. Be **Active** (open; no `status:*` label) — see §9.
3. Contain a non-empty, valid **Termination condition** meeting all four §3.2 properties,
   plus its evaluation procedure (§3.4).
4. Contain non-empty **Summary, Problem, Current state, MISSION fit, Non-goals,
   Constraints** (§2.2).
5. Be **self-contained at the planning tier**: everything eng needs to decide *what done
   means* is in the Initiative body; eng never needs to consult dir, the workspace, or
   res to understand the commitment. (eng will, separately and on its own, read code and
   author Directives to *achieve* it — outside this contract.)

### 4.2 What the contract deliberately excludes

dir does **not** specify, and must not put in an Initiative:

- How to implement the commitment (no technical design, no file/module references, no code).
- Directive decomposition (eng owns turning an Initiative into Directives).
- Acceptance criteria phrased in code terms (those live in eng's Directives/Execution
  Issues, below the boundary).

The boundary is exactly the termination condition: dir owns *what done means, observably*;
eng owns *how to get there, in code*.

### 4.3 Linkage

eng-side artifacts reference their parent Initiative with `Parent Initiative: #N` in their
body (the same marker convention eng already uses for `Parent Directive: #N`). dir does not
author or mutate those downstream artifacts; it only files the Initiative they point at.
claude-orch-shell (claude-orch-shell SPEC) uses the `initiative` label + Active state as the
metadata trigger to propose the dir→eng handoff; it never reads the Initiative body.

---

## 5. Initiative development lifecycle

How a single Initiative is developed — typically by a **human + dir pair**, with dir doing
generation, grounding, and critique while the human steers and the bars enforce quality.
The lifecycle is the same whether the candidate originated from single-Initiative
development or from the candidate-generation mechanism (§12); both converge on the same
gates.

### 5.1 Stages

```
draft → ground → review (survival bar) → revise ─┐
  ▲                                               │  (loop until survival-bar pass
  └──────────────── revise ◄─────────────────────┘   or human abandons)
                       │ survival-bar pass
                       ▼
              commitment bar (termination-condition evaluability gate, §3.4)
                       │ pass            │ fail
                       ▼                 ▼
                     FILE            revise → commitment bar  (≤2 cycles; §5.5)
```

1. **Draft** — produce/seed a candidate with the §2.2 fields (a first termination
   condition included, even if rough).
2. **Ground** — back Problem / Current state / Termination condition with planning-tier
   evidence. When grounding needs investigation dir cannot do from planning artifacts
   alone, dir calls **res in strategic mode** (§6) and folds the returned research
   document in as cited Evidence. (Reminder: res in strategic mode never reads code, so
   dir's code-independence invariant is preserved.)
3. **Review (survival bar)** — the reviewer critiques the candidate against the
   domain-dispatched rubric (§8) at the **survival bar**: "is this candidate worth
   developing?" Output: per-axis verdict + `pass` / `revise` / `reject`.
4. **Revise** — address the review; may change framing, domain, success signals, scope,
   and the termination condition. Loop 3↔4 until survival-bar pass (or the human abandons
   the candidate).
5. **Commitment bar** — the gate (§5.4). Enforces the termination-condition contract (§3.4)
   plus commitment-readiness. Pass → file (§2.3, §9). Fail → revise and re-gate, capped.

### 5.2 Human-in-the-loop

- The human chooses topics, abandons candidates, resolves cross-Initiative conflicts, and
  may override a `reject` to keep developing (the override is recorded in the audit trail).
- The human cannot override the **termination-condition evaluability gate** (§3.4): that
  gate protects the dir→eng contract, which is not dir's to waive. A human who disagrees
  must fix the termination condition, not bypass the check.
- **Autonomy degree** is configurable (workspace config, §7.2): `paired` (default — dir
  proposes, human confirms each stage transition), `assisted` (dir advances automatically
  through survival-bar loops, pauses before filing), `auto` (dir runs the full lifecycle
  and files on commitment-bar pass; for batch generation, §12). The termination-condition
  gate is identical in all three.

### 5.3 Survival bar

"Is this candidate worth continued development?" Filters weak/ungrounded candidates early.
Applies the cross-cutting axes (§8.2) and the domain rubric (§8.3) at a screening
threshold. A `reject` here means stop developing (human may override); a `revise` means
loop.

### 5.4 Commitment bar (the filing gate)

Stricter than the survival bar and **mandatory before filing**. It adds two things on top
of the survival-bar rubric:

- The **termination-condition evaluability check** (§3.4) — the non-skippable gate.
- A **commitment-readiness** axis (§8.2): are Non-goals/Constraints sharp enough to bound
  the commitment? Are conflicts with current direction (other Active Initiatives, MISSION)
  resolved or explicitly bracketed?

Verdict: `commit` (file it) or `revise` (return to §5.5). There is no `reject` at the
commitment bar — a candidate that reaches this bar has already passed survival; the only
outcomes are "file" or "keep fixing."

**Tooling (implemented, Tier-2):** the deterministic core of this gate and of filing lives
in [`lint/filing.py`](lint/): `evaluate_for_filing` enforces contract-completeness (§4.1)
and the non-skippable termination-condition gate (PARK on an invalid condition — never
filed, even at the cap; NEEDS_REVIEW on an unconfirmed one), and `file_candidate` emits the
§2.3 filed body + §7.3 record (standalone) or files an Issue via an injected `issuer` (repo).
The survival/commitment-readiness LLM *rubric* judgments (§8) and the interactive draft→
ground→revise steps (§5.1–§5.3) are not yet implemented.

### 5.5 Revision loop and cap

- The commitment-bar→revise→commitment-bar loop is capped at **two cycles** per Initiative
  to avoid infinite polish.
- **At the cap, the termination-condition gate still governs** (§3.4):
  - If the only open issues are *commitment-readiness* concerns (not the termination
    condition), the Initiative **is filed** with an `## Unresolved concerns` section
    recording them for the human/eng to weigh — the pipeline does not block forever.
  - If the *termination condition itself* is still invalid at the cap, the Initiative is
    **not filed**; it is parked as a workspace draft and the cap-out is logged with the
    failing property. Filing an Initiative with an invalid termination condition is never
    permitted.

---

## 6. res integration (strategic mode)

dir calls res-shell as an on-demand subroutine to gather evidence it cannot derive from
planning-tier artifacts alone. This section is dir's side of the dir↔res contract; res's
side is in the res-shell SPEC and **must mirror it**.

### 6.1 When dir calls res

During **grounding** (§5.1 stage 2), and optionally during commitment-bar revision, when:

- the Problem or Current state needs evidence dir cannot get from MISSION/Issues/milestones
  (e.g., "what is the state of the art on X?", "what do comparable products do about Y?",
  "what does the published literature say about approach Z?"), or
- the termination condition needs a defensible threshold ("what activation rate is
  realistic / industry-typical?").

dir does **not** call res for code-derived facts — that would violate dir's
code-independence (§7.4). If a question can only be answered by reading the codebase, it is
out of bounds for a dir-initiated research call; dir reframes it as a planning-tier
question or defers it to eng.

### 6.2 The research request dir issues

dir issues a request with these fields (the contract res consumes):

| Field | Value when dir is the caller |
|---|---|
| `question` | The research question, planning-tier framed. |
| `mode` | **`strategic`** — always, for dir. Fixed by caller identity (§ res SPEC). |
| `caller` | `dir` |
| `context` | Planning-tier context only: relevant MISSION excerpts, the candidate's Problem/Current state, related Initiatives. **Never source code, never file paths into a codebase.** |
| `output_location` | Workspace path where res writes the research document (§7.1, under the batch's `research/`). |

**Mode is fixed by the caller and is `strategic` for every dir call.** dir cannot request
`technical` mode; res enforces that a `strategic` invocation reads no code (res SPEC). A
single research call is one mode throughout — dir never receives a document that mixed in
code-derived findings.

### 6.3 Incorporating the returned document

res returns a **research document** (a file at `output_location`; see res SPEC for its
shape and the strategic-mode contract guaranteeing no code-derived content). dir:

- cites it under the Initiative's **Evidence** field by workspace path + the document's
  title/date,
- may quote specific findings into Problem / Current state / Termination condition, always
  attributed,
- treats it as **evidence for dir's judgment, not a decision** — res decides nothing; dir
  (with the human) decides whether and how the evidence changes the candidate.

The research document is part of the workspace audit trail (§7.3): a future session can see
exactly what evidence informed an Initiative.

---

## 7. Modes and substrate

### 7.1 Workspace layout

The **workspace** is a user-managed local directory, separate from both the dir-shell tool
repo and any target repo. It is the decision-making archive; its git history is the version
log.

```
<workspace>/
  MISSION.md                          # workspace-owned mission (standalone anchor; optional in repo mode)
  .dir-shell.yml                      # workspace config (§7.2)
  initiatives/
    <batch-id>/                       # one development run (single-candidate or batch)
      meta.md                         # mode, target repo, topic, timestamp, autonomy degree
      candidates/
        <candidate-id>.md             # draft; mutated across the lifecycle (§5)
        merged-into/<candidate-id>.md # batch mode only — candidates absorbed by a merge (§12)
      reviews/
        <candidate-id>.survival.md    # survival-bar review(s)
        <candidate-id>.commitment.md  # commitment-bar review + evaluability check (§3.4)
      research/
        <doc-id>.md                   # research documents res produced for this batch (§6)
      rejected/<candidate-id>.md      # batch mode only — screened-out candidates, with reason
      ranking.md                      # batch mode only (§12)
      selection.md                    # batch mode only (§12)
      filed/<initiative-id>.md        # filing record (both modes; §7.3)
```

A **single-Initiative** development run (the primary path, §5) uses only `meta.md`,
`candidates/<id>.md`, `reviews/`, `research/`, and `filed/`. The `merged-into/`,
`rejected/`, `ranking.md`, and `selection.md` artifacts appear **only in batch mode** (§12).
(Renamed `drafts/` → `initiatives/` and added `research/` vs. the prior spec; rationale in
the decision record §14.)

**Tooling (implemented, Tier-2):** [`bin/dir`](bin/dir) + [`lint/dir_cli.py`](lint/) +
[`lint/workspace.py`](lint/). `dir init-workspace <path>` scaffolds this layout (MISSION
anchor + `.dir-shell.yml` + `initiatives/`); `dir file <candidate>` runs the §5.4 gate and
writes the §7.3 record (standalone) or `gh issue create`s an Active `initiative` Issue
(repo). IDs (§7.3) and the config loader (§7.2) are pure/offline-tested; filesystem + `gh`
are injected so the core is tested without them.

### 7.2 Workspace config (`.dir-shell.yml`)

```yaml
target_repo: owner/name      # optional; absent → standalone mode
default_topic: ~             # optional; null = mission-wide
default_n_candidates: 5      # batch-mode candidate count (§12)
autonomy: paired             # paired | assisted | auto (§5.2)
```

CLI flags override config; config overrides built-in defaults.

### 7.3 IDs and the filing record

- `<batch-id>` = `<ISO-date>-<kebab-slug>` (slug = topic, or `mission-wide`). Collisions
  get `-2`, `-3`, … .
- `<candidate-id>` = zero-padded sequence within a batch (`01`, `02`, …).
- `<initiative-id>` = `<batch-id>-<candidate-id>` (persistent local identifier).
- `<doc-id>` = `<ISO-date>-<kebab-slug>` for research documents (§6).

The **filing record** (`filed/<initiative-id>.md`) persists the mapping from local
candidate to filed location:

```yaml
---
initiative-id: 2026-06-03-activation-rate-01
batch-id: 2026-06-03-activation-rate
candidate-id: 01
domain: product-development
filed-at: 2026-06-03T14:32:01Z
mode: repo | standalone
target-repo: owner/name              # repo mode only
issue-number: 47                     # repo mode only
issue-url: https://github.com/owner/name/issues/47  # repo mode only
termination-condition-evaluability: pass   # always pass for a filed Initiative (§3.4)
---

<filed Initiative body — §2.3. Repo mode mirrors the Issue body; standalone IS the body.>
```

### 7.4 Modes (I/O boundary only)

Both modes run the same lifecycle (§5) and substrate; they differ only at the I/O edges.

- **Repo mode** (`--repo owner/name`): MISSION fetched via
  `gh api repos/<owner>/<name>/contents/MISSION.md` (fallback `docs/MISSION.md`; if neither
  exists, halt and prompt for `--mission <path>` or a committed MISSION). Milestones,
  Issues, and existing Initiatives read via `gh`. The target repo is **read-only except**
  for the final `gh issue create` filing. **Never cloned** — accessed by address via `gh`
  only. **dir never reads source code even when it could** — this is an invariant, not a
  consequence of not cloning.
- **Standalone mode** (no `--repo`): the workspace's own `MISSION.md` is the anchor
  (`--mission <path>` overrides per run). Filing writes only the local filing record.

---

## 8. Domains and review rubric

### 8.1 Domains

Every Initiative carries a `domain` ∈ { `scientific-methodology`, `experiment-design`,
`product-development`, `decision-making` }. The domain dispatches the rubric variant and
shapes which termination-condition *form* (§3.3) is expected (e.g., `decision-making` →
"decision reached"; `experiment-design` → "experiment concluded"). Planning work that fits
none of the four is an open item (§15) — for now, pick the nearest and note the misfit in
`meta.md`.

### 8.2 Cross-cutting axes (all domains)

| Axis | Question |
|---|---|
| MISSION fit | Does it serve a concrete MISSION section / success criterion? |
| Context-grounding | Are Problem and Current state cited with planning-tier (or research-document) evidence, not vacuum-generated? |
| Scope clarity | Are Non-goals/Constraints sharp enough to adjudicate scope creep? |
| Framing rigor | Is the problem framed at the right altitude — not platitude, not premature solutioning? |
| **Termination evaluability** *(commitment bar)* | Does the termination condition meet all four §3.2 properties? (The §3.4 gate.) |
| **Commitment-readiness** *(commitment bar)* | Are conflicts with current direction resolved/bracketed; is the commitment bounded and ready? |

### 8.3 Domain rubrics

- **scientific-methodology** — Testability (falsifiable hypotheses / verifiable criteria);
  Rigor (pre-registered thresholds, confounder control, named failure modes);
  Replicability (executable from the body alone, modulo external resources).
- **experiment-design** — Pre-registration discipline (thresholds stated before the run);
  Falsification clarity (what observation refutes it?); Resource bounds (time, sample,
  compute); Reference baseline (prior result / null model).
- **product-development** — Bet sizing (commitment ∝ information; downside framed);
  Market reasoning (demand hypothesis + evidence); Reversibility (one-way vs reversible
  door); Kill criteria (what winds it down?).
- **decision-making** — Framework clarity (options/criteria/weights disclosed);
  Stakeholder map (who is affected; whose buy-in); Reversibility/commitment (Type-1 vs
  Type-2, framing proportional); Information value (what info would change the decision; is
  acquiring it in scope?).

In every domain, the domain rubric's "verifiability"-flavored axis (testability /
falsification clarity / kill criteria / information value) **feeds** the termination
condition: a domain that can't state how it's falsified/killed/decided usually can't state
a decidable termination condition either.

---

## 9. Initiative lifecycle (post-filing)

A filed Initiative is **Active**. Its termination condition (§3) is the criterion for the
`Completed` transition.

| State | Enter | Exit |
|---|---|---|
| **Active** | Filed (commitment-bar pass) | → Blocked (label `status:blocked`); → Completed (close, `--reason completed`, termination condition met) |
| **Blocked** | Add `status:blocked` | → Active (remove label); → Completed |
| **Completed** | Close with `--reason completed` **only when the termination condition is satisfied** (evaluated per §3.4's recorded procedure) | terminal |
| **Closed (not pursued)** | Close with `--reason not-planned` | terminal |

Who evaluates the termination condition at close time is outside dir's scope (it may be the
human, claude-orch-shell surfacing it, or eng reporting up) — but because the condition is
code-independent (§3.2 property 2), any of them *can*. dir's job ends at guaranteeing the condition
is evaluable; it does not own the evaluation event.

`status:proposed` is **not** an Active-path state; it appears only on the manual-filing
path (§11).

### 9.1 Feedback consumption (eng→dir: challenge / completion)

After filing, the execution layer can surface a finding **up** to the Initiative — a
**challenge** (execution reality contradicts it) or a **completion** (the extracted work
landed). eng posts this as a comment via its `/initiative-feedback` (comment-only; eng
*escalates, it does not decide*), and a target-repo Action projects the comment marker into
a label — `initiative:challenged` / `initiative:completion-requested` — which
claude-orch-shell routes back to dir (R8/R9; vocabulary + routing owned by claude-orch-shell
SPEC §3.6/§5.4). **dir is the upstream owner that adjudicates.**

**The handshake.** dir is the **sole remover** of the feedback label (claude-orch-shell
decision O11). Removing it means *"dir has adjudicated this feedback"* (not necessarily
"agreed") — and clears claude-orch-shell's upward route. eng never removes it; the Action
only adds it (on a *new* comment); claude-orch-shell only reads it.

#### Challenge (`initiative:challenged`)

A challenge says: from execution, the Initiative appears not to hold — typically the
termination condition turned out **not** to be code-independently evaluable, or a real
dependency / measurability / cost the planning tier could not see surfaced. dir reads the
challenge comment and **re-judges**, with three outcomes (the choice is a strategic
judgment — dir's, with the human steering):

- **Revise** — the challenge is right. Fix the termination condition / scope and **re-run
  the commitment-bar evaluability gate (§3.4)** on the revision, then update the filed
  Initiative body in place. A challenge that the condition "smuggled in execution detail"
  is exactly the §3.4 gate having let something through — revising **tightens the gate**.
- **Defend** — the Initiative holds. Post a rebuttal comment explaining why (e.g., the
  condition *is* evaluable as stated; eng's concern is an implementation choice, not a
  contract flaw). The Initiative is unchanged.
- **Retire** — no longer worth pursuing in light of the finding. Close `--reason
  not-planned`.

After **any** outcome, **remove `initiative:challenged`** — the feedback is adjudicated.

#### Completion (`initiative:completion-requested`)

A completion reports the extracted Directives have all landed and **requests a termination
assessment** (eng does not assert completion). dir **evaluates the termination condition
(§3) against eng's cited evidence — code-independently**, using the evaluation procedure
recorded at filing (§3.4). This is the payoff of §3.2 property 2: dir decides done/not-done **without
reading eng's code**. Two outcomes:

- **Met** → close the Initiative `--reason completed`.
- **Not met** → post a comment naming what the termination condition still requires; the
  Initiative stays Active (eng may extract more and re-report).

After either, **remove `initiative:completion-requested`**.

This is where the dir→eng contract (§4) pays off twice: dir guaranteed an evaluable
condition at filing, so at completion it can assess without code; and a challenge that the
condition wasn't truly evaluable is the feedback that tightens the §3.4 gate.

#### Challenge-loop cap

challenge → revise → re-challenge can ping-pong. Cap it, mirroring the commitment-bar cap
(§5.5): after **N=2** challenge→revise rounds on the same Initiative without convergence,
dir stops auto-revising and **escalates to the human** (or marks `status:blocked` with the
open contention recorded). The cap prevents an infinite planning↔execution loop; the human
breaks the tie (revise differently, defend, or retire).

---

## 10. Assumptions about eng-shell (fixed external contract)

eng-shell is **frozen and out of scope** (a founding premise: eng-shell is frozen). dir designs around it as an
external system with a fixed contract. Assumptions dir relies on (read-only knowledge, not
requests for eng to change):

- eng recognizes the `initiative` label and the `Parent Initiative: #N` body marker.
- eng's hook predicates `is_directive_issue` / `is_initiative_issue` depend on
  `initiative`/`directive` label exclusivity — so dir must never co-apply them (§2.1).
- eng consumes an Active Initiative and produces its own Directives/execution; dir does not
  author or assume anything about eng's internal Directive flow.
- eng surfaces execution findings **up** via `/initiative-feedback` — comment-only, led by
  a `## Initiative challenge` / `## Initiative completion` marker (eng *escalates, does not
  decide*; eng MISSION "Consuming Initiatives"). dir consumes these (§9.1); dir relies only
  on eng's *existing* comment behavior, not on any eng change. (The comment→label
  projection is claude-orch-shell-side substrate, §9.1 / claude-orch-shell SPEC §5.4.)

**Deferred — would require an eng-shell change (do not act; record only):**
- The **feedback-label workflow** that projects eng's `## Initiative challenge|completion`
  comments into the `initiative:challenged` / `initiative:completion-requested` labels is
  hosted by eng substrate (a scoped additive eng change, `claude-eng-shell#305`). This is
  **not** dir's dependency — dir reads the comment and (separately) removes the label; the
  label vocabulary is owned by claude-orch-shell SPEC §3.6. Recorded here only because it
  touches eng; dir designs against eng's current comment behavior regardless.

---

## 11. Manual-filing path (secondary)

A GitHub Issue template (`.github/ISSUE_TEMPLATE/initiative-proposal.yml`, installed in the
target repo) supports filing outside the development loop — retrofitting an external
proposal, a one-off, or seeding a batch. Manual filings land at `initiative` +
`status:proposed` and **await a commitment-bar review before becoming Active** — the
termination-condition gate (§3.4) is not bypassed by the manual path; it is merely deferred
to review time. A manual filing whose termination condition fails the gate stays
`status:proposed` (or is closed `not-planned`), never silently Active.

**Seeding a batch**: file manually first, then `/develop-initiative <batch-id> --seed
#<issue-number>`; the candidate is treated as `01` and developed through §5. On commitment-
bar pass, the seed's `status:proposed` is removed (the developed version replaces it).

---

## 12. Candidate-generation mechanism (batch mode; secondary)

Single-Initiative development (§5) is the primary path. For breadth, dir can also generate
many candidates and converge — the prior spec's divergent/convergent pipeline, retained as
a **mechanism that feeds §5**, not as the headline. In `auto` autonomy (§5.2):

1. **Brainstorm** — generate N diverse candidates (genuinely different framings).
2. **Survival review + revise + screen** — apply §5.3 across the set; drop failures and
   dominated candidates to `rejected/`.
3. **Develop** — deepen survivors (§5.1 stage 2 grounding, incl. res calls).
4. **Rank** — order survivors **ordinally** with per-candidate justification; no numeric
   scoring (avoids false precision on fuzzy judgments). Flag ties.
5. **Select** — pick winner(s): default one; up to three when ranking is tight and
   non-conflicting; resolve cross-candidate conflict by merge (absorb into survivor; move
   merged-in to `merged-into/`) or drop; record in `selection.md`. All-dropped is a valid
   outcome (record "no selections" + rationale; terminate without filing).
6. **Commitment bar + file** — each selected candidate goes through §5.4–§5.5 independently.

Every selected candidate still passes the **same** termination-condition gate (§3.4); batch
mode changes how candidates *arrive* at the gate, never the gate itself.

---

## 13. Hooks / enforcement (deferred)

No hooks yet; discipline is by convention plus the §3.4 gate enforced in the development
flow. v1 candidates: `initiative`-branch protection (parallel to eng's `directive-protect`),
`initiative`/`directive` label-exclusivity enforcement, `Parent Initiative: #N` integrity
warnings, workspace-boundary write protection, and a hook asserting no filed Initiative
lacks a gate-passed termination condition. All deferred; recorded in claude-orch-shell
`WORK_LOG.md` open items when scheduled.

---

## 14. Decision record

Settled choices + rationale. Do not re-litigate without recording a new entry. (Premises
inherited from the project's founding premises are marked **[brief]**; they are fixed unless a future
session proves they block the end goal, per brief §2.4.)

| # | Decision | Rationale |
|---|---|---|
| D1 **[brief]** | The Initiative's load-bearing property is a **code-independent, evaluable termination condition** (§3). | It is the exact contract eng relies on and the only thing claude-orch-shell can route on without reading content. Everything else in dir serves producing it. |
| D2 | **Termination condition is a distinct required field**; the prior spec's "success signals" is demoted to an optional leading-indicator field (§2.2). | The gate must be one unambiguous criterion. Conflating it with progress signals (which may be partially met while open) blurs the done/not-done verdict the contract needs. |
| D3 | The four properties — **decidable, code-independent, attributable, bounded** (§3.2) — are the validity test, checked explicitly at the commitment bar (§3.4). | Gives the gate teeth: a checklist a reviewer can pass/fail per property, plus a written evaluation procedure that operationally proves code-independence. |
| D4 | The **termination-condition gate is non-skippable**, even at the revision cap; an Initiative with an invalid condition is parked, never filed (§5.5). | The contract is not dir's to waive (D1). Other (commitment-readiness) concerns may be filed with a note; the gate may not. |
| D5 **[brief]** | **dir never reads source code**, even in repo mode where it technically could (§7.4); code-derived facts come only via res *strategic* documents (which also never read code, §6). | Preserves the planning-tier/execution-tier separation that makes the termination condition authorable by dir and routable by claude-orch-shell. An invariant, not a side effect of "no clone." |
| D6 **[brief]** | dir calls **res in strategic mode**, mode fixed by caller, one mode per invocation, no code (§6.2). res returns a document used as **evidence, not a decision**. | Mirrors the res SPEC's mode contract; keeps dir code-independent while still letting it ground claims in real research. |
| D7 | **Single-Initiative development (§5) is primary; batch generation (§12) is a secondary mechanism** feeding the same gate. | The brief frames dir as developing an Initiative (often with the human), not primarily as an autonomous batch brainstormer. Batch mode is retained for breadth but subordinated; the gate is identical either way. |
| D8 | **Human cannot override the termination-condition gate** but can override a survival-bar `reject` (§5.2). | The gate protects an external contract (eng's); survival is dir-internal quality and the human may accept the risk of developing a weak candidate. |
| D9 | Keep the four **domains** and the **domain-dispatched rubric** (§8) from the prior spec; keep **repo/standalone modes**, **target-by-address-never-cloned**, **workspace-as-archive**, **`initiative`/`directive` exclusivity**. | These were sound and independent of the recentering; salvaged wholesale (WORK_LOG 2026-06-03 salvage note). |
| D10 | Rename workspace `drafts/` → `initiatives/` and add `research/` (§7.1). | "initiatives/" names what the tree holds; `research/` is needed now that res documents are first-class evidence (§6) and must live in the audit trail. |
| D11 **[brief]** | claude-orch-shell sees the Initiative on **metadata only** (`initiative` label + Active state) and does **not** see res calls (§4.3, §6). | res calls are stage-internal subroutines; claude-orch-shell is type-A plumbing routing on metadata (claude-orch-shell SPEC). |
| D12 | **dir is the sole adjudicator of eng feedback and the sole remover of the feedback label** (§9.1). On a challenge dir decides revise/defend/retire; on a completion dir decides met/not-met; either way it removes the label. | eng escalates, it does not decide (eng MISSION); the strategic decision is dir's. Sole-remover mirrors claude-orch-shell O11 — label removal is the "handled" signal that clears the upward route. |
| D13 | **Completion is assessed via the code-independent termination condition** (§9.1); a challenge that the condition wasn't truly evaluable **tightens the §3.4 gate** rather than just being filed. | The §3.2 property-2 payoff: dir can decide done without reading code. And a challenge is evidence the gate let an under-evaluable condition through — the right response is to fix the gate's output, not to defend a flawed contract. |
| D14 | **Challenge-loop cap N=2** → escalate to human / `status:blocked` (§9.1), mirroring the commitment-bar cap (§5.5). | Prevents an infinite planning↔execution ping-pong; the human breaks a genuine contention. |

---

## 15. Open items

- Default `N` for batch brainstorm (currently 5; revisit after first dogfood).
- Whether the termination condition should eventually be a **structured machine-readable
  field** (vs free text) — would let claude-orch-shell/eng parse it, but claude-orch-shell is
  metadata-only by design (D11) and eng is frozen (§10), so deferred; free text for now.
- Tie threshold in batch ranking (ranker self-judgment for now).
- Reviewer abstain semantics (`insufficient-evidence` vs revise/reject).
- Domain extensibility for planning work outside the four domains (§8.1).
- Cross-mode promotion: can a standalone workspace later attach a target repo and file
  previously-local Initiatives without re-running the lifecycle?
- Whether `Completed` evaluation should be assisted by a dir command (re-running the §3.4
  evaluation procedure) even though dir doesn't own the evaluation event (§9).
- **Feedback-consumption tooling** (§9.1): a `dir feedback <N>` command that reads the
  challenge/completion comment + label, runs the revise/defend/retire or completion
  assessment, and **removes the label** — the dir-side actuator of the eng→dir edge. Tier 2.

---

*This SPEC is a fresh rewrite (2026-06-03) superseding the prior 9-phase-pipeline SPEC and
ADR-0001 where they conflict. State/progress: claude-orch-shell `WORK_LOG.md`.*
