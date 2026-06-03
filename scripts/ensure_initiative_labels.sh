#!/usr/bin/env bash
# scripts/ensure_initiative_labels.sh — idempotent creation of the labels a
# target repo needs to host claude-dir-shell Initiatives. Run once against the
# target (via `gh`; no local clone required).
#
# Labels created:
#   - initiative       — primary marker for an Initiative Issue (SPEC §2.1)
#   - status:proposed  — Initiative filed via the manual path (Issue template),
#                        awaiting a commitment-bar review. Initiatives filed by
#                        the development lifecycle skip this state — they are
#                        filed directly Active.
#   - status:blocked   — Initiative cannot proceed without external input
#   - needs-triage     — Issue filed without a template (raw filing)
#
# Status convention: an Active Initiative is "open + initiative + no status:*
# label" (mirrors eng-shell's Directive convention). Completed is the implicit
# closed-with-reason=completed pattern, not a label.
#
# Two filing paths (SPEC §5, §11):
#   1. Development lifecycle (primary, SPEC §5): dir develops an Initiative
#      (draft → ground → survival/commitment-bar gate) and files it directly as
#      an Active Issue (via `gh issue create`).
#   2. Manual (secondary, SPEC §11): the Issue template files at
#      initiative + status:proposed for retrofitting external proposals or
#      one-offs, gated by a commitment-bar review before becoming Active.
#
# Not created here: the orch-owned feedback labels
# (`initiative:challenged` / `initiative:completion-requested`, SPEC §9.1) — their
# vocabulary belongs to claude-orch-shell and their workflow is eng-hosted.
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

ensure_label "initiative"      "1D76DB" "Initiative — planning-tier strategic commitment (SPEC §2)"
ensure_label "status:proposed" "FBCA04" "Initiative proposed; awaiting commitment-bar review"
ensure_label "status:blocked"  "B60205" "Initiative cannot proceed without external input"
ensure_label "needs-triage"    "D4C5F9" "Issue filed without a template — awaiting maintainer triage"

echo "ensure_initiative_labels: done."
echo
echo "Note: if this repo also runs claude-eng-shell, the 'status:*' and"
echo "'needs-triage' labels are shared by both shells. Re-running eng-shell's"
echo "ensure_v3_labels.sh after this script is safe (colors/descriptions"
echo "may diverge by last-writer-wins — accept whichever is authoritative)."
