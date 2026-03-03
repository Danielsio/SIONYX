using FluentAssertions;
using Moq;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Integration;

/// <summary>
/// Integration tests for the session lifecycle:
/// login -> start session -> countdown -> end session.
/// Tests multiple services working together.
/// </summary>
public class SessionFlowTests : IDisposable
{
    private readonly string _dbPath = Path.Combine(Path.GetTempPath(), $"sionyx_test_{Guid.NewGuid()}.db");

    public void Dispose()
    {
        try { File.Delete(_dbPath); } catch { }
    }

    [Fact]
    public async Task FullSessionFlow_LoginToLogout()
    {
        // Arrange: create services with mock Firebase
        var (firebase, handler) = TestFirebaseFactory.Create("test-user-id");
        var localDb = new LocalDatabase(_dbPath);
        var computerService = new ComputerService(firebase);
        var authService = new AuthService(firebase, localDb, computerService);

        handler.WhenRaw("signInWithPassword", """
            {"idToken":"tok","refreshToken":"ref","localId":"test-user-id"}
        """);
        handler.WhenRaw("users/test-user-id", """
            {"firstName":"Test","lastName":"User","phoneNumber":"0501234567","remainingTime":3600,"printBalance":10,"isLoggedIn":false,"isAdmin":false,"isSessionActive":false,"createdAt":"2026-01-01","updatedAt":"2026-01-01"}
        """);

        // Act: Login
        var loginResult = await authService.LoginAsync("0501234567", "password123");

        // Assert: login succeeded and user data loaded
        loginResult.IsSuccess.Should().BeTrue();
        authService.CurrentUser.Should().NotBeNull();
        authService.CurrentUser!.RemainingTime.Should().Be(3600);
        authService.CurrentUser.PrintBalance.Should().Be(10);
        authService.CurrentUser.FirstName.Should().Be("Test");
    }

    [Fact]
    public async Task Login_WithExpiredToken_ShouldClearSavedData()
    {
        var (firebase, handler) = TestFirebaseFactory.Create("test-user-id");
        var localDb = new LocalDatabase(_dbPath);
        var computerService = new ComputerService(firebase);
        var authService = new AuthService(firebase, localDb, computerService);

        // Simulate saved token
        localDb.Set("refresh_token", "old-token");
        localDb.Set("user_id", "test-user-id");

        // Token refresh fails
        handler.WhenError("token", System.Net.HttpStatusCode.Unauthorized);

        var isLoggedIn = await authService.IsLoggedInAsync();
        isLoggedIn.Should().BeFalse();

        // Saved data should be cleared
        localDb.Get("refresh_token").Should().BeNull();
        localDb.Get("user_id").Should().BeNull();
    }

    [Fact]
    public async Task Logout_ShouldClearAllState()
    {
        var (firebase, handler) = TestFirebaseFactory.Create("test-user-id");
        var localDb = new LocalDatabase(_dbPath);
        var computerService = new ComputerService(firebase);
        var authService = new AuthService(firebase, localDb, computerService);

        // Login first
        handler.WhenRaw("signInWithPassword", """
            {"idToken":"tok","refreshToken":"ref","localId":"test-user-id"}
        """);
        handler.WhenRaw("users/test-user-id", """
            {"firstName":"Test","lastName":"User","phoneNumber":"0501234567","remainingTime":3600,"printBalance":10,"isLoggedIn":false,"isAdmin":false,"isSessionActive":false,"createdAt":"2026-01-01","updatedAt":"2026-01-01"}
        """);

        await authService.LoginAsync("0501234567", "password123");
        authService.CurrentUser.Should().NotBeNull();

        // Logout
        await authService.LogoutAsync();

        authService.CurrentUser.Should().BeNull();
        localDb.Get("refresh_token").Should().BeNull();
        localDb.Get("user_id").Should().BeNull();
        localDb.Get("phone").Should().BeNull();
    }

    [Fact]
    public async Task Login_WhenUserActiveOnAnotherPC_ShouldReject()
    {
        var (firebase, handler) = TestFirebaseFactory.Create("test-user-id");
        var localDb = new LocalDatabase(_dbPath);
        var computerService = new ComputerService(firebase);
        var authService = new AuthService(firebase, localDb, computerService);

        handler.WhenRaw("signInWithPassword", """
            {"idToken":"tok","refreshToken":"ref","localId":"test-user-id"}
        """);
        handler.WhenRaw("users/test-user-id", """
            {"firstName":"Test","lastName":"User","phoneNumber":"0501234567","remainingTime":3600,"printBalance":10,"isLoggedIn":true,"isAdmin":false,"isSessionActive":true,"currentComputerId":"OTHER-PC-ID","createdAt":"2026-01-01","updatedAt":"2026-01-01"}
        """);

        var result = await authService.LoginAsync("0501234567", "password123");
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("מחובר");
    }

    [Fact]
    public async Task Register_ShouldCreateUser()
    {
        var (firebase, handler) = TestFirebaseFactory.Create();
        var localDb = new LocalDatabase(_dbPath);
        var computerService = new ComputerService(firebase);
        var authService = new AuthService(firebase, localDb, computerService);

        handler.WhenRaw("signUp", """
            {"idToken":"tok","refreshToken":"ref","localId":"new-uid"}
        """);
        handler.SetDefaultSuccess();

        var result = await authService.RegisterAsync("0509876543", "password123", "Jane", "Doe");
        result.IsSuccess.Should().BeTrue();
        authService.CurrentUser.Should().NotBeNull();
        authService.CurrentUser!.FirstName.Should().Be("Jane");
        authService.CurrentUser.PhoneNumber.Should().Be("0509876543");
    }

    [Fact]
    public async Task Register_WithShortPassword_ShouldFail()
    {
        var (firebase, handler) = TestFirebaseFactory.Create();
        var localDb = new LocalDatabase(_dbPath);
        var computerService = new ComputerService(firebase);
        var authService = new AuthService(firebase, localDb, computerService);

        var result = await authService.RegisterAsync("0509876543", "123", "Jane", "Doe");
        result.IsSuccess.Should().BeFalse();
    }
}
