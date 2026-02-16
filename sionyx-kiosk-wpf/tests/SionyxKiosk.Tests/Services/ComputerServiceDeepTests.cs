using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for ComputerService covering registration and association paths.
/// </summary>
public class ComputerServiceDeepTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ComputerService _service;

    public ComputerServiceDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new ComputerService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public void GetComputerId_ShouldReturnNonEmptyString()
    {
        var id = _service.GetComputerId();
        id.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetComputerId_ShouldBeConsistent()
    {
        var id1 = _service.GetComputerId();
        var id2 = _service.GetComputerId();
        id1.Should().Be(id2);
    }

    [Fact]
    public async Task RegisterComputerAsync_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        var result = await _service.RegisterComputerAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task RegisterComputerAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("computers");
        var result = await _service.RegisterComputerAsync();
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task AssociateUserWithComputerAsync_ForLogin_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        var computerId = _service.GetComputerId();
        var result = await _service.AssociateUserWithComputerAsync("user-1", computerId, isLogin: true);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task AssociateUserWithComputerAsync_ForSession_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        var computerId = _service.GetComputerId();
        var result = await _service.AssociateUserWithComputerAsync("user-1", computerId, isLogin: false);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task DisassociateUserFromComputerAsync_ForLogout_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        var computerId = _service.GetComputerId();
        var result = await _service.DisassociateUserFromComputerAsync("user-1", computerId, isLogout: true);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task DisassociateUserFromComputerAsync_ForSessionEnd_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        var computerId = _service.GetComputerId();
        var result = await _service.DisassociateUserFromComputerAsync("user-1", computerId, isLogout: false);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task DisassociateUserFromComputerAsync_WhenFirebaseFails_ShouldStillReturnSuccess()
    {
        // DisassociateUserFromComputerAsync doesn't check DbUpdate result - always returns Success
        _handler.WhenError("test-db.firebaseio.com");
        var computerId = _service.GetComputerId();
        var result = await _service.DisassociateUserFromComputerAsync("user-1", computerId, isLogout: true);
        result.IsSuccess.Should().BeTrue(); // By design: fire-and-forget updates
    }

    [Fact]
    public async Task AssociateUserWithComputerAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("test-db.firebaseio.com");
        var computerId = _service.GetComputerId();
        var result = await _service.AssociateUserWithComputerAsync("user-1", computerId, isLogin: true);
        result.IsSuccess.Should().BeFalse();
    }
}
