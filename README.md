# claude-dir-shell

The **planning tier** of an orchestrated [Claude Code](https://docs.claude.com/claude-code) shell system. dir-shell helps a person — or human + Claude pair — generate, critique, and curate **Initiatives**: planning-tier strategic commitments. It files them for the execution tier ([claude-eng-shell](https://github.com/ilgyu-yi/claude-eng-shell)) to consume, and calls the research tier ([claude-res-shell](https://github.com/ilgyu-yi/claude-res-shell)) for evidence. dir-shell never reads source code.

See [MISSION.md](MISSION.md) for direction and [SPEC.md](SPEC.md) for the authoritative design (a fresh 2026-06-03 rewrite). [docs/ADRs/0001-architecture.md](docs/ADRs/0001-architecture.md) is the earlier architecture record, superseded by SPEC where they conflict.

## Status

Specification phase (SPEC rewritten 2026-06-03). MISSION, CLAUDE.md, SPEC.md, an Issue template, and a label setup script are in place. No subagents, slash commands, or hooks yet — those are the next phase.

## Core ideas

- **The termination-condition contract**: every Initiative carries a **decidable,
  code-independent, attributable, bounded** termination condition — *what done means*,
  evaluable without reading code. This is the contract the execution tier relies on; dir
  guarantees it at a non-skippable commitment-bar gate. SPEC §3–§4.
- **Review-gated development**: draft → ground → survival-bar review/revise →
  commitment-bar gate → file, typically with a human steering. SPEC §5.
- **Strategic-mode research**: when planning artifacts aren't enough, dir calls res-shell
  in strategic mode (no code) and folds the returned document in as cited evidence. SPEC §6.
- **Workspace is the archive**: a user-managed local directory holds candidates, reviews,
  research documents, rejections, and filing records. SPEC §7.
- **Target by address, not by clone**; **standalone mode** when there's no target repo. SPEC §7.4.
- **Domain-dispatched rubric**: four domains (scientific-methodology / experiment-design /
  product-development / decision-making). SPEC §8.
- **Batch generation** (secondary): brainstorm → screen → rank → select feeds the same
  gate when breadth is wanted. SPEC §12.

## Relationship to claude-eng-shell

eng-shell owns the `directive` label and execution-tier Directives; dir-shell owns the `initiative` label and planning-tier Initiatives. The labels are mutually exclusive on any Issue, so eng-shell type-aware hooks (`is_directive_issue`) continue to work without modification in combined repos.

Tier hierarchy:

```
MISSION
   ▼
Initiative (dir-shell)                ← planning-tier strategic commitment
   ▼
Directive | experiment | decision | bet   ← Tier-2 execution artifacts
   ▼
Execution Issue (eng-shell only)      ← code-level work, PRs, merges
```

A combined repo accumulates at most four tiers on the engineering path; non-engineering paths stop at Tier 2.

## License

TBD.
