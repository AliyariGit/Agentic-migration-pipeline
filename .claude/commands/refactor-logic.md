# /refactor-logic
# Slash command template for recovery — triggered after validation gate failure

## Command
`/refactor-logic`

## Purpose
Applies a targeted, surgical fix to a specific validation failure.
NEVER regenerates the entire file — only addresses flagged patterns.

## Input
- The generated C# file that failed validation
- The structured JSON validation report (machine-readable)
- CLAUDE.md rulebook

## Recovery Rules
1. Read the `issues` array from the validation report
2. Fix ONLY the patterns listed — do not touch passing code
3. For each `pattern_id`, apply the corresponding fix:

| pattern_id              | Fix Action                                          |
|------------------------|-----------------------------------------------------|
| `bare_catch_block`     | Add `_logger.LogError(ex, ...)` + `throw;`          |
| `dynamic_keyword`      | Replace with explicit type or `object` + TODO       |
| `session_direct_access`| Replace with `_sessionService.Get("key")`           |
| `synchronous_db_call`  | Add `Async` suffix + `await`                        |
| `non_sealed_service`   | Add `sealed` keyword to class declaration           |
| `sql_string_concat`    | Replace with EF Core typed query                    |
| `response_write`       | Comment out + add TODO for Razor view migration     |

## Output
- The same file, with targeted fixes applied
- A recovery log entry added as a comment block at top of file
- No new files created
- No functional logic changed — only the flagged pattern corrected

## After Recovery
The validator will re-run automatically on the fixed file.
If it still fails, escalate to engineer review — do not loop more than 2 times.
