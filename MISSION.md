# MISSION — claude-dir-shell

claude-dir-shell is the **planning tier** of an orchestrated Claude Code shell system. It
helps a person — or a human + Claude pair — generate, critique, and curate planning-tier
strategic commitments called **Initiatives**, then files them for the execution tier
(claude-eng-shell) to consume. dir-shell never reads source code; it operates over
planning-tier artifacts and over research documents that claude-res-shell produces for it
in strategic mode.

## The load-bearing idea

An Initiative's reason to exist as a distinct artifact is its **termination condition**: a
statement of *what done means* that is **decidable, code-independent, attributable, and
bounded** — assessable by someone who has never read the codebase. This is the exact
contract the execution tier relies on and the only thing claude-orch-shell can route on
without interpreting content. dir-shell's central job is to **guarantee** that contract:
no Initiative is filed unless its termination condition passes an explicit evaluability
gate. See [SPEC.md](SPEC.md) §3 and §4.

## Shared principle — context narrowing

dir shares the system's load-bearing principle (origin:
[claude-eng-shell MISSION](https://github.com/ilgyu-yi/claude-eng-shell/blob/main/MISSION.md)
"The mechanism"; system statement in claude-orch-shell MISSION): **output quality is bounded
by the size and relevance of working context** — keep the active context small and relevant
(narrowing + selective injection), with **artifacts, not conversations, as the durable
memory**. Every Initiative is judged against it.

dir embodies it by **excluding the entire code context**: it reads only planning-tier
artifacts (never source code, even when it could), and grounds claims in res **documents** (a
distilled verdict, not a research transcript). Most pointedly, the **termination condition is
itself a context boundary** between planning and execution — the artifact that lets *dir
reason without code context* and *eng reason without strategy context*. Guaranteeing it is
how dir keeps both tiers' working contexts small and relevant.

## What it does

- **Develops Initiatives** through a review-gated lifecycle (draft → ground → survival-bar
  review/revise → commitment-bar gate → file), typically with a human steering.
- **Grounds them in evidence** — when planning-tier artifacts aren't enough, dir calls
  res-shell in **strategic mode** (no code) and folds the returned research document in as
  cited evidence.
- **Guarantees the termination-condition contract** at a non-skippable commitment-bar gate
  before any Initiative is filed Active.
- **Files Initiatives** as `initiative`-labeled GitHub Issues against a target repo (read
  by address via `gh`, never cloned), or as local records in standalone mode.
- **Archives the decision trail** in a user-managed workspace: every candidate, review,
  research document, rejection, and filing rationale.

dir reads only planning-tier artifacts (MISSION, milestones, Issues, existing Initiatives)
plus strategic-mode research documents — **never source code** (an invariant, not a
side effect of not cloning). For breadth, dir can also generate many candidates and
converge (batch mode, SPEC §12), but single-Initiative development is the primary path.

## Success looks like

A planner using dir-shell produces Initiatives whose quality matches a careful senior
planner's, faster — and crucially, **every filed Initiative carries a termination condition
the execution tier can evaluate to done/not-done without reading code.** Concretely:

- **The gate has teeth.** No Initiative is filed with a vague, code-coupled, unbounded, or
  unattributable termination condition; the commitment-bar evaluability check (SPEC §3.4)
  blocks it.
- **Review and screening have teeth.** Weak candidates are rejected with specific,
  rubric-tied reasons at the survival bar; the commitment bar catches the rest.
- **Quality is domain-appropriate.** The rubric dispatches per domain
  (scientific-methodology / experiment-design / product-development / decision-making).
- **Grounding is the default.** Initiatives cite concrete planning-tier evidence or
  research documents; ungrounded candidates are dropped.
- **The archive is durable.** A future planner can ask "what did we consider, what evidence
  did we gather, and why did we drop those?" and get an answer from the workspace.

## Out of scope

- **Not engineering execution** — that's [claude-eng-shell](https://github.com/ilgyu-yi/claude-eng-shell).
- **Not a code-reading tool** — planning-tier artifacts and strategic research only.
- **Not a project-management/roadmap tool**, and not a generic ideation app — scoped to
  mission-aligned strategic commitments under critical review, each with an evaluable
  termination condition.

---

*Last reviewed: 2026-06-03. Specification phase. Authoritative design: [SPEC.md](SPEC.md)
(fresh rewrite superseding the prior pipeline-centric framing and ADR-0001 where they
conflict). Progress/state: claude-orch-shell's `WORK_LOG.md`.*
