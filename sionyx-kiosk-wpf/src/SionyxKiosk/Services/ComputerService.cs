using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Services;

/// <summary>
/// Manages computer/PC registration and tracking in Firebase.
/// </summary>
public class ComputerService : BaseService
{
    protected override string ServiceName => "ComputerService";

    public ComputerService(FirebaseClient firebase) : base(firebase) { }

    public string GetComputerId() => DeviceInfo.GetDeviceId();

    public async Task<ServiceResult> RegisterComputerAsync(string? computerName = null, string? location = null)
    {
        try
        {
            LogOperation("RegisterComputer");
            var info = DeviceInfo.GetComputerInfo();
            var computerId = info["deviceId"].ToString()!;

            if (!string.IsNullOrEmpty(computerName))
                info["computerName"] = computerName;
            else if (info["computerName"].ToString() == "Unknown-PC")
                info["computerName"] = $"PC-{computerId[..8].ToUpper()}";

            if (!string.IsNullOrEmpty(location))
                info["location"] = location;

            var now = DateTime.Now.ToString("o");
            info["currentUserId"] = null!;
            info["createdAt"] = now;
            info["updatedAt"] = now;

            var result = await Firebase.DbSetAsync($"computers/{computerId}", info);
            if (!result.Success)
                return Error("Failed to register computer");

            Logger.Information("Computer registered: {Id}", computerId);
            return Success(new { computerId, computerName = info["computerName"].ToString() });
        }
        catch (Exception ex)
        {
            return Error(HandleFirebaseError(ex, "RegisterComputer"));
        }
    }

    public async Task<ServiceResult> AssociateUserWithComputerAsync(string userId, string computerId, bool isLogin = false)
    {
        try
        {
            var now = DateTime.Now.ToString("o");
            var userUpdates = new Dictionary<string, object?> { ["currentComputerId"] = computerId, ["updatedAt"] = now };
            if (isLogin) userUpdates["isLoggedIn"] = true;

            var result = await Firebase.DbUpdateAsync($"users/{userId}", userUpdates);
            if (result.Success)
            {
                await Firebase.DbUpdateAsync($"computers/{computerId}",
                    new { currentUserId = userId, updatedAt = now });
            }
            return result.Success ? Success() : Error(result.Error ?? "Failed");
        }
        catch (Exception ex)
        {
            return Error(HandleFirebaseError(ex, "AssociateUser"));
        }
    }

    public async Task<ServiceResult> DisassociateUserFromComputerAsync(string userId, string computerId, bool isLogout = false)
    {
        try
        {
            var now = DateTime.Now.ToString("o");
            var userUpdates = new Dictionary<string, object?> { ["currentComputerId"] = (object?)null, ["updatedAt"] = now };
            if (isLogout) userUpdates["isLoggedIn"] = false;

            await Firebase.DbUpdateAsync($"users/{userId}", userUpdates);
            await Firebase.DbUpdateAsync($"computers/{computerId}",
                new Dictionary<string, object?> { ["currentUserId"] = null, ["updatedAt"] = now });

            return Success();
        }
        catch (Exception ex)
        {
            return Error(HandleFirebaseError(ex, "DisassociateUser"));
        }
    }
}
