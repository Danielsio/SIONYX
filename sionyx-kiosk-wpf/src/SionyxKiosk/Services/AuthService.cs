using System.Text.Json;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;

namespace SionyxKiosk.Services;

/// <summary>
/// Authentication service: login, register, logout, session recovery.
/// </summary>
public class AuthService : BaseService
{
    protected override string ServiceName => "AuthService";

    private readonly LocalDatabase _localDb;
    private readonly ComputerService _computerService;

    public UserData? CurrentUser { get; private set; }

    public AuthService(FirebaseClient firebase, LocalDatabase localDb) : base(firebase)
    {
        _localDb = localDb;
        _computerService = new ComputerService(firebase);
    }

    /// <summary>Check if user is already logged in via stored token.</summary>
    public async Task<bool> IsLoggedInAsync()
    {
        var storedRefreshToken = _localDb.Get("refresh_token");
        var storedUserId = _localDb.Get("user_id");
        if (string.IsNullOrEmpty(storedRefreshToken) || string.IsNullOrEmpty(storedUserId))
            return false;

        // Restore the saved refresh token into FirebaseClient so it can refresh
        Firebase.RestoreAuth("", storedRefreshToken, storedUserId);

        var refreshed = await Firebase.RefreshTokenAsync();
        if (!refreshed)
        {
            // Token expired or revoked — clear local storage
            _localDb.Delete("refresh_token");
            _localDb.Delete("user_id");
            _localDb.Delete("phone");
            Firebase.ClearAuth();
            return false;
        }

        // Fetch user data from Firebase
        var userResult = await Firebase.DbGetAsync($"users/{Firebase.UserId}");
        if (!userResult.Success || userResult.Data is not JsonElement data || data.ValueKind == JsonValueKind.Null)
            return false;

        CurrentUser = ParseUserData(data, Firebase.UserId!);

        // Update stored refresh token in case it was rotated during refresh
        if (!string.IsNullOrEmpty(Firebase.RefreshToken))
            _localDb.Set("refresh_token", Firebase.RefreshToken);

        Logger.Information("User auto-logged in: {UserId}", Firebase.UserId);

        await RecoverOrphanedSessionAsync(Firebase.UserId!, data);
        await HandleComputerRegistrationAsync(Firebase.UserId!);
        return true;
    }

    /// <summary>Login with phone and password.</summary>
    public async Task<ServiceResult> LoginAsync(string phone, string password)
    {
        Logger.Information("Login attempt for {Phone}", phone);
        var email = PhoneToEmail(phone);

        var result = await Firebase.SignInAsync(email, password);
        if (!result.Success)
            return Error(result.Error ?? "Login failed");

        var uid = Firebase.UserId!;
        var userResult = await Firebase.DbGetAsync($"users/{uid}");
        if (!userResult.Success || userResult.Data is not JsonElement userData || userData.ValueKind == JsonValueKind.Null)
            return Error(ErrorTranslations.Translate("user data not found"));

        // Single-session enforcement
        if (userData.TryGetProperty("isLoggedIn", out var loggedIn) && loggedIn.GetBoolean())
        {
            var currentComputerId = _computerService.GetComputerId();
            var loggedInComputer = SafeGet(userData, "currentComputerId");
            if (!string.IsNullOrEmpty(loggedInComputer) && loggedInComputer != currentComputerId)
                return Error("המשתמש כבר מחובר במחשב אחר. יש להתנתק שם קודם.");
        }

        CurrentUser = ParseUserData(userData, uid);
        await RecoverOrphanedSessionAsync(uid, userData);
        await HandleComputerRegistrationAsync(uid);

        // Store tokens locally — persist the REAL refresh token for auto-login
        _localDb.Set("refresh_token", Firebase.RefreshToken ?? "");
        _localDb.Set("user_id", uid);
        _localDb.Set("phone", phone);

        Logger.Information("Login successful for {Phone}", phone);
        return Success(CurrentUser);
    }

    /// <summary>Register a new user.</summary>
    public async Task<ServiceResult> RegisterAsync(string phone, string password, string firstName, string lastName, string email = "")
    {
        Logger.Information("Registration attempt for {Phone}", phone);

        if (password.Length < 6)
            return Error(ErrorTranslations.Translate("password must be at least 6 characters"));

        var firebaseEmail = PhoneToEmail(phone);
        var result = await Firebase.SignUpAsync(firebaseEmail, password);
        if (!result.Success)
            return Error(result.Error ?? "Registration failed");

        var uid = Firebase.UserId!;
        var now = DateTime.Now.ToString("o");

        var userDataObj = new
        {
            firstName,
            lastName,
            phoneNumber = phone,
            email = email ?? "",
            remainingTime = 0,
            printBalance = 0.0,
            isLoggedIn = false,
            isAdmin = false,
            createdAt = now,
            updatedAt = now,
        };

        var dbResult = await Firebase.DbSetAsync($"users/{uid}", userDataObj);
        if (!dbResult.Success)
            return Error("Failed to create user profile");

        CurrentUser = new UserData
        {
            Uid = uid,
            FirstName = firstName,
            LastName = lastName,
            PhoneNumber = phone,
            Email = email ?? "",
            CreatedAt = now,
            UpdatedAt = now,
        };

        _localDb.Set("refresh_token", Firebase.RefreshToken ?? "");
        _localDb.Set("user_id", uid);
        _localDb.Set("phone", phone);

        await HandleComputerRegistrationAsync(uid);

        Logger.Information("Registration successful for {Phone}", phone);
        return Success(CurrentUser);
    }

    /// <summary>Logout current user.</summary>
    public async Task LogoutAsync()
    {
        if (CurrentUser != null)
        {
            var userId = CurrentUser.Uid;
            var computerId = CurrentUser.CurrentComputerId;

            if (!string.IsNullOrEmpty(computerId))
                await _computerService.DisassociateUserFromComputerAsync(userId, computerId, isLogout: true);
            else
                await Firebase.DbUpdateAsync($"users/{userId}",
                    new { isLoggedIn = false, updatedAt = DateTime.Now.ToString("o") });

            Logger.Information("User logged out: {UserId}", userId);
        }

        Firebase.ClearAuth();
        _localDb.Delete("refresh_token");
        _localDb.Delete("user_id");
        _localDb.Delete("phone");
        CurrentUser = null;
    }

    /// <summary>Update current user's data in Firebase.</summary>
    public async Task<ServiceResult> UpdateUserDataAsync(Dictionary<string, object> updates)
    {
        if (CurrentUser == null) return Error("No user logged in");
        updates["updatedAt"] = DateTime.Now.ToString("o");
        var result = await Firebase.DbUpdateAsync($"users/{CurrentUser.Uid}", updates);
        return result.Success ? Success() : Error(result.Error ?? "Update failed");
    }

    // ==================== PRIVATE HELPERS ====================

    private async Task RecoverOrphanedSessionAsync(string userId, JsonElement userData)
    {
        try
        {
            if (!userData.TryGetProperty("isSessionActive", out var active) || !active.GetBoolean())
                return;

            var updatedAtStr = SafeGet(userData, "updatedAt");
            if (string.IsNullOrEmpty(updatedAtStr)) return;

            if (!DateTime.TryParse(updatedAtStr, out var lastUpdate)) return;

            var secondsSinceUpdate = (DateTime.Now - lastUpdate).TotalSeconds;
            if (secondsSinceUpdate <= 120) return; // Recent session, no cleanup

            Logger.Information("Orphaned session detected ({Seconds}s since last sync)", (int)secondsSinceUpdate);

            var computerId = SafeGet(userData, "currentComputerId");
            if (!string.IsNullOrEmpty(computerId))
                await _computerService.DisassociateUserFromComputerAsync(userId, computerId, isLogout: true);

            await Firebase.DbUpdateAsync($"users/{userId}", new Dictionary<string, object?>
            {
                ["isSessionActive"] = false,
                ["sessionStartTime"] = null,
                ["currentComputerId"] = null,
                ["updatedAt"] = DateTime.Now.ToString("o"),
            });

            Logger.Information("Orphaned session cleaned up (no time deducted)");
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Failed to recover orphaned session");
        }
    }

    private async Task HandleComputerRegistrationAsync(string userId)
    {
        try
        {
            var computerResult = await _computerService.RegisterComputerAsync();
            if (!computerResult.IsSuccess) return;

            // Extract computerId from the anonymous result
            var computerId = _computerService.GetComputerId();
            var assocResult = await _computerService.AssociateUserWithComputerAsync(userId, computerId, isLogin: true);

            if (assocResult.IsSuccess && CurrentUser != null)
                CurrentUser.CurrentComputerId = computerId;
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Computer registration failed");
        }
    }

    private static UserData ParseUserData(JsonElement data, string uid)
    {
        return new UserData
        {
            Uid = uid,
            FirstName = data.TryGetProperty("firstName", out var fn) ? fn.GetString() ?? "" : "",
            LastName = data.TryGetProperty("lastName", out var ln) ? ln.GetString() ?? "" : "",
            PhoneNumber = data.TryGetProperty("phoneNumber", out var pn) ? pn.GetString() ?? "" : "",
            Email = data.TryGetProperty("email", out var em) ? em.GetString() ?? "" : "",
            RemainingTime = data.TryGetProperty("remainingTime", out var rt) && rt.TryGetInt32(out var rtVal) ? rtVal : 0,
            PrintBalance = data.TryGetProperty("printBalance", out var pb) && pb.TryGetDouble(out var pbVal) ? pbVal : 0,
            IsLoggedIn = data.TryGetProperty("isLoggedIn", out var li) && li.GetBoolean(),
            IsAdmin = data.TryGetProperty("isAdmin", out var ia) && ia.GetBoolean(),
            IsSessionActive = data.TryGetProperty("isSessionActive", out var sa) && sa.GetBoolean(),
            SessionStartTime = data.TryGetProperty("sessionStartTime", out var st) ? st.GetString() : null,
            CurrentComputerId = data.TryGetProperty("currentComputerId", out var ci) ? ci.GetString() : null,
            TimeExpiresAt = data.TryGetProperty("timeExpiresAt", out var te) ? te.GetString() : null,
            CreatedAt = data.TryGetProperty("createdAt", out var ca) ? ca.GetString() ?? "" : "",
            UpdatedAt = data.TryGetProperty("updatedAt", out var ua) ? ua.GetString() ?? "" : "",
        };
    }

    private static string PhoneToEmail(string phone)
    {
        var clean = new string(phone.Where(char.IsDigit).ToArray());
        return $"{clean}@sionyx.app";
    }
}
