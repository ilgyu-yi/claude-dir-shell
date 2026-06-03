# ADR 0001: claude-dir-shell architecture

- Date: 2026-05-27
- Status: **Superseded in part by [SPEC.md](../../SPEC.md) (2026-06-03 rewrite).**

> **Supersession note (2026-06-03).** SPEC.md was rewritten to recenter dir-shell on the
> Initiative's **code-independent evaluable termination condition** (the contract eng-shell
> relies on) and on dir↔res strategic-mode integration. Where this ADR and SPEC conflict,
> **SPEC wins**, and SPEC §14 carries the authoritative decision record. Specifically:
> Decision 6 (the nine-phase pipeline as the *canonical* workflow) is **demoted** —
> single-Initiative development (SPEC §5) is now primary and the pipeline is a secondary
> batch-generation mechanism (SPEC §12). Decisions 1–5, 7, 9, 10 remain broadly valid and
> were salvaged into SPEC. This ADR is retained for history; do not treat it as current.

## Context

claude-dir-shell is a planning scaffold: it helps a planner (or human + Claude pair) generate and curate planning-tier strategic commitments. It is in the specification phase. This ADR records the load-bearing irreversible decisions in one place so SPEC.md and downstream artifacts have a stable foundation. Alternatives sections are intentionally omitted — this is the spec-phase consolidation, not an audit trail of every option considered.

## Decisions

### 1. Artifact, label, and tier

- The artifact produced and curated is called an **Initiative**. GitHub label: `initiative` (singular, lowercase). Required *for any repo where Initiatives are filed*.
- Initiatives sit **one tier above the execution layer**. They parent downstream execution artifacts — eng-shell Directives, experiment-run records, decision records, product bets — via the body marker `Parent Initiative: #N` (symmetric to eng-shell's `Parent Directive: #N`).
- **No Initiative-of-Initiatives.** The tree is flat at the Initiative tier. A large strategic commitment splits into peer Initiatives, not nested ones.
- `initiative` and `directive` labels are mutually exclusive on any given Issue, so eng-shell hook predicates (`is_directive_issue`) remain coherent in combined repos.

### 2. Input surface — planning-tier only

dir-shell reads only **planning-tier artifacts**: MISSION, GitHub Milestones, eng-shell Directives, Issues, and (when present) SPEC.md. dir-shell does **not** read source code. Code-derived context must be distilled into a planning-tier artifact upstream before it reaches dir-shell.

### 3. Target repo — by address, no clone

dir-shell takes a target repo as a **GitHub repo address** (`owner/name` or URL) and operates on it via the `gh` CLI / API. The target repo is **never cloned**. Reads (MISSION fetch, milestones, Directives, Issues) and writes (filing selected Initiatives as Issues) go through `gh api` and `gh issue create`. The target repo is read-only except for the final Issue filings at pipeline end.

### 4. Workspace — user-managed local archive

The **workspace** is a user-managed local directory, separate from both the dir-shell tool repo and the target repo. The user creates it and points dir-shell at it (e.g., `--workspace ~/planning/<topic>/`). All drafts, reviews, rankings, and selection records accumulate there. The workspace serves as the **decision-making archive** — never written back to the target repo, never synced from it. Drafts persist across pipeline runs.

### 5. Standalone (no-target) mode

When no target repo is supplied, dir-shell runs in **standalone mode**. The workspace owns its own `MISSION.md` (written once at workspace creation) as the planning anchor. A `--mission <path>` CLI override is available per run for ad-hoc invocations. In standalone mode, phase-7 "selection" produces local files under the workspace instead of filing GitHub Issues; the audit trail stays entirely within the workspace.

### 6. Nine-phase pipeline

The canonical workflow is a nine-phase pipeline:

1. **Brainstorming** — generate N candidate Initiatives (`brainstormer` subagent).
2. **Review (survival bar)** — critique each candidate against the domain-dispatched rubric (`reviewer` subagent).
3. **Revise** — improve each candidate using review + sibling context (`reviser` subagent).
4. **Screening** — drop candidates that fail the rubric threshold (`screener` subagent).
5. **Develop** — deepen survivors (`developer` subagent).
6. **Ranking** — order survivors by MISSION fit, confidence, impact (`ranker` subagent).
7. **Selection** — pick winner(s); resolve conflicts (`selector` subagent). Single survivor preferred; 2–3 allowed when quality is comparable.
8. **Post-selection review (commitment bar)** — re-evaluate at higher bar (`reviewer` subagent, stricter prompt).
9. **Post-selection revise** — respond to phase-8 critique (`reviser` subagent). **Hybrid loop**: one pass by default; substantive revision re-triggers phase 8 once. Hard cap at two cycles. Then file as Active Issue (repo mode) or write to workspace selection record (standalone mode).

Seven distinct subagents back nine phases; phases 8 and 9 reuse `reviewer` and `reviser` with stricter prompt variants.

### 7. Substrate within the workspace

Candidates persist as files under the workspace's `drafts/<batch-id>/` tree through phases 1–9. Selected Initiatives become GitHub Issues with the `initiative` label, **directly Active** (no `status:proposed` intermediate). Issue tracker stays clean of rejected candidates; the workspace git history is the version log.

Layout (subject to SPEC.md refinement):

```
<workspace>/
  MISSION.md                      # workspace-owned mission (standalone mode anchor)
  drafts/
    <batch-id>/
      meta.md                     # batch context: target repo address (if any), topic, timestamp
      candidates/                 # phase-1 brainstorm; mutated by phases 3, 5, 9
      reviews/                    # phase-2 + phase-8 reviewer output
      rejected/                   # phase-4 screening rejects
      ranking.md                  # phase-6 output
      selection.md                # phase-7 output
```

### 8. Orchestration — two-tier

- **Top-level**: `/run-initiative-pipeline [--repo <owner/name>] [--topic "<area>"] [--mission <path>]` runs phases 1–9 end-to-end. Default scope is mission-wide; `--topic` narrows; `--repo` enables repo mode (vs standalone); `--mission` overrides workspace MISSION.
- **Per-phase**: nine per-phase commands (`/brainstorm`, `/review`, `/revise`, `/screen`, `/develop`, `/rank`, `/select`, `/post-selection-review`, `/post-selection-revise`) operate on an existing batch for resume, intervention, or replay. Names subject to SPEC.md.

### 9. Domain-dispatched rubric

Each candidate carries a structured `domain` field (enumerated: `scientific-methodology` / `experiment-design` / `product-development` / `decision-making`). The reviewer dispatches per-domain rubrics. A small set of cross-cutting axes (MISSION fit, context-grounding, scope clarity, framing rigor) applies to all domains.

### 10. Manual filing path (secondary)

A GitHub Issue template (`.github/ISSUE_TEMPLATE/initiative-proposal.yml`) supports manual filing outside the pipeline — for retrofitting external proposals or seeding a batch. Manual filings land at `status:proposed` and await review. The pipeline path is canonical; manual is secondary.

## Consequences

- **Tool repo / workspace / target repo are three distinct locations.** dir-shell installs into the workspace (eng-shell pattern); the workspace accumulates drafts; the target repo is referenced by address and touched only via `gh` API.
- **Standalone and repo modes share substrate and pipeline shape.** Only the I/O at the boundaries differs (gh API vs local files).
- **Subagent surface = 7.** Authoring, prompting, and iterating seven subagents plus four per-domain rubric variants is the build cost.
- **`status:proposed` is secondary**, used only on the manual-filing path. Pipeline-selected Initiatives skip it (filed directly Active).
- **No Initiative-of-Initiatives constraint** is a deliberate v0 limit; large strategic commitments split into peer Initiatives instead of nesting.

## Open items deferred to SPEC.md

- Per-phase numeric defaults (N candidates, M revision rounds, screening bar, multi-survivor selection threshold).
- Phase-8 commitment-bar differential from phase-2 survival-bar.
- "Substantive revision" criteria for phase 9 → re-trigger phase 8.
- "Develop" output shape.
- Post-selection lifecycle (Active → Blocked / Completed).
- Parent-child completion semantics.
- Batch ID format.
- Manual-filing review path semantics.
- Reviewer abstain vs reject semantics.
- Workspace bootstrap motion (init command, default MISSION template).
- Cross-mode target-repo MISSION discovery (path convention, fallbacks).
