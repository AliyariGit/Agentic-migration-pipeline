"""
=============================================================
STAGE 1: extractor_agent.py
=============================================================
Decomposes legacy files into atomic, agent-consumable units.
No code generation happens here — ONLY structural analysis.

HOW TO RUN:
    python agents/extractor_agent.py

WHAT IT DOES:
    - VBScript: splits by Sub/Function boundaries
    - Classic ASP: splits into SQL DAL layer + UI/Response layer
    - Saves each unit as a separate JSON file for Stage 2
=============================================================
"""

import re
import json
import os
from pathlib import Path
from datetime import datetime


def extract_vbscript_units(filepath: str) -> list[dict]:
    """
    Splits a VBScript file into isolated Sub/Function units.
    Each unit becomes one atomic work item for the generation agent.
    """
    print(f"\n[EXTRACTOR] Processing VBScript: {filepath}")
    
    with open(filepath, "r") as f:
        content = f.read()

    units = []
    
    # Find all Sub and Function blocks
    pattern = r"((?:Sub|Function)\s+\w+.*?End\s+(?:Sub|Function))"
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)

    for i, block in enumerate(matches):
        # Extract the name
        name_match = re.search(r"(?:Sub|Function)\s+(\w+)", block, re.IGNORECASE)
        name = name_match.group(1) if name_match else f"Unit_{i+1}"
        unit_type = "Function" if block.strip().lower().startswith("function") else "Sub"
        
        # Detect COM object usage (needs registry mapping)
        com_objects = re.findall(r'CreateObject\("([^"]+)"\)', block)
        
        # Detect SQL patterns (injection risks)
        sql_patterns = re.findall(r'(?:Execute|Open)\s*"([^"]*(?:SELECT|UPDATE|INSERT|DELETE)[^"]*)"', block, re.IGNORECASE)
        
        unit = {
            "unit_id": f"vbs_{name.lower()}_{i+1}",
            "source_file": filepath,
            "unit_type": unit_type,
            "name": name,
            "legacy_code": block.strip(),
            "metadata": {
                "com_objects_detected": com_objects,
                "sql_patterns_detected": len(sql_patterns),
                "has_error_handling": "On Error" in block,
                "has_sql_injection_risk": any("&" in s for s in sql_patterns),
            },
            "migration_target": f"public async Task {name}Async(...) in OrderService.cs",
            "extracted_at": datetime.now().isoformat(),
        }
        units.append(unit)
        print(f"  ✓ Extracted unit: [{unit_type}] {name}")

    return units


def extract_asp_units(filepath: str) -> list[dict]:
    """
    Splits a Classic ASP file into TWO separate layers:
      1. SQL Data Access Layer (string-concatenated queries)
      2. UI/Response Layer (Response.Write calls + HTML)
    
    These are migrated independently by different slash commands.
    """
    print(f"\n[EXTRACTOR] Processing Classic ASP: {filepath}")

    with open(filepath, "r") as f:
        content = f.read()

    units = []

    # --- UNIT 1: SQL DATA ACCESS LAYER ---
    sql_blocks = re.findall(r'(?:conn\.Execute|\.Open)\s*["\(]([^"\']+(?:SELECT|UPDATE|INSERT|DELETE|JOIN)[^"\']*)["\)]', content, re.IGNORECASE)
    form_inputs = re.findall(r'Request\.Form\("([^"]+)"\)', content)
    session_access = re.findall(r'Session\("([^"]+)"\)', content)

    dal_unit = {
        "unit_id": "asp_dal_order_detail",
        "source_file": filepath,
        "layer": "DATA_ACCESS_LAYER",
        "description": "SQL queries and database connections extracted from order_detail.asp",
        "legacy_queries": sql_blocks,
        "form_inputs_detected": form_inputs,
        "session_access_detected": session_access,
        "injection_risks": [q for q in sql_blocks if "+" in q or "&" in q],
        "migration_target": "EF Core DbContext — AppDbContext.Orders, AppDbContext.OrderItems",
        "slash_command": "/modernize-asp-dal",
        "extracted_at": datetime.now().isoformat(),
    }
    units.append(dal_unit)
    print(f"  ✓ Extracted layer: DATA_ACCESS_LAYER ({len(sql_blocks)} queries, {len(form_inputs)} form inputs)")

    # --- UNIT 2: UI / RESPONSE LAYER ---
    response_writes = re.findall(r'Response\.Write\(([^)]+)\)', content)
    html_blocks = re.findall(r'<[^%][^>]*>.*?</[^>]+>', content, re.DOTALL)

    ui_unit = {
        "unit_id": "asp_ui_order_detail",
        "source_file": filepath,
        "layer": "UI_RESPONSE_LAYER",
        "description": "Response.Write calls and HTML markup extracted from order_detail.asp",
        "response_write_count": len(response_writes),
        "business_logic_in_view": bool(session_access),  # logic leak detected
        "migration_target": "OrderController.cs + OrderDetailViewModel.cs + Views/Order/Detail.cshtml",
        "slash_command": "/modernize-asp-view",
        "warnings": ["Business logic detected in view layer — will be moved to Controller/Service during migration"],
        "extracted_at": datetime.now().isoformat(),
    }
    units.append(ui_unit)
    print(f"  ✓ Extracted layer: UI_RESPONSE_LAYER ({len(response_writes)} Response.Write calls)")
    if session_access:
        print(f"  ⚠  WARNING: Business logic detected in view (Session access) — will be flagged")

    return units


def save_units(units: list[dict], output_dir: str):
    """Saves each extracted unit as a JSON file for Stage 2 (Context Assembly)."""
    os.makedirs(output_dir, exist_ok=True)
    saved = []
    for unit in units:
        filename = f"{unit['unit_id']}.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            json.dump(unit, f, indent=2)
        saved.append(filepath)
        print(f"  → Saved unit: {filename}")
    return saved


def run_extractor():
    print("=" * 60)
    print("  STAGE 1: EXTRACTOR AGENT")
    print("  Breaking legacy files into atomic agent-consumable units")
    print("=" * 60)

    output_dir = "sample-run/stage1-extracted-units"
    all_units = []

    # Process VBScript files
    vbs_dir = Path("legacy/vbscript")
    for vbs_file in vbs_dir.glob("*.vbs"):
        units = extract_vbscript_units(str(vbs_file))
        all_units.extend(units)

    # Process Classic ASP files
    asp_dir = Path("legacy/classic-asp")
    for asp_file in asp_dir.glob("*.asp"):
        units = extract_asp_units(str(asp_file))
        all_units.extend(units)

    print(f"\n[EXTRACTOR] Saving {len(all_units)} units to {output_dir}/")
    saved = save_units(all_units, output_dir)

    print(f"\n{'=' * 60}")
    print(f"  ✅ STAGE 1 COMPLETE")
    print(f"  Extracted {len(all_units)} atomic units from legacy files")
    print(f"  Output: {output_dir}/")
    print(f"  Next step: Run agents/context_assembler.py (Stage 2)")
    print(f"{'=' * 60}\n")

    return all_units


if __name__ == "__main__":
    run_extractor()
