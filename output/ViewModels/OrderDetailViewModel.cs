namespace LegacyMigration.ViewModels;

/// <summary>
/// Strongly-typed ViewModel for the Order Detail page.
/// Replaces: Request.Form("OrderId") and loose rs.Fields() access
/// Migration date: 2026-05-23
/// </summary>
public sealed class OrderDetailViewModel
{
    public int OrderId { get; set; }
    public string CustomerName { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public decimal Total { get; set; }
    public bool IsAdmin { get; set; }
    public List<OrderItemViewModel> Items { get; set; } = new();
}

public sealed class OrderItemViewModel
{
    public string ProductName { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public int Quantity { get; set; }
    public decimal LineTotal => Price * Quantity;
}

public sealed class CancelOrderViewModel
{
    public int OrderId { get; set; }
    public string? Reason { get; set; }
}
