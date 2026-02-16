using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class SessionServiceTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly SessionService _service;

    public SessionServiceTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.SetDefaultSuccess();
        _service = new SessionService(_firebase, "user-123", "test-org");
    }

    public void Dispose()
    {
        _service.Dispose();
        _firebase.Dispose();
    }

    // ==================== INITIAL STATE ====================

    [Fact]
    public void InitialState_ShouldBeInactive()
    {
        _service.IsActive.Should().BeFalse();
        _service.RemainingTime.Should().Be(0);
        _service.TimeUsed.Should().Be(0);
        _service.SessionId.Should().BeNull();
        _service.StartTime.Should().BeNull();
        _service.IsOnline.Should().BeTrue();
    }

    [Fact]
    public void OperatingHours_ShouldNotBeNull()
    {
        _service.OperatingHours.Should().NotBeNull();
    }

    // ==================== START SESSION ====================

    [Fact]
    public async Task StartSessionAsync_WhenAlreadyActive_ShouldFail()
    {
        // Mock time expiration check
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");

        await _service.StartSessionAsync(3600);

        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("already active");
    }

    [Fact]
    public async Task StartSessionAsync_WithZeroTime_ShouldFail()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 0}");

        var result = await _service.StartSessionAsync(0);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task StartSessionAsync_WithValidTime_ShouldSucceed()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");

        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeTrue();
        _service.IsActive.Should().BeTrue();
        _service.RemainingTime.Should().Be(3600);
        _service.SessionId.Should().NotBeNullOrEmpty();
        _service.StartTime.Should().NotBeNull();
    }

    [Fact]
    public async Task StartSessionAsync_ShouldFireSessionStartedEvent()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        var fired = false;
        _service.SessionStarted += () => fired = true;

        await _service.StartSessionAsync(3600);
        fired.Should().BeTrue();
    }

    [Fact]
    public async Task StartSessionAsync_WithExpiredTime_ShouldFail()
    {
        // Mock user with expired time
        var expiredDate = DateTime.Now.AddDays(-1).ToString("o");
        _handler.When("users/user-123.json", new
        {
            remainingTime = 3600,
            timeExpiresAt = expiredDate,
        });

        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== END SESSION ====================

    [Fact]
    public async Task EndSessionAsync_WhenNotActive_ShouldFail()
    {
        var result = await _service.EndSessionAsync();
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task EndSessionAsync_WhenActive_ShouldSucceed()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        var result = await _service.EndSessionAsync("user");
        result.IsSuccess.Should().BeTrue();
        _service.IsActive.Should().BeFalse();
    }

    [Fact]
    public async Task EndSessionAsync_ShouldFireSessionEndedEvent()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        string? endReason = null;
        _service.SessionEnded += reason => endReason = reason;

        await _service.EndSessionAsync("user");
        endReason.Should().Be("user");
    }

    [Fact]
    public async Task EndSessionAsync_WithExpiredReason_ShouldPass()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        var result = await _service.EndSessionAsync("expired");
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== EVENTS ====================

    [Fact]
    public void Events_ShouldBeSubscribable()
    {
        _service.SessionStarted += () => { };
        _service.TimeUpdated += (_) => { };
        _service.SessionEnded += (_) => { };
        _service.Warning5Min += () => { };
        _service.Warning1Min += () => { };
        _service.SyncFailed += (_) => { };
        _service.SyncRestored += () => { };
        _service.OperatingHoursWarning += (_) => { };
        _service.OperatingHoursEnded += (_) => { };
    }

    // ==================== DISPOSE ====================

    [Fact]
    public void Dispose_ShouldNotThrow()
    {
        var act = () => _service.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public async Task Dispose_AfterActiveSession_ShouldNotThrow()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        var act = () => _service.Dispose();
        act.Should().NotThrow();
    }
}
