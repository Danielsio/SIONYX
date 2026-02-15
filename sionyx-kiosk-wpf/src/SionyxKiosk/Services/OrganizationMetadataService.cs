using System.Text;
using System.Text.Json;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Services;

/// <summary>
/// Organization metadata: Nedarim credentials, print pricing, operating hours, admin contact.
/// </summary>
public class OrganizationMetadataService : BaseService
{
    protected override string ServiceName => "OrganizationMetadataService";

    public OrganizationMetadataService(FirebaseClient firebase) : base(firebase) { }

    /// <summary>Decode base64-encoded JSON data.</summary>
    public static object? DecodeData(string encoded)
    {
        try
        {
            var bytes = Convert.FromBase64String(encoded);
            var json = Encoding.UTF8.GetString(bytes);
            return JsonSerializer.Deserialize<object>(json);
        }
        catch (Exception)
        {
            return null;
        }
    }

    public async Task<ServiceResult> GetOrganizationMetadataAsync(string orgId)
    {
        try
        {
            var result = await Firebase.DbGetAsync("metadata");
            if (!result.Success) return Error($"Failed to fetch metadata: {result.Error}");
            if (result.Data is not JsonElement data || data.ValueKind == JsonValueKind.Null)
                return Error("Organization metadata not found");

            var mosadId = DecodeData(SafeGet(data, "nedarim_mosad_id") ?? "");
            var apiValid = DecodeData(SafeGet(data, "nedarim_api_valid") ?? "");
            if (mosadId == null || apiValid == null)
                return Error("NEDARIM credentials not found in organization metadata");

            return Success(new
            {
                name = SafeGet(data, "name") ?? "",
                nedarim_mosad_id = mosadId,
                nedarim_api_valid = apiValid,
                created_at = SafeGet(data, "created_at") ?? "",
                status = SafeGet(data, "status") ?? "active",
            });
        }
        catch (Exception ex)
        {
            return Error(HandleFirebaseError(ex, "GetOrganizationMetadata"));
        }
    }

    public async Task<ServiceResult> GetPrintPricingAsync(string orgId)
    {
        try
        {
            var result = await Firebase.DbGetAsync($"organizations/{orgId}/metadata");
            if (!result.Success) return Error($"Failed to fetch metadata: {result.Error}");
            if (result.Data is not JsonElement data || data.ValueKind == JsonValueKind.Null)
                return Error("Organization metadata not found");

            return Success(new
            {
                blackAndWhitePrice = data.TryGetProperty("blackAndWhitePrice", out var bw) && bw.TryGetDouble(out var bwVal) ? bwVal : 1.0,
                colorPrice = data.TryGetProperty("colorPrice", out var c) && c.TryGetDouble(out var cVal) ? cVal : 3.0,
            });
        }
        catch (Exception ex)
        {
            return Error(HandleFirebaseError(ex, "GetPrintPricing"));
        }
    }

    public async Task<ServiceResult> SetPrintPricingAsync(string orgId, double blackWhitePrice, double colorPrice)
    {
        try
        {
            var result = await Firebase.DbUpdateAsync($"organizations/{orgId}/metadata",
                new { blackAndWhitePrice = blackWhitePrice, colorPrice });
            if (!result.Success) return Error($"Failed to update pricing: {result.Error}");

            Logger.Information("Print pricing updated for org {OrgId}: B&W={Bw} NIS, Color={Color} NIS",
                orgId, blackWhitePrice, colorPrice);
            return Success();
        }
        catch (Exception ex)
        {
            return Error(HandleFirebaseError(ex, "SetPrintPricing"));
        }
    }

    public async Task<ServiceResult> GetOperatingHoursAsync()
    {
        try
        {
            var result = await Firebase.DbGetAsync("metadata/settings/operatingHours");
            var defaults = new
            {
                enabled = false,
                startTime = "06:00",
                endTime = "00:00",
                gracePeriodMinutes = 5,
                graceBehavior = "graceful",
            };

            if (!result.Success || result.Data is not JsonElement data || data.ValueKind == JsonValueKind.Null)
                return Success(defaults);

            return Success(new
            {
                enabled = data.TryGetProperty("enabled", out var en) && en.GetBoolean(),
                startTime = SafeGet(data, "startTime") ?? "06:00",
                endTime = SafeGet(data, "endTime") ?? "00:00",
                gracePeriodMinutes = data.TryGetProperty("gracePeriodMinutes", out var gp) && gp.TryGetInt32(out var gpVal) ? gpVal : 5,
                graceBehavior = SafeGet(data, "graceBehavior") ?? "graceful",
            });
        }
        catch (Exception ex)
        {
            return Error(HandleFirebaseError(ex, "GetOperatingHours"));
        }
    }

    public async Task<ServiceResult> GetAdminContactAsync()
    {
        try
        {
            var result = await Firebase.DbGetAsync("metadata");
            if (!result.Success) return Error($"Failed to fetch metadata: {result.Error}");
            if (result.Data is not JsonElement data || data.ValueKind == JsonValueKind.Null)
                return Error("Organization metadata not found");

            var phone = SafeGet(data, "admin_phone") ?? "";
            var email = SafeGet(data, "admin_email") ?? "";
            if (string.IsNullOrEmpty(phone) && string.IsNullOrEmpty(email))
                return Error("Admin contact info not found");

            return Success(new { phone, email, orgName = SafeGet(data, "name") ?? "" });
        }
        catch (Exception ex)
        {
            return Error(HandleFirebaseError(ex, "GetAdminContact"));
        }
    }
}
