using System.IO;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Targeted tests for AuthService.HandleComputerRegistrationAsync resilient flow.
/// </summary>
public class AuthServiceComputerRegistrationTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly LocalDatabase _localDb;
    private readonly AuthService _service;
    private readonly string _dbPath;

    public AuthServiceComputerRegistrationTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _dbPath = Path.Combine(Path.GetTempPath(), $"auth_comp_test_{Guid.NewGuid():N}.db");
        _localDb = new LocalDatabase(_dbPath);
        _service = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
    }

    public void Dispose()
    {
        _firebase.Dispose();
        _localDb.Dispose();
        try { File.Delete(_dbPath); } catch { }
    }

    private void SetupLoginMocks()
    {
        _handler.When("signInWithPassword", new
        {
            idToken = "login-token",
            refreshToken = "login-refresh",
            localId = "user-123",
            expiresIn = "3600",
        });

        _handler.When("users/user-123.json", new
        {
            firstName = "David",
            lastName = "Cohen",
            phoneNumber = "0501234567",
            email = "",
            remainingTime = 3600,
            printBalance = 15.50,
            isLoggedIn = false,
            isAdmin = false,
        });

        _handler.SetDefaultSuccess();
    }

    [Fact]
    public async Task Login_WhenComputerRegistrationSucceeds_ShouldSetComputerId()
    {
        SetupLoginMocks();

        var result = await _service.LoginAsync("0501234567", "password123");
        result.IsSuccess.Should().BeTrue();
        _service.CurrentUser.Should().NotBeNull();
        _service.CurrentUser!.CurrentComputerId.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public async Task Login_WhenDefaultSuccess_ShouldPopulateUser()
    {
        SetupLoginMocks();

        var result = await _service.LoginAsync("0501234567", "password123");
        result.IsSuccess.Should().BeTrue();
        _service.CurrentUser!.FirstName.Should().Be("David");
        _service.CurrentUser!.LastName.Should().Be("Cohen");
        _service.CurrentUser!.PhoneNumber.Should().Be("0501234567");
        _service.CurrentUser!.RemainingTime.Should().Be(3600);
        _service.CurrentUser!.PrintBalance.Should().Be(15.50);
    }

    [Fact]
    public async Task Login_ShouldStoreTokensLocally()
    {
        SetupLoginMocks();

        await _service.LoginAsync("0501234567", "password123");

        _localDb.Get("refresh_token").Should().NotBeNullOrEmpty();
        _localDb.Get("user_id").Should().Be("user-123");
        _localDb.Get("phone").Should().Be("0501234567");
    }

    [Fact]
    public async Task Logout_ShouldClearCurrentUser()
    {
        SetupLoginMocks();
        await _service.LoginAsync("0501234567", "password123");
        _service.CurrentUser.Should().NotBeNull();

        await _service.LogoutAsync();
        _service.CurrentUser.Should().BeNull();
    }

    [Fact]
    public async Task Logout_WhenNotLoggedIn_ShouldNotThrow()
    {
        _handler.SetDefaultSuccess();
        _service.CurrentUser.Should().BeNull();
        await _service.LogoutAsync();
    }

    [Fact]
    public async Task Login_WhenAlreadyLoggedInSameComputer_ShouldSucceed()
    {
        _handler.When("signInWithPassword", new
        {
            idToken = "login-token",
            refreshToken = "login-refresh",
            localId = "user-123",
            expiresIn = "3600",
        });

        _handler.When("users/user-123.json", new
        {
            firstName = "David",
            lastName = "Cohen",
            phoneNumber = "0501234567",
            email = "",
            remainingTime = 3600,
            printBalance = 15.50,
            isLoggedIn = true,
            isAdmin = false,
            currentComputerId = DeviceInfo.GetDeviceId(),
        });

        _handler.SetDefaultSuccess();

        var result = await _service.LoginAsync("0501234567", "password123");
        result.IsSuccess.Should().BeTrue();
    }
}
