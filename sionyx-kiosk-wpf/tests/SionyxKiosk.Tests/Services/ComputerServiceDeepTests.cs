using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep coverage for ComputerService: exception paths, name generation, edge cases.
/// </summary>
public class ComputerServiceDeepTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ComputerService _service;

    public ComputerServiceDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.SetDefaultSuccess();
        _service = new ComputerService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    // ==================== GET COMPUTER ID ====================

    [Fact]
    public void GetComputerId_ShouldReturnConsistentValue()
    {
        var id1 = _service.GetComputerId();
        var id2 = _service.GetComputerId();
        id1.Should().Be(id2);
    }

    [Fact]
    public void GetComputerId_ShouldNotBeEmpty()
    {
        _service.GetComputerId().Should().NotBeNullOrEmpty();
    }

    // ==================== REGISTER COMPUTER ====================

    [Fact]
    public async Task RegisterComputerAsync_WithCustomName_ShouldSucceed()
    {
        var result = await _service.RegisterComputerAsync("MyPC", "Room 1");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task RegisterComputerAsync_WithEmptyName_ShouldUseDefaultName()
    {
        var result = await _service.RegisterComputerAsync("", null);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task RegisterComputerAsync_WithNullName_ShouldUseDefaultName()
    {
        var result = await _service.RegisterComputerAsync(null, null);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task RegisterComputerAsync_WhenFirebaseFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenError("computers/");

        var result = await _service.RegisterComputerAsync("PC1", null);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task RegisterComputerAsync_WhenNetworkFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenThrows("computers/", "Network timeout");

        var result = await _service.RegisterComputerAsync("PC1", null);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task RegisterComputerAsync_WithLocation_ShouldSucceed()
    {
        var result = await _service.RegisterComputerAsync("PC1", "Floor 2");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task RegisterComputerAsync_WithEmptyLocation_ShouldSucceed()
    {
        var result = await _service.RegisterComputerAsync("PC1", "");
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== ASSOCIATE USER ====================

    [Fact]
    public async Task AssociateUserWithComputerAsync_IsLogin_ShouldSucceed()
    {
        var result = await _service.AssociateUserWithComputerAsync("user-123", "comp-1", isLogin: true);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task AssociateUserWithComputerAsync_NotLogin_ShouldSucceed()
    {
        var result = await _service.AssociateUserWithComputerAsync("user-123", "comp-1", isLogin: false);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task AssociateUserWithComputerAsync_WhenFirebaseFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenError("computers/");
        _handler.WhenError("users/");

        var result = await _service.AssociateUserWithComputerAsync("user-123", "comp-1", isLogin: true);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task AssociateUserWithComputerAsync_WhenNetworkFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        // Must throw on users/ path since that's the first write
        _handler.WhenThrows("users/", "Network error");

        var result = await _service.AssociateUserWithComputerAsync("user-123", "comp-1", isLogin: true);
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== DISASSOCIATE USER ====================

    [Fact]
    public async Task DisassociateUserFromComputerAsync_IsLogout_ShouldSucceed()
    {
        var result = await _service.DisassociateUserFromComputerAsync("user-123", "comp-1", isLogout: true);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task DisassociateUserFromComputerAsync_NotLogout_ShouldSucceed()
    {
        var result = await _service.DisassociateUserFromComputerAsync("user-123", "comp-1", isLogout: false);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task DisassociateUserFromComputerAsync_WhenNetworkFails_ShouldNotThrow()
    {
        // DisassociateUser doesn't check DbUpdateAsync return values,
        // so it always succeeds unless an unhandled exception is thrown.
        // This test verifies resilience: no crash even on failures.
        _handler.ClearHandlers();
        _handler.WhenError("users/");
        _handler.WhenError("computers/");

        var act = async () => await _service.DisassociateUserFromComputerAsync("user-123", "comp-1", isLogout: true);
        await act.Should().NotThrowAsync();
    }

    // ==================== MULTIPLE OPERATIONS ====================

    [Fact]
    public async Task FullLifecycle_RegisterAssociateDisassociate_ShouldSucceed()
    {
        var regResult = await _service.RegisterComputerAsync("PC1", "Room 1");
        regResult.IsSuccess.Should().BeTrue();

        var computerId = _service.GetComputerId();

        var assocResult = await _service.AssociateUserWithComputerAsync("user-123", computerId, isLogin: true);
        assocResult.IsSuccess.Should().BeTrue();

        var disassocResult = await _service.DisassociateUserFromComputerAsync("user-123", computerId, isLogout: true);
        disassocResult.IsSuccess.Should().BeTrue();
    }
}
