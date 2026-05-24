"""
=============================================================
run_pipeline.py — MAIN ORCHESTRATOR
=============================================================
Runs all 5 stages of the agentic migration pipeline in sequence.
This is the single entry point to demonstrate the full workflow.

HOW TO RUN:

  Normal run (clean migration):
    python run_pipeline.py

  Demo run (injects failures to show validation + recovery):
    python run_pipeline.py --demo

STAGES:
  Stage 1 — Extractor Agent        → Decomposes legacy files
  Stage 2 — Context Assembler      → Builds context packages
  Stage 3 — Generator              → Produces C# output files
  Stage 4 — Validation Gate        → Scans for regression patterns
  Stage 5 — Recovery Agent         → Applies targeted fixes
=============================================================
"""

import sys
import os
import subprocess
import shutil
from datetime import datetime


def banner(stage_num: int, title: str, description: str):
    print(f"\n{'█' * 60}")
    print(f"  STAGE {stage_num}: {title}")
    print(f"  {description}")
    print(f"{'█' * 60}\n")


def cleanup():
    """Remove previous run outputs for a clean demo."""
    dirs_to_clean = [
        "sample-run",
        "output",
        "validation-reports",
    ]
    for d in dirs_to_clean:
        if os.path.exists(d):
            shutil.rmtree(d)
    print("  [SETUP] Cleaned previous run outputs")


def run_stage(script: str, extra_args: list = []):
    """Runs a stage script and returns success/failure."""
    cmd = [sys.executable, script] + extra_args
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode == 0


def main():
    demo_mode = "--demo" in sys.argv
    start_time = datetime.now()

    print("\n" + "=" * 60)
    print("  AGENTIC MIGRATION PIPELINE — FULL RUN")
    print(f"  Mode: {'DEMO (with injected failures)' if demo_mode else 'Normal'}")
    print(f"  Started: {start_time.strftime('%H:%M:%S')}")
    print("=" * 60)

    # Clean slate
    cleanup()

    # ── STAGE 1: DECOMPOSE ────────────────────────────────────────
    banner(1, "DECOMPOSE", "Breaking legacy files into atomic agent-consumable units")
    if not run_stage("agents/extractor_agent.py"):
        print("❌ Stage 1 failed — stopping pipeline")
        sys.exit(1)

    # ── STAGE 2: CONTEXT ASSEMBLY ─────────────────────────────────
    banner(2, "CONTEXT ASSEMBLY", "Building curated context packages with live schema")
    if not run_stage("agents/context_assembler.py"):
        print("❌ Stage 2 failed — stopping pipeline")
        sys.exit(1)

    # ── STAGE 3: GENERATION ───────────────────────────────────────
    banner(3, "GENERATION", "Producing C# output via structured slash commands")
    if not run_stage("agents/generator.py"):
        print("❌ Stage 3 failed — stopping pipeline")
        sys.exit(1)

    # ── STAGE 4: VALIDATION GATE ──────────────────────────────────
    banner(4, "VALIDATION GATE", "Automated referee scanning for regression patterns")
    validation_args = ["--inject-failure"] if demo_mode else []
    run_stage("agents/enterprise_ai_validation_script.py", validation_args)
    # Validation may exit with issues — that's expected, continue to Stage 5

    # ── STAGE 5: RECOVERY ─────────────────────────────────────────
    banner(5, "RECOVERY", "Applying targeted surgical fixes from validation reports")
    run_stage("agents/recovery_agent.py")

    # ── FINAL SUMMARY ─────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).seconds
    print("\n" + "=" * 60)
    print("  PIPELINE RUN COMPLETE")
    print(f"  Total time: {elapsed}s")
    print()
    print("  OUTPUT FILES PRODUCED:")
    for root, dirs, files in os.walk("output"):
        for file in files:
            print(f"    • {os.path.join(root, file)}")
    print()
    print("  VALIDATION REPORTS:")
    for root, dirs, files in os.walk("validation-reports"):
        for file in files:
            print(f"    • {os.path.join(root, file)}")
    print()
    print("  EXPLORE THE RESULTS:")
    print("    output/Services/OrderService.cs      ← VBScript migration")
    print("    output/Controllers/OrderController.cs ← ASP UI layer")
    print("    output/ViewModels/OrderDetailViewModel.cs")
    print("    output/Views/Order/Detail.cshtml")
    print("    validation-reports/                   ← Structured reports")
    print("    sample-run/                           ← Stage 1 & 2 artifacts")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
