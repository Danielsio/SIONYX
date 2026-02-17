# IMP-005: Design Pattern Improvements

## Changes Applied

### 1. Template Method Pattern — `BaseService.FetchJsonAsync()`
**Problem**: Every service repeated the same 3-line pattern:
```csharp
var result = await Firebase.DbGetAsync(path);
if (!result.Success) return Error(...);
if (result.Data is not JsonElement data || ...) return Error(...);
```

**Fix**: Added `FetchJsonAsync(path, errorContext)` to `BaseService` that returns
`(JsonElement Data, ServiceResult? Error)`. Services can now do:
```csharp
var (data, error) = await FetchJsonAsync("metadata", "fetch metadata");
if (error != null) return error;
```
Reduces boilerplate and ensures consistent error handling across all services.

### 2. Extract Method + Guard Clause — `AuthService.IsLoggedInOnAnotherComputer()`
**Problem**: Single-session enforcement logic was duplicated between `LoginAsync`
and `IsLoggedInAsync` — same 5 lines checking `isLoggedIn` + `currentComputerId`.

**Fix**: Extracted `IsLoggedInOnAnotherComputer(JsonElement userData)` as a Guard
Clause. Both login methods now call the same helper, eliminating duplication and
ensuring consistency.

### 3. Batch Operation Pattern — `ChatService.MarkAllMessagesAsReadAsync()`
**Problem**: Marked messages as read one-by-one, making 2N Firebase calls
(read + readAt for each message). For 10 unread messages = 20 HTTP requests.

**Fix**: Batches all updates into a single `DbUpdateAsync("", updates)` call
using Firebase's multi-path update. 10 messages = 1 HTTP request.

## Impact
- Cleaner, more maintainable service code
- Consistent error handling via Template Method
- Single-session check logic centralized (one place to update)
- Message read marking is ~20x faster for large unread counts

## Status: APPLIED
