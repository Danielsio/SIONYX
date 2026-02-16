using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class ComputerServiceTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ComputerService _service;

    public ComputerServiceTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new ComputerService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public void GetComputerId_ShouldReturnNonEmpty()
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

        var result = await _service.RegisterComputerAsync("Test PC", "Room 1");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task RegisterComputerAsync_WithoutName_ShouldAutoGenerate()
    {
        _handler.SetDefaultSuccess();

        var result = await _service.RegisterComputerAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task RegisterComputerAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("computers/");

        var result = await _service.RegisterComputerAsync();
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task AssociateUserWithComputerAsync_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();

        var result = await _service.AssociateUserWithComputerAsync("user-123", "computer-456", isLogin: true);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task AssociateUserWithComputerAsync_WithoutLogin_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();

        var result = await _service.AssociateUserWithComputerAsync("user-123", "computer-456");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task DisassociateUserFromComputerAsync_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();

        var result = await _service.DisassociateUserFromComputerAsync("user-123", "computer-456", isLogout: true);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task DisassociateUserFromComputerAsync_WithoutLogout_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();

        var result = await _service.DisassociateUserFromComputerAsync("user-123", "computer-456");
        result.IsSuccess.Should().BeTrue();
    }
}
