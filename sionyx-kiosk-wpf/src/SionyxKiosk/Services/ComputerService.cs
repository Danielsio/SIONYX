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

            var name = info["computerName"].ToString()!;
            if (!string.IsNullOrEmpty(computerName))
                name = computerName;
            else if (name == "Unknown-PC")
                name = $"PC-{computerId[..8].ToUpper()}";

            var now = DateTime.Now.ToString("o");
            var data = new Dictionary<string, object?>
            {
                ["computerName"] = name,
                ["currentUserId"] = null,
                ["isActive"] = false,
                ["lastSeen"] = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
                ["createdAt"] = now,
                ["updatedAt"] = now,
            };
            if (!string.IsNullOrEmpty(location))
                data["location"] = location;

            var result = await Firebase.DbUpdateAsync($"computers/{computerId}", data);
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
            var ts = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            var userUpdates = new Dictionary<string, object?> { ["currentComputerId"] = computerId, ["updatedAt"] = now };
            if (isLogin) userUpdates["isLoggedIn"] = true;

            var result = await Firebase.DbUpdateAsync($"users/{userId}", userUpdates);
            if (result.Success)
            {
                await Firebase.DbUpdateAsync($"computers/{computerId}",
                    new Dictionary<string, object>
                    {
                        ["currentUserId"] = userId,
                        ["isActive"] = true,
                        ["lastSeen"] = ts,
                        ["lastUserLogin"] = now,
                        ["updatedAt"] = now,
                    });
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
            var ts = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            var userUpdates = new Dictionary<string, object?> { ["currentComputerId"] = (object?)null, ["updatedAt"] = now };
            if (isLogout) userUpdates["isLoggedIn"] = false;

            await Firebase.DbUpdateAsync($"users/{userId}", userUpdates);
            await Firebase.DbUpdateAsync($"computers/{computerId}",
                new Dictionary<string, object?>
                {
                    ["currentUserId"] = null,
                    ["isActive"] = false,
                    ["lastSeen"] = ts,
                    ["updatedAt"] = now,
                });

            return Success();
        }
        catch (Exception ex)
        {
            return Error(HandleFirebaseError(ex, "DisassociateUser"));
        }
    }
}
