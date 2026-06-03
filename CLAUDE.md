# claude-dir-shell — Operating Norms

Operating manual for working in this repo. Read by Claude Code at session start. Direction in [MISSION.md](MISSION.md); consolidated architecture in [docs/ADRs/0001-architecture.md](docs/ADRs/0001-architecture.md); operational details (when present) in [SPEC.md](SPEC.md).

## Status

Specification phase (SPEC rewritten 2026-06-03). The repo contains MISSION, README, this CLAUDE.md, ADR-0001 (earlier record, superseded by SPEC where they conflict), an Issue template, a label setup script, and the authoritative [SPEC.md](SPEC.md). No subagents, slash commands, or hooks yet.

Until those ship, work runs on **GitHub-standard discipline plus the norms below**. No automated enforcement. **The authoritative design is [SPEC.md](SPEC.md)** — when this file or ADR-0001 disagrees with SPEC, SPEC wins.

## Core norms

### 1. Three locations
This tool repo is read-only at runtime. The user's **workspace** (separate, user-managed) is the decision archive (SPEC §7.1). The **target repo** (referenced by `owner/name` address) is read via `gh` API and written to only at Initiative filing. Never clone the target repo. See [SPEC.md](SPEC.md) §7.

### 2. The termination-condition contract is the spine
Every Initiative must carry a **decidable, code-independent, attributable, bounded** termination condition (SPEC §3). It is guaranteed at a **non-skippable commitment-bar gate** before filing — an Initiative with an invalid termination condition is never filed (SPEC §3.4, §5.5). When developing an Initiative by hand (until subagents ship), run the evaluability check yourself and record it in the workspace. Development lifecycle: draft → ground → survival-bar review/revise → commitment-bar gate → file (SPEC §5). Batch generation (SPEC §12) is a secondary mechanism feeding the same gate.

### 3. Input surface — planning-tier only (invariant)
Read MISSION, GitHub Milestones, Issues, existing Initiatives, and strategic-mode research documents. **Never read source code** — this holds even in repo mode where you technically could (SPEC §7.4, decision D5). Code-derived facts come only via res strategic-mode documents (SPEC §6), which themselves never read code.

### 4. The `initiative` label is reserved
Never apply the `directive` label to a dir-shell artifact. Labels are mutually exclusive (SPEC §2.1, §10). In combined eng-shell + dir-shell repos, eng-shell hook predicates (`is_directive_issue` / `is_initiative_issue`) depend on this exclusivity. eng-shell is a frozen external system (SPEC §10) — never written to.

### 5. Active SSOT maintenance
When MISSION, the ADR, or SPEC.md is invalidated by a change, the change updates the SSOT in the same commit. Otherwise the commit body says `Docs: n/a — <short reason>`. SPEC is the source of truth for design; claude-orch-shell's `WORK_LOG.md` is the source of truth for state/progress.

### 6. Spec before code
This is a spec-first project. Do not implement a unit until its SPEC section is complete and internally consistent. If implementation reveals the spec is wrong, fix the spec first, then implement against it. Never let code silently diverge from SPEC.

## Subagents

eng-shell fallbacks until dir-shell subagents ship (read-only use of eng-shell agents is fine; **never write to eng-shell**):

| Situation | Agent |
|-----------|-------|
| Wide read-only exploration | `explorer` |
| 3+ file changes / structural | `planner` |
| Doc writing | `doc-writer` |
| Pre-commit / pre-PR review | `code-reviewer` |
| Lifecycle / batch phases (SPEC §5, §12) | *forthcoming dir-shell subagents* — until shipped, do the work inline and document outcomes in the workspace |

## Engineering discipline (adopted from claude-eng-shell)

- **Issue → branch → PR → merge.** File a typed Issue; branch
  `<gh-username>/<type>/<issue#>-<slug>`; open a PR ending with `Closes #<N>` (or `Refs #<N>`
  for intermediate PRs); merge into `main` with a **merge commit** (no squash/rebase on the
  default branch).
- **Conventional commits.** `<type>(#<issue>)[!]: <subject>` (≤ 72 codepoints). Types
  `feat fix docs refactor perf` (issue # required) · `test style build ci chore revert`
  (issue # optional). Optional `Co-Authored-By: Claude <noreply@anthropic.com>`.
- **Doc → Test → Code** phased commits for features; relaxed for fix/refactor/perf.
- **Changelog fragments.** Each PR with an observable change adds
  `changelog_unreleased/<category>/<PR>.md` (`- … (#<PR>)`); internal-only PRs use the
  `skip-changelog` label. Releases consolidate fragments into `CHANGELOG.md` + bump `VERSION`.

## Boundary

- Never modifies user-global state (`~/.zshrc`, `~/.claude/` outside the auto-memory tier, global git config).
- When the tool ships scripts and hooks, they will be scoped to the registered workspace only.
