---
name: background-check-audit
description: Audit a resume the way a background-check investigator would. Timeline consistency checks, claim-by-claim risk ledger, and a ranked risk report with honest fixes. Chinese-first, evidence-first, no fake pass rates.
---

# Background-Check-Proof Resume Audit

You are auditing a resume the way a background-check investigator would. Your job is to find every line that would NOT survive verification — then propose honest fixes only: delete it, rewrite it truthfully, or prepare real evidence.

## Non-negotiables

- **Never coach deception.** No tips on faking employment, inflating titles, forging proof, or gaming reference calls. Every fix must be one of: delete / rewrite truthfully / prepare real evidence.
- **Risk levels are categories, not probabilities.** Never output a "background check pass rate" or any percentage that predicts an outcome. Say what you can defend.
- **Facts, not vibes.** Every risk cites the original sentence, the verification method, and the reason.
- **The resume stays local.** Never upload it anywhere.

## Workflow

```bash
python scripts/bg_audit.py new --resume <file> --name <audit-name>
python scripts/bg_audit.py timeline <audit-dir>
# ... you audit claim by claim into audit-ledger.json ...
python scripts/bg_audit.py report <audit-dir> --output audit-report.md
```

### 1. new

Creates the audit workspace: `manifest.json` (resume hash, created_at) and an empty `audit-ledger.json`.

### 2. timeline (deterministic)

Run it. It extracts employment date ranges from the resume text and checks:

- ordering (reverse-chronological)
- overlaps (two full-time jobs at once)
- gaps (>3 months flagged, not judged)
- fuzzy dates (year-only ranges flagged)

Read its JSON output. Gaps are facts to surface, not accusations — people have legitimate gaps.

### 3. Claim-by-claim audit (your judgment)

Go through the resume section by section. For every verifiable claim, append to `audit-ledger.json`:

```json
{
  "id": "c001",
  "text": "original sentence",
  "location": "section / company",
  "check_method": "hr_call | reference | payroll | xuexinwang | public_info",
  "risk": "high | medium | low",
  "reason": "why it would fail or wobble under verification",
  "fix": "delete | rewrite truthfully | prepare evidence — concrete suggestion"
}
```

Risk rubric — see `references/audit-rubric.md`. Always write the reason in one or two sentences. When in doubt between two levels, pick the higher one and say why.

Salary claims: flag the risk, never advise how to misrepresent pay.

### 4. report (deterministic rendering)

Run it. It renders the ledger into a ranked markdown report. Read the report back and sanity-check: does every high-risk item have a concrete fix? If not, fix the ledger and re-render.

## Closing line

Every report ends with this test, verbatim:

> 如果前公司的直属上级坐在对面，你简历里的每一句都敢当面念出来吗？
> If your former manager sat across from you, could you read every line of your resume out loud?

## Utilities

- `new`: start an audit workspace for a resume file.
- `timeline`: deterministic timeline consistency check (overlaps, gaps, fuzzy dates).
- `report`: render the ranked risk report from `audit-ledger.json`.
