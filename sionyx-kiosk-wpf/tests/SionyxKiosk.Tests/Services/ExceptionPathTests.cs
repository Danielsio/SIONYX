using System.IO;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Tests that trigger exception catch blocks in async service methods.
/// These paths are only hit when the HttpClient throws (network failure),
/// not when Firebase returns an error HTTP response.
/// </summary>
public class OrgMetadataExceptionPathTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly OrganizationMetadataService _service;

    public OrgMetadataExceptionPathTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new OrganizationMetadataService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public async Task GetOrganizationMetadataAsync_WhenNetworkFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenThrows("metadata", "Connection refused");

        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetPrintPricingAsync_WhenNetworkFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenThrows("metadata", "Connection refused");

        var result = await _service.GetPrintPricingAsync("test-org");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task SetPrintPricingAsync_WhenNetworkFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenThrows("metadata", "Connection refused");

        var result = await _service.SetPrintPricingAsync("test-org", 1.0, 3.0);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetOperatingHoursAsync_WhenNetworkFails_ShouldReturnDefaults()
    {
        // GetOperatingHoursAsync returns defaults even on failure
        _handler.ClearHandlers();
        _handler.WhenThrows("operatingHours", "Connection refused");

        var result = await _service.GetOperatingHoursAsync();
        result.IsSuccess.Should().BeTrue(); // Returns defaults, not error
    }

    [Fact]
    public async Task GetAdminContactAsync_WhenNetworkFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenThrows("metadata", "Connection refused");

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeFalse();
    }
}

public class ComputerServiceExceptionPathTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ComputerService _service;

    public ComputerServiceExceptionPathTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new ComputerService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public async Task RegisterComputerAsync_WhenNetworkFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenThrows("computers/", "Network unreachable");

        var result = await _service.RegisterComputerAsync();
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task AssociateUser_WhenNetworkFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenThrows("users/", "Network unreachable");

        var result = await _service.AssociateUserWithComputerAsync("u1", "c1", isLogin: true);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task DisassociateUser_WhenNetworkFails_ShouldStillReturnSuccess()
    {
        // DisassociateUser does fire-and-forget updates; FirebaseClient catches the exception
        // internally, so the service method returns Success() regardless.
        _handler.ClearHandlers();
        _handler.WhenThrows("users/", "Network unreachable");

        var result = await _service.DisassociateUserFromComputerAsync("u1", "c1", isLogout: true);
        result.IsSuccess.Should().BeTrue();
    }
}

public class PurchaseServiceExceptionPathTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly PurchaseService _service;

    public PurchaseServiceExceptionPathTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new PurchaseService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public async Task CreatePendingPurchaseAsync_WhenNetworkFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenThrows("purchases/", "Connection timeout");

        var package = new SionyxKiosk.Models.Package
        {
            Id = "pkg-1", Name = "Basic", Minutes = 60, Prints = 10, Price = 29.99, ValidityDays = 30,
        };

        var result = await _service.CreatePendingPurchaseAsync("user-1", package);
        result.IsSuccess.Should().BeFalse();
    }
}

public class AuthServiceExceptionPathTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly LocalDatabase _localDb;
    private readonly AuthService _service;
    private readonly string _dbPath;

    public AuthServiceExceptionPathTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _dbPath = Path.Combine(Path.GetTempPath(), $"auth_exc_test_{Guid.NewGuid():N}.db");
        _localDb = new LocalDatabase(_dbPath);
        _service = new AuthService(_firebase, _localDb);
    }

    public void Dispose()
    {
        _firebase.Dispose();
        _localDb.Dispose();
        try { File.Delete(_dbPath); } catch { }
    }

    [Fact]
    public async Task HandleComputerRegistration_WhenNetworkFails_ShouldNotThrow()
    {
        // Login with network failure on computers path
        _handler.When("signInWithPassword", new
        {
            idToken = "tok", refreshToken = "rtok", localId = "uid-net-fail", expiresIn = "3600",
        });
        _handler.When("users/uid-net-fail.json", new
        {
            firstName = "Test", lastName = "User", isLoggedIn = false,
        });
        // Computer registration throws network error
        _handler.WhenThrows("computers/", "Network unreachable");

        var result = await _service.LoginAsync("0501234567", "password123");
        // Login should still succeed - HandleComputerRegistration catches exceptions
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task RecoverOrphanedSession_WhenCleanupNetworkFails_ShouldNotThrow()
    {
        _localDb.Set("refresh_token", "stored-refresh");
        _localDb.Set("user_id", "stored-uid-exc");

        _handler.When("securetoken.googleapis.com", new
        {
            id_token = "tok", refresh_token = "rtok", user_id = "stored-uid-exc", expires_in = "3600",
        });

        // Orphaned session (old)
        var oldTime = DateTime.Now.AddMinutes(-10).ToString("o");
        _handler.When("users/stored-uid-exc.json", new
        {
            firstName = "Jane", lastName = "Smith", isSessionActive = true,
            updatedAt = oldTime, currentComputerId = "old-comp", isLoggedIn = false,
        });

        // Network failure during cleanup - the recover method catches this
        _handler.WhenThrows("users/stored-uid-exc.json?auth=", "Network failure");
        // But we need some calls to succeed...
        _handler.SetDefaultSuccess();

        var result = await _service.IsLoggedInAsync();
        result.Should().BeTrue();
    }
}
