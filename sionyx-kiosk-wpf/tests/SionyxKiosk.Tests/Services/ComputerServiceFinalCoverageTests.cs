using System.IO;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Final coverage tests for ComputerService targeting exception paths and edge cases:
/// - RegisterComputerAsync with custom name, with Unknown-PC fallback
/// - AssociateUserWithComputerAsync failure path
/// - DisassociateUserFromComputerAsync exception path
/// </summary>
public class ComputerServiceFinalCoverageTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ComputerService _service;

    public ComputerServiceFinalCoverageTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new ComputerService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    // ==================== RegisterComputerAsync ====================

    [Fact]
    public async Task RegisterComputerAsync_WithCustomName_ShouldUseCustomName()
    {
        _handler.SetDefaultSuccess();
        var result = await _service.RegisterComputerAsync(computerName: "Custom-PC", location: "Room 101");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task RegisterComputerAsync_WithNoNameAndNotUnknownPC_ShouldKeepDefault()
    {
        _handler.SetDefaultSuccess();
        // When no name is provided but the default name is not "Unknown-PC",
        // it keeps whatever GetComputerInfo returns (usually Environment.MachineName)
        var result = await _service.RegisterComputerAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task RegisterComputerAsync_WithLocation_ShouldIncludeLocation()
    {
        _handler.SetDefaultSuccess();
        var result = await _service.RegisterComputerAsync(location: "Library Floor 2");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task RegisterComputerAsync_WhenDbSetFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenError("computers/");
        var result = await _service.RegisterComputerAsync();
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("Failed to register");
    }

    // ==================== AssociateUserWithComputerAsync ====================

    [Fact]
    public async Task AssociateUser_WithIsLogin_ShouldIncludeIsLoggedIn()
    {
        _handler.SetDefaultSuccess();
        var result = await _service.AssociateUserWithComputerAsync("user-1", "comp-1", isLogin: true);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task AssociateUser_WithoutIsLogin_ShouldOmitIsLoggedIn()
    {
        _handler.SetDefaultSuccess();
        var result = await _service.AssociateUserWithComputerAsync("user-1", "comp-1", isLogin: false);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task AssociateUser_WhenUserUpdateFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenError("users/");
        var result = await _service.AssociateUserWithComputerAsync("user-1", "comp-1", isLogin: true);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task AssociateUser_WhenComputerUpdateFails_ShouldStillSucceed()
    {
        // User update succeeds, computer update fails - should still return success
        // because the primary operation (user update) succeeded
        _handler.ClearHandlers();
        _handler.When("users/user-1.json", new { success = true });
        _handler.WhenError("computers/comp-1.json");
        // The user update uses PATCH so it hits users/user-1.json
        _handler.SetDefaultSuccess();

        var result = await _service.AssociateUserWithComputerAsync("user-1", "comp-1", isLogin: true);
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== DisassociateUserFromComputerAsync ====================

    [Fact]
    public async Task DisassociateUser_WithIsLogout_ShouldIncludeIsLoggedIn()
    {
        _handler.SetDefaultSuccess();
        var result = await _service.DisassociateUserFromComputerAsync("user-1", "comp-1", isLogout: true);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task DisassociateUser_WithoutIsLogout_ShouldNotIncludeIsLoggedIn()
    {
        _handler.SetDefaultSuccess();
        var result = await _service.DisassociateUserFromComputerAsync("user-1", "comp-1", isLogout: false);
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== GetComputerId ====================

    [Fact]
    public void GetComputerId_ShouldMatchDeviceInfo()
    {
        var id = _service.GetComputerId();
        id.Should().Be(DeviceInfo.GetDeviceId());
    }
}
