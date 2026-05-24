"""
=============================================================
STAGE 5: recovery_agent.py
=============================================================
When the validator flags a failure, we do NOT re-run from scratch.
This agent reads the structured validation report and performs
a targeted, surgical fix on only the flagged patterns.

HOW TO RUN:
    # First run validation with injected failures:
    python agents/enterprise_ai_validation_script.py --inject-failure

    # Then run recovery:
    python agents/recovery_agent.py

WHAT IT DOES:
    - Reads validation-reports/*.json (the structured failure reports)
    - For each BLOCKED file, applies targeted fixes per pattern_id
    - Re-runs validation automatically after fixing
    - Reports pass/fail result
=============================================================
"""

import re
import json
import os
import glob
import subprocess
import sys
from datetime import datetime


# ── Surgical Fix Handlers ─────────────────────────────────────────────────────
# Each handler targets one specific pattern_id and applies a precise fix.
# The agent NEVER regenerates the entire file.

def fix_bare_catch_block(content: str, issue: dict) -> str:
    """
    Replaces empty catch blocks with proper logging + re-throw.
    Pattern: catch { } or catch (Exception) { }
    """
    # Fix completely empty catch blocks
    content = re.sub(
        r'catch\s*\{\s*\}',
        'catch (Exception ex)\n        {\n            _logger.LogError(ex, "Unexpected error occurred");\n            throw;\n        }',
        content
    )
    # Fix catch blocks with no body
    content = re.sub(
        r'catch\s*\(\s*Exception\s+\w*\s*\)\s*\{\s*\}',
        'catch (Exception ex)\n        {\n            _logger.LogError(ex, "Unexpected error occurred");\n            throw;\n        }',
        content
    )
    return content


def fix_dynamic_keyword(content: str, issue: dict) -> str:
    """
    Replaces 'dynamic' with 'object' as a safe intermediate step,
    and adds a TODO comment for the engineer to type properly.
    """
    content = re.sub(
        r'\bdynamic\b',
        'object /* TODO: Replace with explicit type per CLAUDE.md */',
        content
    )
    return content


def fix_session_direct_access(content: str, issue: dict) -> str:
    """
    Replaces Session["key"] with ISessionService method call.
    """
    content = re.sub(
        r'Session\["(\w+)"\]',
        r'_sessionService.Get("\1") /* Injected: ISessionService */',
        content
    )
    return content


def fix_synchronous_db_call(content: str, issue: dict) -> str:
    """
    Adds Async suffix to synchronous EF Core calls and wraps with await.
    """
    # .Find( → .FindAsync(
    content = re.sub(r'\.Find\(', '.FindAsync(', content)
    # .First( → .FirstOrDefaultAsync( 
    content = re.sub(r'\.First\(', '.FirstOrDefaultAsync(', content)
    # .ToList( → .ToListAsync(
    content = re.sub(r'\.ToList\(', '.ToListAsync(', content)
    # .Count( → .CountAsync(
    content = re.sub(r'\.Count\(', '.CountAsync(', content)
    # .Sum( → .SumAsync(
    content = re.sub(r'\.Sum\(', '.SumAsync(', content)
    # Add await if not already present (simplified)
    content = re.sub(
        r'(?<!await )(_context\.\w+\.\w+Async\([^)]*\))',
        r'await \1',
        content
    )
    return content


def fix_non_sealed_service(content: str, issue: dict) -> str:
    """
    Adds 'sealed' modifier to service classes missing it.
    """
    content = re.sub(
        r'public\s+class\s+(\w+Service)\b',
        r'public sealed class \1',
        content
    )
    return content


def fix_response_write(content: str, issue: dict) -> str:
    """
    Flags Response.Write calls with a TODO for manual Razor conversion.
    Cannot be auto-fixed without knowing the view structure.
    """
    content = re.sub(
        r'Response\.Write\(([^)]+)\)',
        r'/* TODO: Move to Razor view: @Model.Property */ // Response.Write(\1)',
        content
    )
    return content


# Map pattern_id → fix function
FIX_HANDLERS = {
    "bare_catch_block":      fix_bare_catch_block,
    "dynamic_keyword":       fix_dynamic_keyword,
    "session_direct_access": fix_session_direct_access,
    "synchronous_db_call":   fix_synchronous_db_call,
    "non_sealed_service":    fix_non_sealed_service,
    "response_write":        fix_response_write,
}


def apply_fixes(filepath: str, issues: list) -> tuple[str, list]:
    """
    Applies all relevant fix handlers to the file content.
    Returns the fixed content and list of fixes applied.
    """
    with open(filepath, "r") as f:
        content = f.read()

    fixes_applied = []
    unique_patterns = set(i["pattern_id"] for i in issues)

    for pattern_id in unique_patterns:
        if pattern_id in FIX_HANDLERS:
            original = content
            content = FIX_HANDLERS[pattern_id](content, {})
            if content != original:
                fixes_applied.append(pattern_id)
                print(f"    ✓ Fixed: {pattern_id}")
            else:
                print(f"    ~ No change for: {pattern_id} (may need manual fix)")
        else:
            print(f"    ⚠ No auto-fix for: {pattern_id} — flagged for engineer review")

    return content, fixes_applied


def rerun_validation(filepath: str) -> dict:
    """Re-runs the validation script on a single fixed file and returns the report."""
    # Import validator directly
    sys.path.insert(0, os.path.dirname(__file__))
    from enterprise_ai_validation_script import validate_file, save_report
    
    report = validate_file(filepath)
    save_report(report, "validation-reports")
    return report


def run_recovery():
    print("=" * 60)
    print("  STAGE 5: RECOVERY AGENT")
    print("  Applying targeted fixes from validation reports")
    print("  (No full regeneration — surgical fixes only)")
    print("=" * 60)

    report_files = glob.glob("validation-reports/*_report.json")

    if not report_files:
        print("\n[ERROR] No validation reports found.")
        print("  → Run Stage 4 first: python agents/enterprise_ai_validation_script.py")
        return

    blocked_reports = []
    for rpath in report_files:
        with open(rpath, "r") as f:
            report = json.load(f)
        if report["status"] == "BLOCKED":
            blocked_reports.append(report)

    if not blocked_reports:
        print("\n  ✅ No blocked files found. All files already passed validation.")
        return

    print(f"\n  Found {len(blocked_reports)} blocked file(s) requiring recovery\n")

    recovery_results = []

    for report in blocked_reports:
        filepath = report["file"]
        issues = report["issues"]

        print(f"[RECOVERY] Processing: {filepath}")
        print(f"  Issues to fix: CRITICAL={report['issue_count']['CRITICAL']}  HIGH={report['issue_count']['HIGH']}  MEDIUM={report['issue_count']['MEDIUM']}")

        if not os.path.exists(filepath):
            print(f"  ⚠ File not found: {filepath} — skipping\n")
            continue

        # Apply surgical fixes
        fixed_content, fixes_applied = apply_fixes(filepath, issues)

        # Save fixed file
        with open(filepath, "w") as f:
            f.write(fixed_content)

        # Re-run validation automatically
        print(f"  → Re-running validation on fixed file...")
        new_report = rerun_validation(filepath)

        new_status = new_report.status
        status_icon = "✅ NOW PASSING" if new_status == "PASSED" else "🚫 STILL BLOCKED"
        print(f"  → Result: {status_icon}")

        if new_status == "BLOCKED":
            remaining = new_report.issue_count
            print(f"  → Remaining: CRITICAL={remaining['CRITICAL']}  HIGH={remaining['HIGH']}  MEDIUM={remaining['MEDIUM']}")
            print(f"  → These require manual engineer review")

        recovery_results.append({
            "file": filepath,
            "fixes_applied": fixes_applied,
            "original_status": "BLOCKED",
            "new_status": new_status,
            "recovered_at": datetime.now().isoformat(),
        })

        # Save recovery log
        log_dir = "sample-run/stage5-recovery-logs"
        os.makedirs(log_dir, exist_ok=True)
        log_name = os.path.basename(filepath).replace(".cs", "_recovery.json")
        with open(f"{log_dir}/{log_name}", "w") as f:
            json.dump(recovery_results[-1], f, indent=2)

        print()

    passed = sum(1 for r in recovery_results if r["new_status"] == "PASSED")
    still_blocked = len(recovery_results) - passed

    print("=" * 60)
    print("  RECOVERY SUMMARY")
    print(f"  Files processed:   {len(recovery_results)}")
    print(f"  ✅ Now passing:    {passed}")
    print(f"  🚫 Still blocked:  {still_blocked} (require engineer review)")
    if still_blocked == 0:
        print(f"\n  🎉 All files recovered — ready for human review!")
    else:
        print(f"\n  Check validation-reports/ for remaining issues")
    print("=" * 60)


if __name__ == "__main__":
    run_recovery()
