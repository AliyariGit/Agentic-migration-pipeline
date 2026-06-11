using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace LegacyMigration.Services;

/// <summary>
/// Handles order processing operations.
/// Migrated from: legacy/vbscript/ProcessOrder.vbs
/// Migration date: 2026-06-11
/// </summary>
public sealed class OrderService
{
    private readonly AppDbContext _context;
    private readonly ILogger<OrderService> _logger;

    public OrderService(AppDbContext context, ILogger<OrderService> logger)
    {
        _context = context;
        _logger = logger;
    }

    /// <summary>
    /// Updates order status to Processing and deducts customer balance.
    /// Migrated from: Sub ProcessOrder(orderId, customerId, amount)
    /// </summary>
    public async Task ProcessOrderAsync(int orderId, int customerId, decimal amount)
    {
        try
        {
            var order = await _context.Orders.FindAsync(orderId)
                ?? throw new InvalidOperationException($"Order {orderId} not found.");

            order.Status = "Processing";

            var customer = await _context.Customers.FindAsync(customerId)
                ?? throw new InvalidOperationException($"Customer {customerId} not found.");

            customer.Balance -= amount;

            await _context.SaveChangesAsync();

            _logger.LogInformation("Order {OrderId} processed for Customer {CustomerId}", orderId, customerId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to process Order {OrderId}", orderId);
            throw;
        }
    }

    /// <summary>
    /// Returns the total value of all items in an order.
    /// Migrated from: Sub GetOrderTotal(orderId)
    /// </summary>
    public async Task<decimal> GetOrderTotalAsync(int orderId)
    {
        var total = await _context.OrderItems
            .Where(i => i.OrderId == orderId)
            .SumAsync(i => i.Price * i.Quantity);

        _logger.LogInformation("Order {OrderId} total calculated: {Total}", orderId, total);
        return total;
    }

    /// <summary>
    /// Cancels an order and writes an audit log entry.
    /// Migrated from: Sub CancelOrder(orderId, reason)
    /// </summary>
    public async Task CancelOrderAsync(int orderId, string reason)
    {
        try
        {
            var order = await _context.Orders.FindAsync(orderId)
                ?? throw new InvalidOperationException($"Order {orderId} not found.");

            order.Status = "Cancelled";
            order.CancelReason = reason;

            _context.AuditLogs.Add(new AuditLog
            {
                OrderId = orderId,
                Action = "CANCEL",
                Timestamp = DateTime.UtcNow
            });

            await _context.SaveChangesAsync();
            _logger.LogInformation("Order {OrderId} cancelled. Reason: {Reason}", orderId, reason);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to cancel Order {OrderId}", orderId);
            throw;
        }
    }
}
