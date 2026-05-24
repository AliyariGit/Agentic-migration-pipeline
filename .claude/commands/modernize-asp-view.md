# /modernize-asp-view
# Slash command template for migrating Classic ASP UI layer to Razor MVC

## Command
`/modernize-asp-view`

## Purpose
Converts a Classic ASP UI/Response layer unit into THREE separate output files.
This is the defining pattern of ASP migration: one file in → three files out.

## Input (from context package)
- The isolated ASP UI layer unit (from Stage 1 Extractor)
- CLAUDE.md rulebook
- Request.Form → ViewModel property map
- EF Core entity schema (from MCP server)

## Output — THREE files required (all must be produced)

### File 1: Controller Action
`output/Controllers/{Name}Controller.cs`
- `public sealed class {Name}Controller : Controller`
- One `async Task<IActionResult>` per page/action
- GET action loads ViewModel from Service layer
- POST action accepts `[FromForm] {Name}ViewModel model`
- `[ValidateAntiForgeryToken]` on all POST actions
- No business logic in controller — delegate to Service

### File 2: Strongly-Typed ViewModel
`output/ViewModels/{Name}ViewModel.cs`
- `public sealed class {Name}ViewModel`  
- One property per `Request.Form("x")` field
- One property per `rs.Fields("x")` column accessed
- Use exact C# types (int, string, decimal, DateTime)
- No `object`, no `dynamic`

### File 3: Razor View
`output/Views/{Name}/Index.cshtml`
- `@model {Name}ViewModel` at top
- Replace every `Response.Write(x)` with `@Model.X`
- Replace every `<% = variable %>` with `@Model.Variable`
- `@Html.AntiForgeryToken()` in all forms
- `asp-for` tag helpers on form inputs

## Forbidden in Output
- `Response.Write(...)` in any file
- `Session["key"]` direct access → use `ISessionService`
- Business logic in .cshtml views
- Synchronous database calls
- SQL string concatenation
