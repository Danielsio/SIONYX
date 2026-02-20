using System.IO;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class AuthServiceTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly LocalDatabase _localDb;
    private readonly AuthService _service;
    private readonly string _dbPath;

    public AuthServiceTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _dbPath = Path.Combine(Path.GetTempPath(), $"auth_test_{Guid.NewGuid():N}.db");
        _localDb = new LocalDatabase(_dbPath);
        _service = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
    }

    public void Dispose()
    {
        _firebase.Dispose();
        _localDb.Dispose();
        try { File.Delete(_dbPath); } catch { }
    }

    // ==================== LOGIN ====================

    [Fact]
    public async Task LoginAsync_WithValidCredentials_ShouldSucceed()
    {
        // Mock sign-in response
        _handler.When("signInWithPassword", new
        {
            idToken = "login-token",
            refreshToken = "login-refresh",
            localId = "user-123",
            expiresIn = "3600"
        });

        // Mock user data fetch
        _handler.When("users/user-123.json", new
        {
            firstName = "David",
            lastName = "Cohen",
            phoneNumber = "0501234567",
            email = "",
            remainingTime = 3600,
            printBalance = 10.0,
            isLoggedIn = false,
            isAdmin = false,
        });

        // Mock computer registration
        _handler.SetDefaultSuccess();

        var result = await _service.LoginAsync("0501234567", "password123");
        result.IsSuccess.Should().BeTrue();
        _service.CurrentUser.Should().NotBeNull();
        _service.CurrentUser!.FirstName.Should().Be("David");
    }

    [Fact]
    public async Task LoginAsync_WithAlreadyLoggedInOnAnotherPC_ShouldFail()
    {
        _handler.When("signInWithPassword", new
        {
            idToken = "login-token",
            refreshToken = "login-refresh",
            localId = "user-123",
            expiresIn = "3600"
        });

        _handler.When("users/user-123.json", new
        {
            firstName = "David",
            lastName = "Cohen",
            isLoggedIn = true,
            currentComputerId = "OTHER-COMPUTER-ID",
        });

        var result = await _service.LoginAsync("0501234567", "password123");
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("מחובר במחשב אחר");
    }

    [Fact]
    public async Task LoginAsync_WhenSignInFails_ShouldFail()
    {
        _handler.WhenError("signInWithPassword", System.Net.HttpStatusCode.BadRequest);

        var result = await _service.LoginAsync("0501234567", "wrong_password");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task LoginAsync_WhenUserDataNotFound_ShouldFail()
    {
        _handler.When("signInWithPassword", new
        {
            idToken = "token",
            refreshToken = "refresh",
            localId = "user-123",
            expiresIn = "3600"
        });

        _handler.WhenRaw("users/user-123.json", "null");

        var result = await _service.LoginAsync("0501234567", "password123");
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== REGISTER ====================

    [Fact]
    public async Task RegisterAsync_WithShortPassword_ShouldFail()
    {
        var result = await _service.RegisterAsync("0501234567", "12345", "David", "Cohen");
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("6");
    }

    [Fact]
    public async Task RegisterAsync_WithValidData_ShouldSucceed()
    {
        _handler.When("signUp", new
        {
            idToken = "reg-token",
            refreshToken = "reg-refresh",
            localId = "new-user-456",
            expiresIn = "3600"
        });

        _handler.SetDefaultSuccess();

        var result = await _service.RegisterAsync("0501234567", "password123", "David", "Cohen", "david@test.com");
        result.IsSuccess.Should().BeTrue();
        _service.CurrentUser.Should().NotBeNull();
        _service.CurrentUser!.FirstName.Should().Be("David");
        _service.CurrentUser!.LastName.Should().Be("Cohen");
    }

    [Fact]
    public async Task RegisterAsync_WhenSignUpFails_ShouldFail()
    {
        _handler.WhenError("signUp", System.Net.HttpStatusCode.BadRequest);

        var result = await _service.RegisterAsync("0501234567", "password123", "David", "Cohen");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task RegisterAsync_WhenDbSetFails_ShouldFail()
    {
        _handler.When("signUp", new
        {
            idToken = "reg-token",
            refreshToken = "reg-refresh",
            localId = "new-user-456",
            expiresIn = "3600"
        });

        _handler.WhenError("users/new-user-456.json");

        var result = await _service.RegisterAsync("0501234567", "password123", "David", "Cohen");
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== LOGOUT ====================

    [Fact]
    public async Task LogoutAsync_WithNoUser_ShouldNotThrow()
    {
        await _service.LogoutAsync();
        _service.CurrentUser.Should().BeNull();
    }

    [Fact]
    public async Task LogoutAsync_WithUser_ShouldClearState()
    {
        // First login
        _handler.When("signInWithPassword", new
        {
            idToken = "token",
            refreshToken = "refresh",
            localId = "user-123",
            expiresIn = "3600"
        });
        _handler.When("users/user-123.json", new
        {
            firstName = "David",
            lastName = "Cohen",
            isLoggedIn = false,
        });
        _handler.SetDefaultSuccess();

        await _service.LoginAsync("0501234567", "password123");

        // Then logout
        await _service.LogoutAsync();
        _service.CurrentUser.Should().BeNull();
        _localDb.Get("refresh_token").Should().BeNull();
        _localDb.Get("user_id").Should().BeNull();
    }

    // ==================== UPDATE USER DATA ====================

    [Fact]
    public async Task UpdateUserDataAsync_WhenNoUser_ShouldFail()
    {
        var result = await _service.UpdateUserDataAsync(new Dictionary<string, object> { ["name"] = "Test" });
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("No user");
    }

    // ==================== IS LOGGED IN ====================

    [Fact]
    public async Task IsLoggedInAsync_WithNoStoredTokens_ShouldReturnFalse()
    {
        var result = await _service.IsLoggedInAsync();
        result.Should().BeFalse();
    }

    [Fact]
    public async Task IsLoggedInAsync_WithStoredTokens_AndRefreshFails_ShouldReturnFalse()
    {
        _localDb.Set("refresh_token", "old-token");
        _localDb.Set("user_id", "user-123");

        // Mock refresh token failure
        _handler.WhenError("securetoken.googleapis.com");

        var result = await _service.IsLoggedInAsync();
        result.Should().BeFalse();
    }
}
