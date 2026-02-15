using System.Text.Json;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;

namespace SionyxKiosk.Services;

/// <summary>
/// Fetch and manage packages from Firebase.
/// </summary>
public class PackageService : BaseService
{
    protected override string ServiceName => "PackageService";

    public PackageService(FirebaseClient firebase) : base(firebase) { }

    /// <summary>Fetch all packages from Firebase.</summary>
    public async Task<ServiceResult> GetAllPackagesAsync()
    {
        LogOperation("GetAllPackages");

        var result = await Firebase.DbGetAsync("packages");
        if (!result.Success) return Error(result.Error ?? "Failed to fetch packages");
        if (result.Data is not JsonElement data || data.ValueKind == JsonValueKind.Null)
            return Success(Array.Empty<Package>());

        var packages = new List<Package>();
        if (data.ValueKind == JsonValueKind.Object)
        {
            foreach (var prop in data.EnumerateObject())
            {
                var pkg = ParsePackage(prop.Value, prop.Name);
                if (pkg != null) packages.Add(pkg);
            }
        }

        Logger.Information("Packages loaded: {Count} total", packages.Count);
        return Success(packages);
    }

    /// <summary>Get a single package by ID.</summary>
    public async Task<ServiceResult> GetPackageByIdAsync(string packageId)
    {
        LogOperation("GetPackageById", packageId);

        var result = await Firebase.DbGetAsync($"packages/{packageId}");
        if (!result.Success) return Error(result.Error ?? "Package not found");
        if (result.Data is not JsonElement data || data.ValueKind == JsonValueKind.Null)
            return Error("Package not found");

        var pkg = ParsePackage(data, packageId);
        return pkg != null ? Success(pkg) : Error("Failed to parse package");
    }

    private static Package? ParsePackage(JsonElement el, string id)
    {
        if (el.ValueKind != JsonValueKind.Object) return null;
        return new Package
        {
            Id = id,
            Name = el.TryGetProperty("name", out var n) ? n.GetString() ?? "" : "",
            Price = el.TryGetProperty("price", out var p) && p.TryGetDouble(out var pv) ? pv : 0,
            Minutes = el.TryGetProperty("minutes", out var m) && m.TryGetInt32(out var mv) ? mv : 0,
            Prints = el.TryGetProperty("prints", out var pr) && pr.TryGetInt32(out var prv) ? prv : 0,
            DiscountPercent = el.TryGetProperty("discountPercent", out var d) && d.TryGetDouble(out var dv) ? dv : 0,
            ValidityDays = el.TryGetProperty("validityDays", out var vd) && vd.TryGetInt32(out var vdv) ? vdv : 0,
            IsFeatured = el.TryGetProperty("isFeatured", out var f) && f.GetBoolean(),
        };
    }
}
