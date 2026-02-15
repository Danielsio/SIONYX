using System.Text.Json;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;

namespace SionyxKiosk.Services;

/// <summary>
/// Handle package purchases with pending state and history.
/// </summary>
public class PurchaseService : BaseService
{
    protected override string ServiceName => "PurchaseService";

    public PurchaseService(FirebaseClient firebase) : base(firebase) { }

    /// <summary>Create a pending purchase record before payment.</summary>
    public async Task<ServiceResult> CreatePendingPurchaseAsync(string userId, Package package)
    {
        Logger.Information("Creating pending purchase for user {UserId}", userId);
        try
        {
            var now = DateTime.Now.ToString("o");
            var purchaseData = new
            {
                userId,
                packageId = package.Id,
                packageName = package.Name,
                minutes = package.Minutes,
                prints = package.Prints,
                printBudget = package.Prints,
                validityDays = package.ValidityDays,
                amount = package.Price,
                status = "pending",
                createdAt = now,
                updatedAt = now,
            };

            // Use DbSetAsync with an auto-generated key path
            var purchaseId = Guid.NewGuid().ToString("N")[..20];
            var result = await Firebase.DbSetAsync($"purchases/{purchaseId}", purchaseData);
            if (!result.Success)
                return Error("Failed to create purchase record");

            Logger.Information("Pending purchase created: {PurchaseId}", purchaseId);
            return Success(new { purchaseId });
        }
        catch (Exception ex)
        {
            return Error(HandleFirebaseError(ex, "CreatePendingPurchase"));
        }
    }

    /// <summary>Get current purchase status.</summary>
    public async Task<ServiceResult> GetPurchaseStatusAsync(string purchaseId)
    {
        var result = await Firebase.DbGetAsync($"purchases/{purchaseId}");
        if (!result.Success) return Error("Purchase not found");
        return Success(result.Data);
    }

    /// <summary>Get all purchases for a specific user, sorted newest first.</summary>
    public async Task<ServiceResult> GetUserPurchaseHistoryAsync(string userId)
    {
        LogOperation("GetUserPurchaseHistory", userId);

        var result = await Firebase.DbGetAsync("purchases");
        if (!result.Success) return Error(result.Error ?? "Failed to fetch purchases");
        if (result.Data is not JsonElement data || data.ValueKind != JsonValueKind.Object)
            return Success(Array.Empty<Purchase>());

        var purchases = new List<Purchase>();
        foreach (var prop in data.EnumerateObject())
        {
            var el = prop.Value;
            if (el.ValueKind != JsonValueKind.Object) continue;

            var uid = el.TryGetProperty("userId", out var u) ? u.GetString() : null;
            if (uid != userId) continue;

            purchases.Add(ParsePurchase(el, prop.Name));
        }

        purchases.Sort((a, b) => string.Compare(b.CreatedAt, a.CreatedAt, StringComparison.Ordinal));
        return Success(purchases);
    }

    /// <summary>Calculate purchase statistics for a user.</summary>
    public async Task<ServiceResult> GetPurchaseStatisticsAsync(string userId)
    {
        var historyResult = await GetUserPurchaseHistoryAsync(userId);
        if (!historyResult.IsSuccess) return historyResult;

        var purchases = (List<Purchase>)historyResult.Data!;
        var completed = purchases.Count(p => p.Status == "completed");
        var totalSpent = purchases.Where(p => p.Status == "completed").Sum(p => p.Amount);

        return Success(new
        {
            totalSpent,
            completedPurchases = completed,
            pendingPurchases = purchases.Count(p => p.Status == "pending"),
            failedPurchases = purchases.Count(p => p.Status == "failed"),
            totalPurchases = purchases.Count,
        });
    }

    private static Purchase ParsePurchase(JsonElement el, string id) => new()
    {
        Id = id,
        UserId = el.TryGetProperty("userId", out var u) ? u.GetString() ?? "" : "",
        PackageId = el.TryGetProperty("packageId", out var pi) ? pi.GetString() ?? "" : "",
        PackageName = el.TryGetProperty("packageName", out var pn) ? pn.GetString() ?? "" : "",
        Minutes = el.TryGetProperty("minutes", out var m) && m.TryGetInt32(out var mv) ? mv : 0,
        Prints = el.TryGetProperty("prints", out var pr) && pr.TryGetInt32(out var prv) ? prv : 0,
        PrintBudget = el.TryGetProperty("printBudget", out var pb) && pb.TryGetDouble(out var pbv) ? pbv : 0,
        ValidityDays = el.TryGetProperty("validityDays", out var vd) && vd.TryGetInt32(out var vdv) ? vdv : 0,
        Amount = el.TryGetProperty("amount", out var a) && a.TryGetDouble(out var av) ? av : 0,
        Status = el.TryGetProperty("status", out var s) ? s.GetString() ?? "pending" : "pending",
        CreatedAt = el.TryGetProperty("createdAt", out var ca) ? ca.GetString() ?? "" : "",
        UpdatedAt = el.TryGetProperty("updatedAt", out var ua) ? ua.GetString() ?? "" : "",
    };
}
