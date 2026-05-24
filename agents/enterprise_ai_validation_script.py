"""
=============================================================
STAGE 4: enterprise_ai_validation_script.py
=============================================================
Automated referee that scans generated C# code for regression
patterns before any human reviews the output.

Every issue is labelled by severity:
  CRITICAL → blocks promotion, must be fixed before recovery
  HIGH     → blocks promotion, must be fixed before recovery
  MEDIUM   → flags for review, recovery recommended

HOW TO RUN:
    python agents/enterprise_ai_validation_script.py

    # To deliberately test a failure (for demo):
    python agents/enterprise_ai_validation_script.py --inject-failure
=============================================================
"""

import re
import json
import os
import glob
import sys
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class ValidationIssue:
    severity: str        # CRITICAL | HIGH | MEDIUM
    pattern_id: str      # machine-readable pattern name
    description: str     # human-readable description
    line_number: int
    line_content: str
    fix_hint: str        # passed to recovery agent


@dataclass
class ValidationReport:
    file: str
    status: str          # PASSED | BLOCKED
    issues: list
    checked_at: str
    issue_count: dict    # {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}


# ── Validation Rules ──────────────────────────────────────────────────────────
# Each rule: (pattern_id, regex, severity, description, fix_hint)

VALIDATION_RULES = [
    # CRITICAL rules
    (
        "sql_string_concatenation",
        r'"\s*(SELECT|UPDATE|INSERT|DELETE)[^"]*"\s*\+',
        "CRITICAL",
        "SQL string concatenation detected — SQL injection vulnerability",
        "Replace with EF Core typed query: _context.Entity.Where(e => e.Id == id)",
    ),
    (
        "bare_catch_block",
        r'catch\s*(\(\s*Exception\s+\w*\s*\))?\s*\{[\s]*\}',
        "CRITICAL",
        "Bare catch block — exception is swallowed silently",
        "Add _logger.LogError(ex, 'message') and re-throw or handle explicitly",
    ),
    (
        "dynamic_keyword",
        r'\bdynamic\b',
        "CRITICAL",
        "Forbidden 'dynamic' keyword — loses type safety, breaks IntelliSense",
        "Replace with explicit typed class or generic <T>",
    ),

    # HIGH rules
    (
        "session_direct_access",
        r'Session\[',
        "HIGH",
        "Direct Session[] access — bypasses auth middleware",
        "Inject ISessionService and call GetCurrentUserId() instead",
    ),
    (
        "response_write",
        r'Response\.Write\(',
        "HIGH",
        "Response.Write detected — UI output must use Razor view",
        "Move output to .cshtml view using @Model.Property syntax",
    ),
    (
        "non_sealed_service",
        r'public\s+class\s+\w+Service\b(?!\s*:)',
        "HIGH",
        "Service class is not sealed — violates architecture contract",
        "Add 'sealed' keyword: public sealed class OrderService",
    ),
    (
        "synchronous_db_call",
        r'\._context\.\w+\.(Find|First|Single|ToList|Sum|Count)\s*\(',
        "HIGH",
        "Synchronous database call — will exhaust thread pool under load",
        "Add Async suffix and await: FindAsync(), FirstOrDefaultAsync(), ToListAsync()",
    ),

    # MEDIUM rules
    (
        "untyped_variable",
        r'\bobject\b\s+\w+\s*=',
        "MEDIUM",
        "Untyped 'object' variable — loses type safety",
        "Replace with explicit type or generic",
    ),
    (
        "missing_null_check",
        r'FindAsync\([^)]+\);(?!\s*\?\?)',
        "MEDIUM",
        "FindAsync result not null-checked — will throw NullReferenceException",
        "Add null check: var x = await _context.X.FindAsync(id) ?? throw new InvalidOperationException(...)",
    ),
]


def validate_file(filepath: str) -> ValidationReport:
    """Scans a single C# file against all validation rules."""
    
    with open(filepath, "r") as f:
        lines = f.readlines()

    issues = []

    for line_num, line in enumerate(lines, start=1):
        for pattern_id, regex, severity, description, fix_hint in VALIDATION_RULES:
            if re.search(regex, line, re.IGNORECASE):
                issues.append(ValidationIssue(
                    severity=severity,
                    pattern_id=pattern_id,
                    description=description,
                    line_number=line_num,
                    line_content=line.strip(),
                    fix_hint=fix_hint,
                ))

    issue_count = {
        "CRITICAL": sum(1 for i in issues if i.severity == "CRITICAL"),
        "HIGH":     sum(1 for i in issues if i.severity == "HIGH"),
        "MEDIUM":   sum(1 for i in issues if i.severity == "MEDIUM"),
    }

    # BLOCKED if any CRITICAL or HIGH issues exist
    status = "PASSED" if issue_count["CRITICAL"] == 0 and issue_count["HIGH"] == 0 else "BLOCKED"

    return ValidationReport(
        file=filepath,
        status=status,
        issues=[asdict(i) for i in issues],
        checked_at=datetime.now().isoformat(),
        issue_count=issue_count,
    )


def inject_failure_for_demo(filepath: str):
    """
    Deliberately inserts bad patterns into a generated file.
    Used to demonstrate the validation gate catching real failures.
    Run with: --inject-failure flag
    """
    if not os.path.exists(filepath):
        return
    with open(filepath, "r") as f:
        content = f.read()

    injected = content + """

    // ⚠️  DELIBERATELY INJECTED BAD CODE (for demo purposes)
    // These patterns will be caught by the validator:

    public void BadMethodOne()
    {
        // CRITICAL: bare catch block
        try { var x = 1; }
        catch { }
    }

    public object BadMethodTwo(int id)
    {
        // HIGH: synchronous DB call (no Async suffix)
        var order = _context.Orders.Find(id);

        // CRITICAL: dynamic keyword
        dynamic result = order;
        return result;
    }

    public async Task BadMethodThree(int id)
    {
        // HIGH: Session direct access
        var userId = Session["UserId"];

        // CRITICAL: SQL string concatenation
        var sql = "SELECT * FROM Orders WHERE Id=" + id;
    }
"""
    with open(filepath, "w") as f:
        f.write(injected)
    print(f"  [DEMO] Injected 5 deliberate failures into {filepath}")


def print_report(report: ValidationReport):
    """Prints a formatted validation report to the console."""
    
    status_icon = "✅ PASSED" if report.status == "PASSED" else "🚫 BLOCKED"
    
    print(f"\n  {'─' * 50}")
    print(f"  File:   {report.file}")
    print(f"  Status: {status_icon}")
    print(f"  Issues: CRITICAL={report.issue_count['CRITICAL']}  HIGH={report.issue_count['HIGH']}  MEDIUM={report.issue_count['MEDIUM']}")

    if report.issues:
        print()
        for issue in report.issues:
            icon = "🔴" if issue["severity"] == "CRITICAL" else ("🟠" if issue["severity"] == "HIGH" else "🟡")
            print(f"  {icon} [{issue['severity']}] {issue['description']}")
            print(f"      Line {issue['line_number']}: {issue['line_content'][:70]}")
            print(f"      Fix: {issue['fix_hint']}")
            print()


def save_report(report: ValidationReport, output_dir: str):
    """Saves the structured JSON report — this is fed back to the recovery agent."""
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.basename(report.file).replace(".cs", "_report.json").replace(".cshtml", "_report.json")
    out_path = os.path.join(output_dir, filename)
    with open(out_path, "w") as f:
        json.dump(asdict(report), f, indent=2)
    return out_path


def run_validator():
    inject_failure = "--inject-failure" in sys.argv

    print("=" * 60)
    print("  STAGE 4: VALIDATION GATE")
    print("  Scanning generated code before any human review")
    if inject_failure:
        print("  ⚠️  DEMO MODE: Injecting deliberate failures")
    print("=" * 60)

    output_files = glob.glob("output/**/*.cs", recursive=True) + \
                   glob.glob("output/**/*.cshtml", recursive=True)

    if not output_files:
        print("\n[ERROR] No output files found.")
        print("  → Run Stage 3 first: python agents/generator.py")
        return

    if inject_failure and output_files:
        # Inject failures into the first .cs file for demo
        cs_files = [f for f in output_files if f.endswith(".cs")]
        if cs_files:
            inject_failure_for_demo(cs_files[0])

    print(f"\n  Scanning {len(output_files)} file(s)...\n")

    all_reports = []
    blocked_files = []
    report_dir = "validation-reports"

    for filepath in sorted(output_files):
        report = validate_file(filepath)
        all_reports.append(report)
        print_report(report)
        report_path = save_report(report, report_dir)
        print(f"  → Report saved: {report_path}")

        if report.status == "BLOCKED":
            blocked_files.append(filepath)

    print(f"\n{'=' * 60}")
    print(f"  VALIDATION SUMMARY")
    print(f"  Total files scanned: {len(all_reports)}")
    print(f"  ✅ Passed: {len(all_reports) - len(blocked_files)}")
    print(f"  🚫 Blocked: {len(blocked_files)}")

    if blocked_files:
        print(f"\n  Files blocked from promotion:")
        for f in blocked_files:
            print(f"    • {f}")
        print(f"\n  Reports saved to: {report_dir}/")
        print(f"  Next step: Run agents/recovery_agent.py (Stage 5)")
    else:
        print(f"\n  ✅ ALL FILES PASSED — ready for human review")

    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    run_validator()
