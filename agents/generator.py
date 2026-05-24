"""
=============================================================
STAGE 3: generator.py
=============================================================
Reads context packages from Stage 2 and produces C# output.
In production this calls Claude API with the context package.
Here we generate realistic sample output files to demonstrate
what the agent produces for each slash command.

HOW TO RUN:
    python agents/generator.py

WHAT IT PRODUCES:
    VBScript unit  → output/Services/OrderService.cs
    ASP UI layer   → output/Controllers/ + ViewModels/ + Views/
    ASP DAL layer  → output/Services/OrderDataService.cs
=============================================================
"""

import json
import os
import glob
from datetime import datetime


# ── Generated C# Output Templates ────────────────────────────────────────────
# These represent exactly what the Claude agent produces when given the
# context package + slash command. The code follows ALL CLAUDE.md rules.

VBSCRIPT_SERVICE_OUTPUT = '''using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace LegacyMigration.Services;

/// <summary>
/// Handles order processing operations.
/// Migrated from: legacy/vbscript/ProcessOrder.vbs
/// Migration date: {date}
/// </summary>
public sealed class OrderService
{{
    private readonly AppDbContext _context;
    private readonly ILogger<OrderService> _logger;

    public OrderService(AppDbContext context, ILogger<OrderService> logger)
    {{
        _context = context;
        _logger = logger;
    }}

    /// <summary>
    /// Updates order status to Processing and deducts customer balance.
    /// Migrated from: Sub ProcessOrder(orderId, customerId, amount)
    /// </summary>
    public async Task ProcessOrderAsync(int orderId, int customerId, decimal amount)
    {{
        try
        {{
            var order = await _context.Orders.FindAsync(orderId)
                ?? throw new InvalidOperationException($"Order {{orderId}} not found.");

            order.Status = "Processing";

            var customer = await _context.Customers.FindAsync(customerId)
                ?? throw new InvalidOperationException($"Customer {{customerId}} not found.");

            customer.Balance -= amount;

            await _context.SaveChangesAsync();

            _logger.LogInformation("Order {{OrderId}} processed for Customer {{CustomerId}}", orderId, customerId);
        }}
        catch (Exception ex)
        {{
            _logger.LogError(ex, "Failed to process Order {{OrderId}}", orderId);
            throw;
        }}
    }}

    /// <summary>
    /// Returns the total value of all items in an order.
    /// Migrated from: Sub GetOrderTotal(orderId)
    /// </summary>
    public async Task<decimal> GetOrderTotalAsync(int orderId)
    {{
        var total = await _context.OrderItems
            .Where(i => i.OrderId == orderId)
            .SumAsync(i => i.Price * i.Quantity);

        _logger.LogInformation("Order {{OrderId}} total calculated: {{Total}}", orderId, total);
        return total;
    }}

    /// <summary>
    /// Cancels an order and writes an audit log entry.
    /// Migrated from: Sub CancelOrder(orderId, reason)
    /// </summary>
    public async Task CancelOrderAsync(int orderId, string reason)
    {{
        try
        {{
            var order = await _context.Orders.FindAsync(orderId)
                ?? throw new InvalidOperationException($"Order {{orderId}} not found.");

            order.Status = "Cancelled";
            order.CancelReason = reason;

            _context.AuditLogs.Add(new AuditLog
            {{
                OrderId = orderId,
                Action = "CANCEL",
                Timestamp = DateTime.UtcNow
            }});

            await _context.SaveChangesAsync();
            _logger.LogInformation("Order {{OrderId}} cancelled. Reason: {{Reason}}", orderId, reason);
        }}
        catch (Exception ex)
        {{
            _logger.LogError(ex, "Failed to cancel Order {{OrderId}}", orderId);
            throw;
        }}
    }}
}}
'''

CONTROLLER_OUTPUT = '''using Microsoft.AspNetCore.Mvc;
using LegacyMigration.Services;
using LegacyMigration.ViewModels;

namespace LegacyMigration.Controllers;

/// <summary>
/// Handles order detail views and order actions.
/// Migrated from: legacy/classic-asp/order_detail.asp (UI layer)
/// Migration date: {date}
/// </summary>
public sealed class OrderController : Controller
{{
    private readonly OrderService _orderService;
    private readonly ILogger<OrderController> _logger;

    public OrderController(OrderService orderService, ILogger<OrderController> logger)
    {{
        _orderService = orderService;
        _logger = logger;
    }}

    /// <summary>
    /// Displays order detail page.
    /// Migrated from: order_detail.asp (replaced Response.Write with Razor view)
    /// </summary>
    [HttpGet]
    public async Task<IActionResult> Detail(int orderId)
    {{
        try
        {{
            var viewModel = await _orderService.GetOrderDetailViewModelAsync(orderId);
            return View(viewModel);
        }}
        catch (Exception ex)
        {{
            _logger.LogError(ex, "Failed to load Order {{OrderId}}", orderId);
            return NotFound();
        }}
    }}

    /// <summary>
    /// Cancels an order via POST.
    /// Migrated from: cancel_order.asp form action
    /// </summary>
    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Cancel([FromForm] CancelOrderViewModel model)
    {{
        if (!ModelState.IsValid)
            return View("Detail", await _orderService.GetOrderDetailViewModelAsync(model.OrderId));

        await _orderService.CancelOrderAsync(model.OrderId, model.Reason ?? "User requested");
        return RedirectToAction("Detail", new {{ orderId = model.OrderId }});
    }}
}}
'''

VIEWMODEL_OUTPUT = '''namespace LegacyMigration.ViewModels;

/// <summary>
/// Strongly-typed ViewModel for the Order Detail page.
/// Replaces: Request.Form("OrderId") and loose rs.Fields() access
/// Migration date: {date}
/// </summary>
public sealed class OrderDetailViewModel
{{
    public int OrderId {{ get; set; }}
    public string CustomerName {{ get; set; }} = string.Empty;
    public string Status {{ get; set; }} = string.Empty;
    public decimal Total {{ get; set; }}
    public bool IsAdmin {{ get; set; }}
    public List<OrderItemViewModel> Items {{ get; set; }} = new();
}}

public sealed class OrderItemViewModel
{{
    public string ProductName {{ get; set; }} = string.Empty;
    public decimal Price {{ get; set; }}
    public int Quantity {{ get; set; }}
    public decimal LineTotal => Price * Quantity;
}}

public sealed class CancelOrderViewModel
{{
    public int OrderId {{ get; set; }}
    public string? Reason {{ get; set; }}
}}
'''

RAZOR_VIEW_OUTPUT = '''@model LegacyMigration.ViewModels.OrderDetailViewModel
@* Migrated from: legacy/classic-asp/order_detail.asp (UI layer)
   Replaces: All Response.Write(...) calls
   Migration date: {date} *@

@{{
    ViewData["Title"] = $"Order #{{Model.OrderId}}";
}}

<h1>Order Detail</h1>

@if (Model.IsAdmin)
{{
    <div class="admin-banner">
        <strong>Admin View</strong> — Customer: @Model.CustomerName
    </div>
}}

<dl>
    <dt>Order ID</dt>
    <dd>@Model.OrderId</dd>

    <dt>Customer</dt>
    <dd>@Model.CustomerName</dd>

    <dt>Status</dt>
    <dd><span class="badge">@Model.Status</span></dd>

    <dt>Total</dt>
    <dd>@Model.Total.ToString("C")</dd>
</dl>

<h2>Items</h2>
<ul>
    @foreach (var item in Model.Items)
    {{
        <li>@item.ProductName — @item.Price.ToString("C") × @item.Quantity = @item.LineTotal.ToString("C")</li>
    }}
</ul>

<form asp-action="Cancel" asp-controller="Order" method="post">
    @Html.AntiForgeryToken()
    <input type="hidden" asp-for="OrderId" />
    <button type="submit" class="btn-danger">Cancel Order</button>
</form>
'''


def run_generator():
    print("=" * 60)
    print("  STAGE 3: GENERATOR")
    print("  Producing C# output from context packages + slash commands")
    print("=" * 60)

    input_dir = "sample-run/stage2-context-packages"
    context_files = glob.glob(f"{input_dir}/*.json")

    if not context_files:
        print(f"\n[ERROR] No context packages found in {input_dir}/")
        print("  → Run Stage 2 first: python agents/context_assembler.py")
        return

    date = datetime.now().strftime("%Y-%m-%d")
    generated = []

    for ctx_file in context_files:
        with open(ctx_file, "r") as f:
            ctx = json.load(f)

        unit_id = ctx["unit_id"]
        slash_cmd = ctx["slash_command"]
        print(f"\n[GENERATOR] Unit: {unit_id}")
        print(f"  Slash command: {slash_cmd}")

        # Route to correct output template based on slash command
        if slash_cmd == "/map-vbscript-to-logic":
            out_path = "output/Services/OrderService.cs"
            content = VBSCRIPT_SERVICE_OUTPUT.format(date=date)
            print(f"  → Generating: sealed OrderService class (3 async methods)")

        elif slash_cmd == "/modernize-asp-view":
            # One .asp file → THREE output files
            os.makedirs("output/Controllers", exist_ok=True)
            os.makedirs("output/ViewModels", exist_ok=True)
            os.makedirs("output/Views/Order", exist_ok=True)

            for path, content_template in [
                ("output/Controllers/OrderController.cs", CONTROLLER_OUTPUT),
                ("output/ViewModels/OrderDetailViewModel.cs", VIEWMODEL_OUTPUT),
                ("output/Views/Order/Detail.cshtml", RAZOR_VIEW_OUTPUT),
            ]:
                c = content_template.format(date=date)
                with open(path, "w") as f:
                    f.write(c)
                generated.append(path)
                print(f"  → Generated: {path}")
            continue  # Already saved above

        elif slash_cmd == "/modernize-asp-dal":
            out_path = "output/Services/OrderDataService.cs"
            content = "// DAL layer migrated to AppDbContext — see OrderService.cs for EF Core queries\n"
            print(f"  → DAL layer merged into OrderService (EF Core queries)")

        else:
            print(f"  ⚠  Unknown slash command: {slash_cmd} — skipping")
            continue

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            f.write(content)
        generated.append(out_path)
        print(f"  → Generated: {out_path}")

    print(f"\n{'=' * 60}")
    print(f"  ✅ STAGE 3 COMPLETE")
    print(f"  Generated {len(generated)} output file(s)")
    for g in generated:
        print(f"    • {g}")
    print(f"  Next step: Run agents/enterprise_ai_validation_script.py (Stage 4)")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    run_generator()
