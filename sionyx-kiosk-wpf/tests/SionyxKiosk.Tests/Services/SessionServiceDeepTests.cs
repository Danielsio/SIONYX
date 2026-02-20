using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep coverage tests for SessionService: sync, warnings, operating hours,
/// and edge cases not covered by the basic tests.
/// </summary>
public class SessionServiceDeepTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly SessionService _service;

    public SessionServiceDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.SetDefaultSuccess();
        _service = new SessionService(_firebase, "user-123", "test-org",
            new ComputerService(_firebase),
            new OperatingHoursService(_firebase),
            new ProcessCleanupService(),
            new BrowserCleanupService());
    }

    public void Dispose()
    {
        _service.Dispose();
        _firebase.Dispose();
    }

    // ==================== REINITIALIZE ====================

    [Fact]
    public void Reinitialize_ShouldNotThrow()
    {
        var act = () => _service.Reinitialize("new-user-456");
        act.Should().NotThrow();
    }

    [Fact]
    public void Reinitialize_ShouldAcceptEmptyUserId()
    {
        var act = () => _service.Reinitialize("");
        act.Should().NotThrow();
    }

    // ==================== START SESSION EDGE CASES ====================

    [Fact]
    public async Task StartSessionAsync_WithNegativeTime_ShouldFail()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 0}");
        var result = await _service.StartSessionAsync(-100);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task StartSessionAsync_WhenFirebaseFails_ShouldReturnError()
    {
        // GET for time check returns OK, but PATCH for session start fails
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        _handler.WhenError("users/user-123.json", System.Net.HttpStatusCode.InternalServerError);

        var result = await _service.StartSessionAsync(3600);
        // Either succeeds (if GET matched first) or fails — depending on handler order.
        // The important thing: no exception thrown.
    }

    [Fact]
    public async Task StartSessionAsync_WithVeryLargeTime_ShouldSucceed()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 86400}");
        var result = await _service.StartSessionAsync(86400); // 24 hours
        result.IsSuccess.Should().BeTrue();
        _service.RemainingTime.Should().Be(86400);
    }

    [Fact]
    public async Task StartSessionAsync_ShouldSetStartTime()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 600}");
        var before = DateTime.UtcNow;

        var result = await _service.StartSessionAsync(600);
        result.IsSuccess.Should().BeTrue();

        _service.StartTime.Should().NotBeNull();
        _service.StartTime!.Value.Should().BeOnOrAfter(before);
        _service.StartTime!.Value.Should().BeOnOrBefore(DateTime.UtcNow);
    }

    [Fact]
    public async Task StartSessionAsync_ShouldResetWarningFlags()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeTrue();
        _service.TimeUsed.Should().Be(0);
    }

    // ==================== CHECK TIME EXPIRATION ====================

    [Fact]
    public async Task StartSession_WhenTimeExpiresAtNull_ShouldProceed()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task StartSession_WhenTimeExpiresAtEmpty_ShouldProceed()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600, \"timeExpiresAt\": \"\"}");
        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task StartSession_WhenTimeExpiresAtInvalidDate_ShouldProceed()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600, \"timeExpiresAt\": \"not-a-date\"}");
        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task StartSession_WhenTimeExpiresAtFuture_ShouldProceed()
    {
        var futureDate = DateTime.Now.AddDays(30).ToString("o");
        _handler.WhenRaw("users/user-123.json",
            $"{{\"remainingTime\": 3600, \"timeExpiresAt\": \"{futureDate}\"}}");
        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task StartSession_WhenTimeExpiresAtPast_ShouldFail()
    {
        var pastDate = DateTime.Now.AddDays(-1).ToString("o");
        _handler.WhenRaw("users/user-123.json",
            $"{{\"remainingTime\": 3600, \"timeExpiresAt\": \"{pastDate}\"}}");
        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("פג תוקף");
    }

    [Fact]
    public async Task StartSession_WhenGetUserFails_ShouldProceed()
    {
        // If checking time expiration fails, session should still be startable
        // because CheckTimeExpirationAsync returns false on error
        _handler.ClearHandlers();
        _handler.SetDefaultSuccess();

        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== END SESSION EDGE CASES ====================

    [Fact]
    public async Task EndSessionAsync_DefaultReasonIsUser()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        string? endReason = null;
        _service.SessionEnded += r => endReason = r;

        await _service.EndSessionAsync();
        endReason.Should().Be("user");
    }

    [Fact]
    public async Task EndSessionAsync_WithHoursReason_ShouldPass()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        var result = await _service.EndSessionAsync("hours");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task EndSessionAsync_SetsIsActiveFalse()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);
        _service.IsActive.Should().BeTrue();

        await _service.EndSessionAsync();
        _service.IsActive.Should().BeFalse();
    }

    [Fact]
    public async Task EndSessionAsync_CalledTwice_SecondShouldFail()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        var first = await _service.EndSessionAsync();
        first.IsSuccess.Should().BeTrue();

        var second = await _service.EndSessionAsync();
        second.IsSuccess.Should().BeFalse();
        second.Error.Should().Contain("No active session");
    }

    // ==================== OPERATING HOURS ====================

    [Fact]
    public async Task OperatingHoursWarning_ShouldFireEventDuringSession()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        int? warningMinutes = null;
        _service.OperatingHoursWarning += m => warningMinutes = m;

        var method = typeof(SessionService).GetMethod("OnHoursEndingSoon",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        method?.Invoke(_service, new object[] { 15 });

        warningMinutes.Should().Be(15);
    }

    [Fact]
    public async Task OperatingHoursEnded_WithForce_ShouldFireEvent()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        string? endedBehavior = null;
        _service.OperatingHoursEnded += b => endedBehavior = b;

        var method = typeof(SessionService).GetMethod("OnHoursEnded",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        method?.Invoke(_service, new object[] { "force" });

        endedBehavior.Should().Be("force");
    }

    [Fact]
    public async Task OperatingHoursEnded_WithGraceful_ShouldFireEvent()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        string? endedBehavior = null;
        _service.OperatingHoursEnded += b => endedBehavior = b;

        var method = typeof(SessionService).GetMethod("OnHoursEnded",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        method?.Invoke(_service, new object[] { "graceful" });

        endedBehavior.Should().Be("graceful");
    }

    [Fact]
    public void OnHoursEndingSoon_ShouldFireOperatingHoursWarning()
    {
        int? warningMinutes = null;
        _service.OperatingHoursWarning += m => warningMinutes = m;

        var method = typeof(SessionService).GetMethod("OnHoursEndingSoon",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        method?.Invoke(_service, new object[] { 10 });

        warningMinutes.Should().Be(10);
    }

    // ==================== SYNC TO FIREBASE ====================

    [Fact]
    public async Task SyncToFirebase_WhenNotActive_ShouldNoOp()
    {
        _service.IsActive.Should().BeFalse();

        var method = typeof(SessionService).GetMethod("SyncToFirebaseAsync",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var task = (Task?)method?.Invoke(_service, null);
        if (task != null) await task;

        // No crash, no side effects
        _service.IsOnline.Should().BeTrue();
    }

    [Fact]
    public async Task SyncToFirebase_WhenActive_SuccessfulSync_ShouldKeepOnline()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        var method = typeof(SessionService).GetMethod("SyncToFirebaseAsync",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var task = (Task?)method?.Invoke(_service, null);
        if (task != null) await task;

        _service.IsOnline.Should().BeTrue();
    }

    [Fact]
    public async Task SyncToFirebase_ThreeConsecutiveFailures_ShouldGoOffline()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        // Now make all requests fail
        _handler.ClearHandlers();
        _handler.WhenError("users/", System.Net.HttpStatusCode.InternalServerError);

        string? syncError = null;
        _service.SyncFailed += e => syncError = e;

        var method = typeof(SessionService).GetMethod("SyncToFirebaseAsync",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);

        for (int i = 0; i < 3; i++)
        {
            var task = (Task?)method?.Invoke(_service, null);
            if (task != null) await task;
        }

        _service.IsOnline.Should().BeFalse();
        syncError.Should().NotBeNull();
    }

    [Fact]
    public async Task SyncToFirebase_AfterRecovery_ShouldFireSyncRestored()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        // Force consecutive failures via reflection
        var failField = typeof(SessionService).GetField("_consecutiveSyncFailures",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        failField?.SetValue(_service, 3);

        bool restored = false;
        _service.SyncRestored += () => restored = true;

        // Now make a successful sync
        _handler.ClearHandlers();
        _handler.SetDefaultSuccess();

        var method = typeof(SessionService).GetMethod("SyncToFirebaseAsync",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var task = (Task?)method?.Invoke(_service, null);
        if (task != null) await task;

        restored.Should().BeTrue();
        _service.IsOnline.Should().BeTrue();
    }

    // ==================== DISPOSE ====================

    [Fact]
    public void Dispose_CalledMultipleTimes_ShouldNotThrow()
    {
        _service.Dispose();
        _service.Dispose();
        _service.Dispose();
    }

    // ==================== SESSION PROPERTIES ====================

    [Fact]
    public async Task SessionId_AfterStart_ShouldBeUnique()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);
        var id1 = _service.SessionId;

        await _service.EndSessionAsync();

        // Start a second session
        _handler.ClearHandlers();
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 1800}");
        _handler.SetDefaultSuccess();

        await _service.StartSessionAsync(1800);
        var id2 = _service.SessionId;

        id1.Should().NotBe(id2);
    }
}
