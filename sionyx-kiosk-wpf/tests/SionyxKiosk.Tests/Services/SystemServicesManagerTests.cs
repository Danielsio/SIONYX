using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class SystemServicesManagerTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly SessionService _session;
    private readonly ForceLogoutService _forceLogout;
    private readonly ChatService _chat;
    private readonly PrintMonitorService _printMonitor;
    private readonly OperatingHoursService _operatingHours;
    private readonly KeyboardRestrictionService _keyboard;
    private readonly ProcessRestrictionService _processRestriction;
    private readonly GlobalHotkeyService _globalHotkey;
    private readonly SystemServicesManager _manager;

    public SystemServicesManagerTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _handler.SetDefaultSuccess();

        _forceLogout = new ForceLogoutService(_firebase);
        _chat = new ChatService(_firebase, "user-123");
        _printMonitor = new PrintMonitorService(_firebase, "user-123");
        _operatingHours = new OperatingHoursService(_firebase);
        _keyboard = new KeyboardRestrictionService(enabled: false);
        _processRestriction = new ProcessRestrictionService(enabled: false);
        _globalHotkey = new GlobalHotkeyService();
        _session = new SessionService(
            _firebase, "user-123", "test-org",
            new ComputerService(_firebase),
            _operatingHours,
            new ProcessCleanupService(),
            new BrowserCleanupService());

        _manager = new SystemServicesManager(
            _forceLogout, _chat, _printMonitor, _operatingHours,
            _keyboard, _processRestriction, _globalHotkey);
    }

    public void Dispose() => _firebase.Dispose();

    // ── Start ──

    [Fact]
    public void Start_WithEmptyUserId_ShouldReturnEarly()
    {
        var act = () => _manager.Start("", isKiosk: false);
        act.Should().NotThrow();
    }

    [Fact]
    public void Start_WithNullUserId_ShouldReturnEarly()
    {
        var act = () => _manager.Start(null!, isKiosk: false);
        act.Should().NotThrow();
    }

    [Fact]
    public void Start_WithValidUserId_NonKiosk_ShouldNotThrow()
    {
        var act = () => _manager.Start("user-123", isKiosk: false);
        act.Should().NotThrow();
    }

    [Fact]
    public void Start_WithValidUserId_Kiosk_ShouldNotThrow()
    {
        // Process restriction and keyboard are disabled in ctor, so Start won't actually restrict
        var act = () => _manager.Start("user-123", isKiosk: true);
        act.Should().NotThrow();
    }

    [Fact]
    public void Start_CalledTwice_ShouldNotThrow()
    {
        _manager.Start("user-123", isKiosk: false);
        var act = () => _manager.Start("user-456", isKiosk: false);
        act.Should().NotThrow();
    }

    // ── StopAsync ──

    [Fact]
    public async Task StopAsync_WithoutStart_ShouldNotThrow()
    {
        var act = () => _manager.StopAsync(_session);
        await act.Should().NotThrowAsync();
    }

    [Fact]
    public async Task StopAsync_AfterStart_ShouldNotThrow()
    {
        _manager.Start("user-123", isKiosk: false);
        var act = () => _manager.StopAsync(_session);
        await act.Should().NotThrowAsync();
    }

    [Fact]
    public async Task StopAsync_CalledMultipleTimes_ShouldNotThrow()
    {
        _manager.Start("user-123", isKiosk: false);
        await _manager.StopAsync(_session);
        var act = () => _manager.StopAsync(_session);
        await act.Should().NotThrowAsync();
    }

    // ── StopAll ──

    [Fact]
    public void StopAll_WithoutStart_ShouldNotThrow()
    {
        var act = () => _manager.StopAll();
        act.Should().NotThrow();
    }

    [Fact]
    public void StopAll_AfterStart_ShouldNotThrow()
    {
        _manager.Start("user-123", isKiosk: true);
        var act = () => _manager.StopAll();
        act.Should().NotThrow();
    }

    // ── StartGlobalHotkey ──

    [Fact]
    public void StartGlobalHotkey_ShouldNotThrow()
    {
        var act = () => _manager.StartGlobalHotkey();
        act.Should().NotThrow();
    }

    [Fact]
    public void StartGlobalHotkey_CalledTwice_ShouldNotThrow()
    {
        _manager.StartGlobalHotkey();
        var act = () => _manager.StartGlobalHotkey();
        act.Should().NotThrow();
    }

    // ── Events ──

    [Fact]
    public void ForceLogoutReceived_CanSubscribe()
    {
        var fired = false;
        _manager.ForceLogoutReceived += () => { fired = true; return Task.CompletedTask; };
        fired.Should().BeFalse();
    }

    [Fact]
    public void AdminExitRequested_CanSubscribe()
    {
        var fired = false;
        _manager.AdminExitRequested += () => fired = true;
        fired.Should().BeFalse();
    }

    // ── Full lifecycle ──

    [Fact]
    public async Task FullLifecycle_StartStopAll_ShouldWork()
    {
        _manager.StartGlobalHotkey();
        _manager.Start("user-123", isKiosk: true);
        await _manager.StopAsync(_session);
        _manager.StopAll();
    }

    [Fact]
    public async Task FullLifecycle_MultipleUsers_ShouldWork()
    {
        _manager.Start("user-1", isKiosk: false);
        await _manager.StopAsync(_session);

        _manager.Start("user-2", isKiosk: true);
        await _manager.StopAsync(_session);
        _manager.StopAll();
    }
}
