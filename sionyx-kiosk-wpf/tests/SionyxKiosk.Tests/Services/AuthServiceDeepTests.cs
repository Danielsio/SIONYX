using System.IO;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for AuthService covering IsLoggedInAsync, RecoverOrphanedSession,
/// HandleComputerRegistration, and edge cases.
/// </summary>
public class AuthServiceDeepTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly LocalDatabase _localDb;
    private readonly AuthService _service;
    private readonly string _dbPath;

    public AuthServiceDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _dbPath = Path.Combine(Path.GetTempPath(), $"auth_deep_test_{Guid.NewGuid():N}.db");
        _localDb = new LocalDatabase(_dbPath);
        _service = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
    }

    public void Dispose()
    {
        _firebase.Dispose();
        _localDb.Dispose();
        try { File.Delete(_dbPath); } catch { }
    }

    // ==================== IsLoggedInAsync ====================

    [Fact]
    public async Task IsLoggedInAsync_WithNoStoredTokens_ShouldReturnFalse()
    {
        var result = await _service.IsLoggedInAsync();
        result.Should().BeFalse();
    }

    [Fact]
    public async Task IsLoggedInAsync_WithStoredTokens_AndRefreshSuccess_ShouldReturnTrue()
    {
        _localDb.Set("refresh_token", "stored-refresh-token");
        _localDb.Set("user_id", "stored-uid");

        // Mock token refresh
        _handler.When("securetoken.googleapis.com", new
        {
            id_token = "new-id-token",
            refresh_token = "new-refresh-token",
            user_id = "stored-uid",
            expires_in = "3600",
        });

        // Mock user data fetch
        _handler.When("users/stored-uid.json", new
        {
            firstName = "John",
            lastName = "Doe",
            phoneNumber = "0501234567",
            remainingTime = 3600,
            isLoggedIn = false,
        });

        // Mock computer registration and association
        _handler.SetDefaultSuccess();

        var result = await _service.IsLoggedInAsync();
        result.Should().BeTrue();
        _service.CurrentUser.Should().NotBeNull();
        _service.CurrentUser!.FirstName.Should().Be("John");
    }

    [Fact]
    public async Task IsLoggedInAsync_WithStoredTokens_AndRefreshFails_ShouldReturnFalse()
    {
        _localDb.Set("refresh_token", "expired-token");
        _localDb.Set("user_id", "stored-uid");

        // Mock token refresh failure
        _handler.WhenError("securetoken.googleapis.com");

        var result = await _service.IsLoggedInAsync();
        result.Should().BeFalse();

        // Should clear stored tokens
        _localDb.Get("refresh_token").Should().BeNull();
        _localDb.Get("user_id").Should().BeNull();
    }

    [Fact]
    public async Task IsLoggedInAsync_WithStoredTokens_ButNoUserData_ShouldReturnFalse()
    {
        _localDb.Set("refresh_token", "stored-refresh");
        _localDb.Set("user_id", "stored-uid");

        _handler.When("securetoken.googleapis.com", new
        {
            id_token = "new-token",
            refresh_token = "new-refresh",
            user_id = "stored-uid",
            expires_in = "3600",
        });

        // Return null user data
        _handler.WhenRaw("users/stored-uid.json", "null");

        var result = await _service.IsLoggedInAsync();
        result.Should().BeFalse();
    }

    [Fact]
    public async Task IsLoggedInAsync_WithOrphanedSession_ShouldRecover()
    {
        _localDb.Set("refresh_token", "stored-refresh");
        _localDb.Set("user_id", "stored-uid");

        _handler.When("securetoken.googleapis.com", new
        {
            id_token = "tok",
            refresh_token = "rtok",
            user_id = "stored-uid",
            expires_in = "3600",
        });

        // User data with orphaned session (old updatedAt)
        var oldTime = DateTime.Now.AddMinutes(-10).ToString("o");
        _handler.When("users/stored-uid.json", new
        {
            firstName = "Jane",
            lastName = "Smith",
            isSessionActive = true,
            updatedAt = oldTime,
            currentComputerId = "old-computer",
            isLoggedIn = false,
        });

        _handler.SetDefaultSuccess();

        var result = await _service.IsLoggedInAsync();
        result.Should().BeTrue();
    }

    // ==================== LoginAsync ====================

    [Fact]
    public async Task LoginAsync_WithSingleSessionConflict_ShouldReturnError()
    {
        _handler.When("signInWithPassword", new
        {
            idToken = "tok",
            refreshToken = "rtok",
            localId = "uid-1",
            expiresIn = "3600",
        });

        // User logged in on another computer
        _handler.When("users/uid-1.json", new
        {
            firstName = "Test",
            lastName = "User",
            isLoggedIn = true,
            currentComputerId = "other-computer-id-different",
        });

        var result = await _service.LoginAsync("0501234567", "password123");
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("מחובר"); // Hebrew for "connected"
    }

    [Fact]
    public async Task LoginAsync_WithSignInFailure_ShouldReturnError()
    {
        _handler.WhenError("signInWithPassword", System.Net.HttpStatusCode.Unauthorized);

        var result = await _service.LoginAsync("0501234567", "password123");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task LoginAsync_WithUserDataFetchFailure_ShouldReturnError()
    {
        _handler.When("signInWithPassword", new
        {
            idToken = "tok",
            refreshToken = "rtok",
            localId = "uid-1",
            expiresIn = "3600",
        });
        _handler.WhenRaw("users/uid-1.json", "null");

        var result = await _service.LoginAsync("0501234567", "password123");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task LoginAsync_Success_ShouldStoreTokensLocally()
    {
        _handler.When("signInWithPassword", new
        {
            idToken = "tok",
            refreshToken = "rtok",
            localId = "uid-1",
            expiresIn = "3600",
        });
        _handler.When("users/uid-1.json", new
        {
            firstName = "Test",
            lastName = "User",
            isLoggedIn = false,
        });
        _handler.SetDefaultSuccess();

        var result = await _service.LoginAsync("0501234567", "password123");
        result.IsSuccess.Should().BeTrue();

        _localDb.Get("user_id").Should().Be("uid-1");
        _localDb.Get("phone").Should().Be("0501234567");
    }

    // ==================== RegisterAsync ====================

    [Fact]
    public async Task RegisterAsync_WithShortPassword_ShouldReturnError()
    {
        var result = await _service.RegisterAsync("0501234567", "123", "John", "Doe");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task RegisterAsync_WhenSignUpFails_ShouldReturnError()
    {
        _handler.WhenError("signUp", System.Net.HttpStatusCode.BadRequest);

        var result = await _service.RegisterAsync("0501234567", "password123", "John", "Doe");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task RegisterAsync_WhenDbSetFails_ShouldReturnError()
    {
        _handler.When("signUp", new
        {
            idToken = "tok",
            refreshToken = "rtok",
            localId = "uid-1",
            expiresIn = "3600",
        });

        // Make the DB set for user profile fail
        _handler.WhenError("test-db.firebaseio.com");

        var result = await _service.RegisterAsync("0501234567", "password123", "John", "Doe");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task RegisterAsync_Success_ShouldSetCurrentUser()
    {
        _handler.When("signUp", new
        {
            idToken = "tok",
            refreshToken = "rtok",
            localId = "uid-1",
            expiresIn = "3600",
        });
        _handler.SetDefaultSuccess();

        var result = await _service.RegisterAsync("0501234567", "password123", "John", "Doe", "john@test.com");
        result.IsSuccess.Should().BeTrue();
        _service.CurrentUser.Should().NotBeNull();
        _service.CurrentUser!.FirstName.Should().Be("John");
        _service.CurrentUser.Email.Should().Be("john@test.com");
    }

    // ==================== LogoutAsync ====================

    [Fact]
    public async Task LogoutAsync_WithNoUser_ShouldClearAuthAndLocalDb()
    {
        _localDb.Set("refresh_token", "old");
        _localDb.Set("user_id", "old");
        _localDb.Set("phone", "old");

        await _service.LogoutAsync();

        _localDb.Get("refresh_token").Should().BeNull();
        _localDb.Get("user_id").Should().BeNull();
        _localDb.Get("phone").Should().BeNull();
        _firebase.IsAuthenticated.Should().BeFalse();
    }

    [Fact]
    public async Task LogoutAsync_WithUser_ShouldDisassociateComputer()
    {
        // First login
        _handler.When("signInWithPassword", new
        {
            idToken = "tok",
            refreshToken = "rtok",
            localId = "uid-1",
            expiresIn = "3600",
        });
        _handler.When("users/uid-1.json", new
        {
            firstName = "Test",
            lastName = "User",
            isLoggedIn = false,
        });
        _handler.SetDefaultSuccess();
        await _service.LoginAsync("0501234567", "password123");

        // Now logout
        await _service.LogoutAsync();

        _service.CurrentUser.Should().BeNull();
        _firebase.IsAuthenticated.Should().BeFalse();
    }

    // ==================== UpdateUserDataAsync ====================

    [Fact]
    public async Task UpdateUserDataAsync_WithNoUser_ShouldReturnError()
    {
        var result = await _service.UpdateUserDataAsync(new Dictionary<string, object> { ["name"] = "Test" });
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task UpdateUserDataAsync_WithUser_ShouldSucceed()
    {
        // Login first
        _handler.When("signInWithPassword", new
        {
            idToken = "tok",
            refreshToken = "rtok",
            localId = "uid-1",
            expiresIn = "3600",
        });
        _handler.When("users/uid-1.json", new
        {
            firstName = "Test",
            lastName = "User",
            isLoggedIn = false,
        });
        _handler.SetDefaultSuccess();
        await _service.LoginAsync("0501234567", "password123");

        var result = await _service.UpdateUserDataAsync(new Dictionary<string, object> { ["firstName"] = "Updated" });
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task UpdateUserDataAsync_WhenFirebaseFails_ShouldReturnError()
    {
        // Login first
        _handler.When("signInWithPassword", new
        {
            idToken = "tok",
            refreshToken = "rtok",
            localId = "uid-1",
            expiresIn = "3600",
        });
        _handler.When("users/uid-1.json", new
        {
            firstName = "Test",
            lastName = "User",
            isLoggedIn = false,
        });
        _handler.SetDefaultSuccess();
        await _service.LoginAsync("0501234567", "password123");

        // Clear all handlers, then add error handler
        _handler.ClearHandlers();
        _handler.WhenError("test-db.firebaseio.com");

        var result = await _service.UpdateUserDataAsync(new Dictionary<string, object> { ["firstName"] = "X" });
        result.IsSuccess.Should().BeFalse();
    }
}
