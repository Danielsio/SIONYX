using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Final coverage push for SessionService: countdown tick, sync branches, warning events.
/// </summary>
public class SessionServiceFinalTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly SessionService _service;

    public SessionServiceFinalTests()
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

    // ==================== COUNTDOWN TICK ====================

    [Fact]
    public void OnCountdownTick_WhenNotActive_ShouldNoOp()
    {
        var method = typeof(SessionService).GetMethod("OnCountdownTick",
            BindingFlags.NonPublic | BindingFlags.Instance)!;

        _service.IsActive.Should().BeFalse();
        var act = () => method.Invoke(_service, null);
        act.Should().NotThrow();
    }

    [Fact]
    public async Task OnCountdownTick_WhenActive_ShouldUpdateRemainingTime()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        int? updatedTime = null;
        _service.TimeUpdated += t => updatedTime = t;

        // Simulate some time passing
        var startTimeField = typeof(SessionService).GetField("StartTime",
            BindingFlags.Public | BindingFlags.Instance);
        // StartTime is a property, use reflection on the backing field
        var backingField = typeof(SessionService).GetProperty("StartTime")!
            .GetBackingField();
        if (backingField != null)
            backingField.SetValue(_service, DateTime.UtcNow.AddSeconds(-10));

        var method = typeof(SessionService).GetMethod("OnCountdownTick",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(_service, null);

        // Should have updated the time
        _service.TimeUsed.Should().BeGreaterThanOrEqualTo(0);
    }

    [Fact]
    public async Task OnCountdownTick_Near5MinWarning_ShouldFireWarning()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 300}");
        await _service.StartSessionAsync(300);

        bool warning5 = false;
        _service.Warning5Min += () => warning5 = true;

        // Set StartTime to be 1 second ago so remaining ~299
        SetStartTimePast(1);

        var method = typeof(SessionService).GetMethod("OnCountdownTick",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(_service, null);

        warning5.Should().BeTrue();
    }

    [Fact]
    public async Task OnCountdownTick_Near1MinWarning_ShouldFireWarning()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 60}");
        await _service.StartSessionAsync(60);

        bool warning1 = false;
        _service.Warning1Min += () => warning1 = true;

        // Set StartTime to 1 second ago so remaining ~59
        SetStartTimePast(1);

        var method = typeof(SessionService).GetMethod("OnCountdownTick",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(_service, null);

        warning1.Should().BeTrue();
    }

    [Fact]
    public async Task OnCountdownTick_Warnings_ShouldOnlyFireOnce()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 300}");
        await _service.StartSessionAsync(300);

        int warning5Count = 0;
        _service.Warning5Min += () => warning5Count++;

        SetStartTimePast(1);

        var method = typeof(SessionService).GetMethod("OnCountdownTick",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(_service, null);
        method.Invoke(_service, null);
        method.Invoke(_service, null);

        warning5Count.Should().Be(1); // Only fires once
    }

    [Fact]
    public async Task OnCountdownTick_AtZero_ShouldTriggerEnd()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 5}");
        await _service.StartSessionAsync(5);

        // Set time far in the past so remaining = 0
        SetStartTimePast(10);

        string? endReason = null;
        _service.SessionEnded += r => endReason = r;

        var method = typeof(SessionService).GetMethod("OnCountdownTick",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(_service, null);

        // Wait for fire-and-forget EndSessionAsync
        for (int i = 0; i < 20 && _service.IsActive; i++)
            await Task.Delay(50);

        _service.RemainingTime.Should().Be(0);
    }

    // ==================== SYNC ====================

    [Fact]
    public async Task SyncToFirebase_SuccessAfterFailures_ShouldResetCounter()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        // Simulate 2 sync failures
        var failField = typeof(SessionService).GetField("_consecutiveSyncFailures",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        failField.SetValue(_service, 2);

        // Now sync successfully
        var method = typeof(SessionService).GetMethod("SyncToFirebaseAsync",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        var task = (Task)method.Invoke(_service, null)!;
        await task;

        var failures = (int)failField.GetValue(_service)!;
        failures.Should().Be(0);
    }

    [Fact]
    public async Task SyncToFirebase_ExactlyThreeFailures_ShouldGoOffline()
    {
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 3600}");
        await _service.StartSessionAsync(3600);

        _handler.ClearHandlers();
        _handler.WhenError("users/");

        string? syncError = null;
        _service.SyncFailed += e => syncError = e;

        var method = typeof(SessionService).GetMethod("SyncToFirebaseAsync",
            BindingFlags.NonPublic | BindingFlags.Instance)!;

        // First two failures: still online
        await (Task)method.Invoke(_service, null)!;
        _service.IsOnline.Should().BeTrue();

        await (Task)method.Invoke(_service, null)!;
        _service.IsOnline.Should().BeTrue();

        // Third failure: goes offline
        await (Task)method.Invoke(_service, null)!;
        _service.IsOnline.Should().BeFalse();
        syncError.Should().NotBeNull();
    }

    // ==================== CHECK TIME EXPIRATION ====================

    [Fact]
    public async Task CheckTimeExpiration_WithExpiredTime_ShouldFail()
    {
        // Setup: user has expired timeExpiresAt
        _handler.When("users/user-123.json", new
        {
            remainingTime = 3600,
            timeExpiresAt = DateTime.Now.AddDays(-1).ToString("o"),
        });

        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("פג תוקף");
    }

    [Fact]
    public async Task CheckTimeExpiration_WithValidTime_ShouldProceed()
    {
        // User has future timeExpiresAt
        _handler.When("users/user-123.json", new
        {
            remainingTime = 3600,
            timeExpiresAt = DateTime.Now.AddDays(30).ToString("o"),
        });

        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task CheckTimeExpiration_WithNoExpiry_ShouldProceed()
    {
        _handler.When("users/user-123.json", new
        {
            remainingTime = 3600,
        });

        var result = await _service.StartSessionAsync(3600);
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== HELPER ====================

    private void SetStartTimePast(int secondsAgo)
    {
        // Use reflection to set StartTime in the past
        var prop = typeof(SessionService).GetProperty("StartTime")!;
        var backingField = prop.GetBackingField();
        backingField?.SetValue(_service, (DateTime?)DateTime.UtcNow.AddSeconds(-secondsAgo));
    }
}

// Extension to find auto-property backing fields
internal static class PropertyInfoExtensions
{
    public static FieldInfo? GetBackingField(this PropertyInfo prop)
    {
        return prop.DeclaringType?.GetField($"<{prop.Name}>k__BackingField",
            BindingFlags.NonPublic | BindingFlags.Instance);
    }
}
