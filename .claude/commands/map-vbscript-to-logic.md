# /map-vbscript-to-logic
# Slash command template for migrating VBScript Sub/Function units to C# Service class

## Command
`/map-vbscript-to-logic`

## Purpose
Converts an isolated VBScript Sub or Function unit into a method inside a sealed C# Service class.
One slash command invocation = one method produced.

## Input (from context package)
- The isolated VBScript unit (from Stage 1 Extractor)
- CLAUDE.md rulebook
- migration-patterns.md dictionary  
- Live EF Core schema (from MCP server)

## Output Rules (ALL must be satisfied)
1. Wrap output in a `public sealed class {Name}Service`
2. One `public async Task` method per VBScript Sub
3. One `public async Task<T>` method per VBScript Function (infer return type)
4. Replace ALL COM object usage with constructor-injected dependencies
5. Replace ALL SQL string execution with EF Core typed queries
6. Wrap ALL operations in try/catch with `_logger.LogError` + re-throw
7. Add XML doc comment referencing original VBScript Sub name
8. Constructor: inject `AppDbContext _context` and `ILogger<T> _logger` minimum

## Forbidden in Output
- `dynamic`, `object` for typed data
- Bare catch blocks
- SQL string concatenation  
- Non-async methods touching the database
- Hardcoded connection strings

## Output File
`output/Services/{Name}Service.cs`
