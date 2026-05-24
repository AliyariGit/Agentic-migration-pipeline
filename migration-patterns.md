# migration-patterns.md — Legacy → Modern Translation Dictionary

## VBScript → C# Patterns

| Legacy (VBScript)              | Modern (.NET Core)                        |
|-------------------------------|-------------------------------------------|
| `Dim x`                       | `var x` or explicit typed declaration     |
| `Sub ProcessOrder()`          | `public async Task ProcessOrderAsync()`   |
| `Function GetTotal()`         | `public async Task<decimal> GetTotalAsync()` |
| `Set conn = CreateObject(...)` | Constructor-injected `AppDbContext`       |
| `conn.Execute "UPDATE ..."`   | `await _context.SaveChangesAsync()`       |
| `rs.Fields("Name")`           | `entity.Name` (typed EF Core entity)      |
| `On Error Resume Next`        | `try/catch` with structured logging       |
| `MsgBox "Error"`              | `_logger.LogError(ex, "message")`         |
| `Err.Number <> 0`             | Typed exception handling                  |
| `WScript.Echo`                | Return typed result from method           |

## Classic ASP → Razor MVC Patterns

| Legacy (Classic ASP)                    | Modern (Razor MVC)                          |
|----------------------------------------|---------------------------------------------|
| `Request.Form("OrderId")`              | `[FromForm] OrderViewModel model`            |
| `Response.Write("<h1>" & name & "</h1>")` | `<h1>@Model.Name</h1>` in .cshtml         |
| `Session("UserId")`                    | `ISessionService.GetCurrentUserId()`         |
| `"SELECT * FROM Orders WHERE Id=" & id` | `_context.Orders.FindAsync(id)`             |
| `rs.Open sql, conn`                    | `await _context.Orders.ToListAsync()`        |
| `rs("Name")`                           | `order.Name` (typed EF Core entity)          |
| `<%  ... %>`  (code blocks)            | Controller Action method                     |
| `<% Response.Write(x) %>`             | `@Model.X` in Razor view                     |
| `rs.EOF`                               | `.FirstOrDefaultAsync()` returning null check|

## COM Object Registry

| COM Object                    | .NET Core Replacement                     |
|------------------------------|-------------------------------------------|
| `ADODB.Connection`           | `AppDbContext` (EF Core)                  |
| `ADODB.Recordset`            | `List<TEntity>` or `IQueryable<TEntity>` |
| `MSXML2.DOMDocument`         | `System.Xml.Linq.XDocument`              |
| `Scripting.FileSystemObject` | `System.IO.File` / `System.IO.Directory` |
| `CDO.Message` (email)        | `IEmailService` with MailKit             |
| `WScript.Shell`              | `System.Diagnostics.Process`             |
