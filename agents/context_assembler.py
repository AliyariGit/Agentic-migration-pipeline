"""
=============================================================
STAGE 2: context_assembler.py
=============================================================
Assembles a curated context package for each extracted unit.
This is what the agent receives before generating any code.

Simulates the MCP server by reading local schema files.
In production, this pulls live schema from the MCP server.

HOW TO RUN:
    python agents/context_assembler.py

WHAT IT DOES:
    - Reads extracted units from Stage 1 output
    - Loads CLAUDE.md rulebook
    - Loads migration-patterns.md dictionary
    - Loads (simulated) database schema from MCP
    - Assembles a complete context package per unit
    - Saves context packages as JSON for the generation step
=============================================================
"""

import json
import os
import glob
from datetime import datetime


# ── Simulated MCP Server ──────────────────────────────────────────────────────
# In production this calls your actual MCP server endpoint.
# Here we simulate it returning the live EF Core entity schema.

MCP_SCHEMA = {
    "entities": {
        "Order": {
            "table": "Orders",
            "properties": {
                "Id": "int (PK)",
                "CustomerId": "int (FK → Customers.Id)",
                "Status": "string (Processing | Cancelled | Complete)",
                "Total": "decimal",
                "CancelReason": "string?",
                "CreatedAt": "DateTime",
            },
            "ef_core_dbset": "DbSet<Order> Orders",
        },
        "Customer": {
            "table": "Customers",
            "properties": {
                "Id": "int (PK)",
                "Name": "string",
                "Balance": "decimal",
                "Email": "string",
            },
            "ef_core_dbset": "DbSet<Customer> Customers",
        },
        "OrderItem": {
            "table": "OrderItems",
            "properties": {
                "Id": "int (PK)",
                "OrderId": "int (FK → Orders.Id)",
                "ProductName": "string",
                "Price": "decimal",
                "Quantity": "int",
            },
            "ef_core_dbset": "DbSet<OrderItem> OrderItems",
        },
        "AuditLog": {
            "table": "AuditLog",
            "properties": {
                "Id": "int (PK)",
                "OrderId": "int (FK → Orders.Id)",
                "Action": "string",
                "Timestamp": "DateTime",
            },
            "ef_core_dbset": "DbSet<AuditLog> AuditLogs",
        },
    }
}


def load_file(path: str) -> str:
    """Load a governance file into the context package."""
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"[WARNING: {path} not found]"


def fetch_mcp_schema(unit: dict) -> dict:
    """
    Simulates MCP server call.
    Returns only the schema entities relevant to this unit.
    In production: GET https://your-mcp-server/schema?context={unit_id}
    """
    print(f"  [MCP] Fetching live schema for unit: {unit['unit_id']}")
    # Return full schema (in production, MCP filters by relevance)
    return MCP_SCHEMA


def determine_slash_command(unit: dict) -> str:
    """Selects the correct slash command template for this unit."""
    if unit.get("unit_type") in ["Sub", "Function"]:
        return "/map-vbscript-to-logic"
    elif unit.get("layer") == "DATA_ACCESS_LAYER":
        return "/modernize-asp-dal"
    elif unit.get("layer") == "UI_RESPONSE_LAYER":
        return "/modernize-asp-view"
    return "/generic-migration"


def assemble_context(unit: dict) -> dict:
    """
    Builds the complete context package for one extracted unit.
    This is everything the generation agent needs — nothing more, nothing less.
    """
    slash_command = determine_slash_command(unit)

    context_package = {
        "unit_id": unit["unit_id"],
        "assembled_at": datetime.now().isoformat(),
        "slash_command": slash_command,

        # The governance rulebook — agent must follow ALL rules
        "rulebook": load_file("CLAUDE.md"),

        # The translation dictionary — maps legacy patterns to modern equivalents
        "migration_patterns": load_file("migration-patterns.md"),

        # Live schema from MCP server — eliminates hallucination of table/column names
        "live_schema": fetch_mcp_schema(unit),

        # The actual unit to migrate
        "target_unit": unit,

        # Explicit instructions passed to the generation agent
        "agent_instructions": build_instructions(unit, slash_command),
    }

    return context_package


def build_instructions(unit: dict, slash_command: str) -> str:
    """Builds the structured instruction block for the generation agent."""
    
    if unit.get("unit_type") in ["Sub", "Function"]:
        return f"""
SLASH COMMAND: {slash_command}
TASK: Migrate the VBScript {unit['unit_type']} '{unit['name']}' to a C# async method.

RULES (from CLAUDE.md — non-negotiable):
1. Output class MUST be sealed
2. Method MUST be async Task or async Task<T>
3. NO SQL strings — use EF Core entities from the live schema
4. NO bare catch blocks — log all exceptions
5. ALL dependencies via constructor injection
6. XML doc comment on the method

OUTPUT STRUCTURE:
- One sealed C# service class
- One async method per legacy Sub/Function
- Place in: output/Services/OrderService.cs

COM OBJECTS DETECTED: {unit['metadata'].get('com_objects_detected', [])}
→ Replace with: constructor-injected AppDbContext

SQL INJECTION RISKS DETECTED: {unit['metadata'].get('has_sql_injection_risk', False)}
→ Replace ALL SQL strings with EF Core typed queries
""".strip()

    elif unit.get("layer") == "UI_RESPONSE_LAYER":
        return f"""
SLASH COMMAND: {slash_command}
TASK: Migrate the Classic ASP UI layer to Razor MVC (3 output files).

RULES (from CLAUDE.md — non-negotiable):
1. NO Response.Write — all output via Razor @Model syntax
2. NO Session[] direct access — use ISessionService
3. Business logic detected in view — move to Controller/Service
4. ViewModel must be strongly typed

OUTPUT STRUCTURE (3 files from 1 .asp file):
  File 1: output/Controllers/OrderController.cs  (async action methods)
  File 2: output/ViewModels/OrderDetailViewModel.cs  (typed properties)
  File 3: output/Views/Order/Detail.cshtml  (Razor view, @model OrderDetailViewModel)

WARNINGS TO ADDRESS: {unit.get('warnings', [])}
""".strip()

    else:
        return f"""
SLASH COMMAND: {slash_command}
TASK: Migrate the Classic ASP DAL layer to EF Core.

RULES:
1. Replace ALL SQL string concatenation with EF Core typed queries
2. Use live schema entities: Order, Customer, OrderItem, AuditLog
3. Async/await all database calls

SQL INJECTION RISKS: {unit.get('injection_risks', [])}
→ Each must be replaced with a parameterized EF Core call
""".strip()


def run_assembler():
    print("=" * 60)
    print("  STAGE 2: CONTEXT ASSEMBLER")
    print("  Building curated context packages for each extracted unit")
    print("=" * 60)

    input_dir = "sample-run/stage1-extracted-units"
    output_dir = "sample-run/stage2-context-packages"
    os.makedirs(output_dir, exist_ok=True)

    unit_files = glob.glob(f"{input_dir}/*.json")
    if not unit_files:
        print(f"\n[ERROR] No units found in {input_dir}/")
        print("  → Run Stage 1 first: python agents/extractor_agent.py")
        return

    print(f"\n  Found {len(unit_files)} unit(s) to process\n")

    for unit_file in unit_files:
        with open(unit_file, "r") as f:
            unit = json.load(f)

        print(f"[ASSEMBLER] Building context for: {unit['unit_id']}")
        context = assemble_context(unit)

        out_path = os.path.join(output_dir, f"{unit['unit_id']}_context.json")
        with open(out_path, "w") as f:
            json.dump(context, f, indent=2)

        print(f"  → Slash command selected: {context['slash_command']}")
        print(f"  → Context package saved: {os.path.basename(out_path)}")
        print()

    print("=" * 60)
    print("  ✅ STAGE 2 COMPLETE")
    print(f"  Built {len(unit_files)} context packages")
    print(f"  Output: {output_dir}/")
    print("  Next step: Run agents/generator.py (Stage 3)")
    print("=" * 60)


if __name__ == "__main__":
    run_assembler()
