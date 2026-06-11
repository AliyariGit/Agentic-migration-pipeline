using Microsoft.AspNetCore.Mvc;
using LegacyMigration.Services;
using LegacyMigration.ViewModels;

namespace LegacyMigration.Controllers;

/// <summary>
/// Handles order detail views and order actions.
/// Migrated from: legacy/classic-asp/order_detail.asp (UI layer)
/// Migration date: 2026-06-11
/// </summary>
public sealed class OrderController : Controller
{
    private readonly OrderService _orderService;
    private readonly ILogger<OrderController> _logger;

    public OrderController(OrderService orderService, ILogger<OrderController> logger)
    {
        _orderService = orderService;
        _logger = logger;
    }

    /// <summary>
    /// Displays order detail page.
    /// Migrated from: order_detail.asp (replaced Response.Write with Razor view)
    /// </summary>
    [HttpGet]
    public async Task<IActionResult> Detail(int orderId)
    {
        try
        {
            var viewModel = await _orderService.GetOrderDetailViewModelAsync(orderId);
            return View(viewModel);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to load Order {OrderId}", orderId);
            return NotFound();
        }
    }

    /// <summary>
    /// Cancels an order via POST.
    /// Migrated from: cancel_order.asp form action
    /// </summary>
    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Cancel([FromForm] CancelOrderViewModel model)
    {
        if (!ModelState.IsValid)
            return View("Detail", await _orderService.GetOrderDetailViewModelAsync(model.OrderId));

        await _orderService.CancelOrderAsync(model.OrderId, model.Reason ?? "User requested");
        return RedirectToAction("Detail", new { orderId = model.OrderId });
    }
}
