#!/usr/bin/env bash
# scripts/ensure_initiative_labels.sh — idempotent creation of labels the
# Initiative Issue template and the (forthcoming) pipeline subagents + slash
# commands depend on. Run once against a target repo that will host
# claude-dir-shell Initiatives (via `gh`; no local clone required).
#
# Labels created:
#   - initiative       — primary marker for an Initiative Issue (ADR-0001)
#   - status:proposed  — Initiative filed via the manual path (Issue template),
#                        awaiting review. Pipeline-selected Initiatives skip
#                        this state — they are filed directly Active.
#   - status:blocked   — Initiative cannot proceed without external input
#   - needs-triage     — Issue filed without a template (raw filing)
#
# Status convention: an Active Initiative is "open + initiative + no status:*
# label" (mirrors eng-shell's Directive convention). status:completed is the
# implicit closed-state-reason=completed pattern, not a label.
#
# Two filing paths (ADR-0001):
#   1. Pipeline (canonical): /run-initiative-pipeline produces drafts in the
#      user's workspace; phase-9 output files survivors directly as Active
#      Issues in the target repo (via `gh issue create`).
#   2. Manual (secondary): Issue template files at initiative + status:proposed
#      for retrofitting external proposals or one-off filings.
#
# Idempotent: `gh label create --force` overwrites color/description but is
# stable on existing label names. Safe to re-run.

set -euo pipefail

ensure_label() {
  local name="$1" color="$2" desc="$3"
  gh label create "$name" --color "$color" --description "$desc" --force >/dev/null
  echo "  label '$name' ensured"
}

echo "ensure_initiative_labels: creating Initiative labels (idempotent)..."

ensure_label "initiative"      "1D76DB" "Initiative — planning-tier strategic commitment (ADR-0001)"
ensure_label "status:proposed" "FBCA04" "Initiative proposed; awaiting convergent review"
ensure_label "status:blocked"  "B60205" "Initiative cannot proceed without external input"
ensure_label "needs-triage"    "D4C5F9" "Issue filed without a template — awaiting maintainer triage"

echo "ensure_initiative_labels: done."
echo
echo "Note: if this repo also runs claude-eng-shell, the 'status:*' and"
echo "'needs-triage' labels are shared by both shells. Re-running eng-shell's"
echo "ensure_v3_labels.sh after this script is safe (colors/descriptions"
echo "may diverge by last-writer-wins — accept whichever is authoritative)."
