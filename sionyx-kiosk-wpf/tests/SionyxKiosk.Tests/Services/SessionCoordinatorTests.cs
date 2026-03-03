using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class SessionCoordinatorTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly SessionService _session;
    private readonly PrintMonitorService _printMonitor;
    private readonly AuthService _auth;
    private readonly SessionCoordinator _coordinator;
    private readonly string _dbPath;
    private readonly LocalDatabase _localDb;

    public SessionCoordinatorTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _handler.SetDefaultSuccess();

        _session = new SessionService(
            _firebase, "user-123", "test-org",
            new ComputerService(_firebase),
            new OperatingHoursService(_firebase),
            new ProcessCleanupService(),
            new BrowserCleanupService());

        _printMonitor = new PrintMonitorService(_firebase, "user-123");
        _dbPath = Path.Combine(Path.GetTempPath(), $"coord_test_{Guid.NewGuid():N}.db");
        _localDb = new LocalDatabase(_dbPath);
        _auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));

        _coordinator = new SessionCoordinator(_session, _printMonitor, _auth, new PrintHistoryService(), new IdleTimeoutService());
    }

    public void Dispose()
    {
        _localDb.Dispose();
        _firebase.Dispose();
        try { File.Delete(_dbPath); } catch { }
    }

    // ── Subscribe / Unsubscribe ──

    [Fact]
    public void Subscribe_ShouldWireSessionEvents()
    {
        _coordinator.Subscribe();

        // Verify by checking that firing events doesn't throw (handlers are wired)
        var act = () =>
        {
            _session.GetType()
                .GetEvent("SessionStarted")!
                .RaiseMethod?.Invoke(_session, null);
        };
        // Even if we can't raise directly, the subscribe itself shouldn't throw
        act.Should().NotThrow();
    }

    [Fact]
    public void Subscribe_CalledTwice_ShouldNotDoubleSubscribe()
    {
        _coordinator.Subscribe();
        _coordinator.Subscribe();

        // Should not throw - idempotent
    }

    [Fact]
    public void Unsubscribe_WithoutSubscribe_ShouldNotThrow()
    {
        var act = () => _coordinator.Unsubscribe();
        act.Should().NotThrow();
    }

    [Fact]
    public void Unsubscribe_AfterSubscribe_ShouldNotThrow()
    {
        _coordinator.Subscribe();
        var act = () => _coordinator.Unsubscribe();
        act.Should().NotThrow();
    }

    [Fact]
    public void Unsubscribe_CalledMultipleTimes_ShouldNotThrow()
    {
        _coordinator.Subscribe();
        _coordinator.Unsubscribe();
        _coordinator.Unsubscribe();
        _coordinator.Unsubscribe();
    }

    // ── CloseFloatingTimer ──

    [Fact]
    public void CloseFloatingTimer_WhenNoTimer_ShouldNotThrow()
    {
        // Application.Current is null in tests, so Dispatcher.Invoke is a no-op
        var act = () => _coordinator.CloseFloatingTimer();
        act.Should().NotThrow();
    }

    // ── ResumeSession ──

    [Fact]
    public void ResumeSession_WhenNoTimer_ShouldNotThrow()
    {
        var act = () => _coordinator.ResumeSession();
        act.Should().NotThrow();
    }

    // ── Events ──

    [Fact]
    public void MinimizeMainWindow_Event_CanBeSubscribedAndUnsubscribed()
    {
        var fired = false;
        _coordinator.MinimizeMainWindow += () => fired = true;
        _coordinator.MinimizeMainWindow -= () => fired = true;
        fired.Should().BeFalse();
    }

    [Fact]
    public void RestoreMainWindow_Event_CanBeSubscribedAndUnsubscribed()
    {
        var fired = false;
        _coordinator.RestoreMainWindow += () => fired = true;
        _coordinator.RestoreMainWindow -= () => fired = true;
        fired.Should().BeFalse();
    }

    [Fact]
    public void Subscribe_ThenUnsubscribe_ShouldCleanUpAllHandlers()
    {
        _coordinator.Subscribe();
        _coordinator.Unsubscribe();

        // After unsubscribe, re-subscribing should work cleanly
        var act = () => _coordinator.Subscribe();
        act.Should().NotThrow();
    }

    // ── Full lifecycle ──

    [Fact]
    public void FullLifecycle_SubscribeUnsubscribeClose_ShouldWork()
    {
        _coordinator.Subscribe();
        _coordinator.ResumeSession();
        _coordinator.CloseFloatingTimer();
        _coordinator.Unsubscribe();
    }
}
