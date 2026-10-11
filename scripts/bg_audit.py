#!/usr/bin/env python3
"""Background-check-proof resume audit CLI. Python standard library only.

Commands:
  new       Start an audit workspace for a resume file.
  timeline  Deterministic timeline consistency check (overlaps, gaps, fuzzy dates).
  report    Render the ranked risk report from audit-ledger.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
GAP_MONTHS = 3

RISK_ORDER = {"high": 0, "medium": 1, "low": 2}
CHECK_METHODS = ("hr_call", "reference", "payroll", "xuexinwang", "public_info")

CLOSING_ZH = "如果前公司的直属上级坐在对面，你简历里的每一句都敢当面念出来吗？"
CLOSING_EN = "If your former manager sat across from you, could you read every line of your resume out loud?"


# ---------------------------------------------------------------- utilities

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        if shutil.which("pdftotext"):
            result = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError:
            raise RuntimeError(
                "Cannot read PDF: install pypdf or pdftotext, or convert to .txt first."
            )
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    raise RuntimeError(f"Unsupported file type: {suffix} (use .pdf or .txt)")


# ---------------------------------------------------------------- timeline

# Matches: 2025.09 / 2025-09 / 2025年9月 / 2025/09, and range ends like 至今/现在/Present/Now
DATE = r"(?P<y>\d{4})\s*[.\-/年]\s*(?P<m>\d{1,2})\s*月?"
YEAR_ONLY = r"(?P<y>\d{4})\s*年?"
PRESENT = r"(?:至今|现在|目前|Present|present|Now|now)"
SEP = r"\s*(?:–|—|-|~|至|到)\s*"

_DATE_ANY = r"(?:\d{4}\s*[.\-/年]\s*\d{1,2}\s*月?|\d{4}\s*年?)"
RANGE_RE = re.compile(rf"(?P<start>{_DATE_ANY}){SEP}(?P<end>{_DATE_ANY}|{PRESENT})")


def _to_month(year: int, month: int | None) -> tuple[int, bool]:
    """Return (absolute month index, fuzzy). Year-only dates are fuzzy."""
    if month is None:
        return year * 12, True
    return year * 12 + (month - 1), False


def parse_ranges(text: str, today: tuple[int, int] | None = None) -> list[dict]:
    """Find employment date ranges in document order."""
    if today is None:
        now = datetime.now()
        today = (now.year, now.month)
    ranges = []
    for match in RANGE_RE.finditer(text):
        start_raw, end_raw = match.group("start"), match.group("end")

        def parse(part: str) -> tuple[tuple[int, bool], str]:
            m = re.fullmatch(DATE, part.strip())
            if m:
                return _to_month(int(m.group("y")), int(m.group("m"))), part.strip()
            m = re.fullmatch(YEAR_ONLY, part.strip())
            if m:
                return _to_month(int(m.group("y")), None), part.strip()
            # present
            return (today[0] * 12 + (today[1] - 1), False), part.strip()

        (s_idx, s_fuzzy), s_norm = parse(start_raw)
        (e_idx, e_fuzzy), e_norm = parse(end_raw)
        ranges.append(
            {
                "raw": match.group(0).strip(),
                "start": s_norm,
                "end": e_norm,
                "start_index": s_idx,
                "end_index": e_idx,
                "fuzzy": s_fuzzy or e_fuzzy,
                "reversed": s_idx > e_idx,
            }
        )
    return ranges


def check_timeline(ranges: list[dict]) -> dict:
    """Deterministic consistency checks over parsed ranges (document order)."""
    findings: list[dict] = []
    for i, r in enumerate(ranges):
        if r["fuzzy"]:
            findings.append({"type": "fuzzy_date", "range": r["raw"],
                             "note": "Year-only date; background checks compare exact months."})
        if r["reversed"]:
            findings.append({"type": "reversed_range", "range": r["raw"],
                             "note": "Start is after end."})
    # overlaps and gaps need chronological order: sort by start_index desc
    # (resumes list most recent first)
    ordered = sorted(
        [r for r in ranges if not r["reversed"]],
        key=lambda r: r["start_index"], reverse=True,
    )
    for a, b in zip(ordered, ordered[1:]):
        # a is more recent than b; b should end before-or-when a starts
        if b["end_index"] > a["start_index"]:
            findings.append({"type": "overlap", "ranges": [a["raw"], b["raw"]],
                             "note": "Two jobs claim the same months."})
        else:
            gap = a["start_index"] - b["end_index"]
            if gap >= GAP_MONTHS:
                years, months = divmod(gap, 12)
                label = f"{years}y{months}m" if years else f"{months}m"
                findings.append({"type": "gap", "between": [b["raw"], a["raw"]],
                                 "gap_months": gap,
                                 "note": f"Unexplained gap of ~{label}. Flag it, don't judge it."})
    return {"ranges_found": len(ranges), "findings": findings}


# ---------------------------------------------------------------- commands

def manifest_path(audit_dir: Path) -> Path:
    return audit_dir / "manifest.json"


def ledger_path(audit_dir: Path) -> Path:
    return audit_dir / "audit-ledger.json"


def load_manifest(audit_dir: Path) -> dict:
    path = manifest_path(audit_dir)
    if not path.is_file():
        raise RuntimeError(f"Not an audit workspace: {audit_dir}")
    return json.loads(path.read_text(encoding="utf-8"))


def command_new(args: argparse.Namespace) -> int:
    resume = args.resume.resolve()
    if not resume.is_file():
        raise RuntimeError(f"Resume not found: {resume}")
    root = Path(args.output_dir).resolve() if args.output_dir else Path.cwd()
    audit_dir = root / args.name
    if audit_dir.exists() and not args.force:
        raise RuntimeError(f"Directory exists: {audit_dir} (use --force to overwrite)")
    audit_dir.mkdir(parents=True, exist_ok=True)
    text = extract_text(resume)
    if not text.strip():
        raise RuntimeError("No extractable text in resume.")
    write_json(manifest_path(audit_dir), {
        "schema_version": SCHEMA_VERSION,
        "name": args.name,
        "resume_file": resume.name,
        "resume_sha256": sha256_file(resume),
        "created_at": utc_now(),
    })
    write_json(ledger_path(audit_dir), {"schema_version": SCHEMA_VERSION, "claims": []})
    (audit_dir / "resume.txt").write_text(text, encoding="utf-8")
    print(str(audit_dir))
    return 0


def command_timeline(args: argparse.Namespace) -> int:
    audit_dir = args.audit_dir.resolve()
    load_manifest(audit_dir)
    text = (audit_dir / "resume.txt").read_text(encoding="utf-8")
    ranges = parse_ranges(text)
    result = check_timeline(ranges)
    # strip internal indexes from output
    clean_ranges = [
        {k: r[k] for k in ("raw", "start", "end", "fuzzy", "reversed")} for r in ranges
    ]
    output = {"ranges": clean_ranges, **result}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def validate_ledger(ledger: dict) -> list[str]:
    errors = []
    if ledger.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    claims = ledger.get("claims")
    if not isinstance(claims, list):
        return errors + ["claims must be a list"]
    seen = set()
    for i, claim in enumerate(claims):
        where = f"claims[{i}]"
        for key in ("id", "text", "location", "check_method", "risk", "reason", "fix"):
            if not claim.get(key):
                errors.append(f"{where}: missing {key}")
        if claim.get("id") in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(claim.get("id"))
        if claim.get("check_method") not in CHECK_METHODS:
            errors.append(f"{where}: check_method must be one of {', '.join(CHECK_METHODS)}")
        if claim.get("risk") not in RISK_ORDER:
            errors.append(f"{where}: risk must be high/medium/low")
    return errors


def command_report(args: argparse.Namespace) -> int:
    audit_dir = args.audit_dir.resolve()
    manifest = load_manifest(audit_dir)
    ledger = json.loads(ledger_path(audit_dir).read_text(encoding="utf-8"))
    errors = validate_ledger(ledger)
    if errors:
        raise RuntimeError("Ledger invalid:\n- " + "\n- ".join(errors))
    claims = sorted(ledger["claims"], key=lambda c: (RISK_ORDER[c["risk"]], c["id"]))
    lines = [
        f"# 背调审计报告 · {manifest['name']}",
        "",
        f"> 审计对象：{manifest['resume_file']}（sha256:{manifest['resume_sha256'][:12]}…）",
        f"> 审计时间：{utc_now()[:10]}",
        "",
    ]
    if not claims:
        lines += ["审计台账为空：还没有写入任何 claim。", ""]
    for risk in ("high", "medium", "low"):
        group = [c for c in claims if c["risk"] == risk]
        if not group:
            continue
        label = {"high": "🔴 高风险", "medium": "🟡 中风险", "low": "🟢 低风险"}[risk]
        lines.append(f"## {label}（{len(group)}）")
        lines.append("")
        for claim in group:
            lines += [
                f"### {claim['id']} · {claim['location']}",
                "",
                f"- **原句**：{claim['text']}",
                f"- **核查方式**：{claim['check_method']}",
                f"- **风险原因**：{claim['reason']}",
                f"- **修复建议**：{claim['fix']}",
                "",
            ]
    lines += ["---", "", f"> {CLOSING_ZH}", ">", f"> {CLOSING_EN}", ""]
    output = "\n".join(lines)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(str(Path(args.output).resolve()))
    else:
        print(output)
    return 0


# ---------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bg_audit.py",
        description="Background-check-proof resume audit.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    new = commands.add_parser("new", help="Start an audit workspace for a resume file")
    new.add_argument("--resume", type=Path, required=True)
    new.add_argument("--name", required=True)
    new.add_argument("--output-dir", type=Path, default=None)
    new.add_argument("--force", action="store_true")
    new.set_defaults(func=command_new)

    timeline = commands.add_parser("timeline", help="Deterministic timeline consistency check")
    timeline.add_argument("audit_dir", type=Path)
    timeline.set_defaults(func=command_timeline)

    report = commands.add_parser("report", help="Render the ranked risk report")
    report.add_argument("audit_dir", type=Path)
    report.add_argument("--output", type=Path, default=None)
    report.set_defaults(func=command_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
