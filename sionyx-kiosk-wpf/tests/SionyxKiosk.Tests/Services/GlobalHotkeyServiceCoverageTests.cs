using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class GlobalHotkeyServiceCoverageTests
{
    [Fact]
    public void Constructor_SetsDefaultHotkey()
    {
        var svc = new GlobalHotkeyService();
        svc.AdminExitHotkey.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void IsRunning_InitiallyFalse()
    {
        var svc = new GlobalHotkeyService();
        svc.IsRunning.Should().BeFalse();
    }

    [Fact]
    public void Stop_WhenNotRunning_DoesNotThrow()
    {
        var svc = new GlobalHotkeyService();
        var act = () => svc.Stop();
        act.Should().NotThrow();
    }

    [Fact]
    public void Stop_WhenNotRunning_StaysNotRunning()
    {
        var svc = new GlobalHotkeyService();
        svc.Stop();
        svc.IsRunning.Should().BeFalse();
    }

    [Fact]
    public void Dispose_WhenNotStarted_DoesNotThrow()
    {
        var svc = new GlobalHotkeyService();
        var act = () => svc.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_MultipleTimes_DoesNotThrow()
    {
        var svc = new GlobalHotkeyService();
        svc.Dispose();
        var act = () => svc.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void AdminExitRequested_CanSubscribe()
    {
        var svc = new GlobalHotkeyService();
        svc.AdminExitRequested += () => { };
        svc.Should().NotBeNull();
    }

    [Fact]
    public void AdminExitRequested_CanSubscribeMultiple()
    {
        var svc = new GlobalHotkeyService();
        int count = 0;
        svc.AdminExitRequested += () => count++;
        svc.AdminExitRequested += () => count++;
        svc.Should().NotBeNull();
    }

    [Fact]
    public void Start_WithWindowHandle_IsBackwardCompatible()
    {
        var svc = new GlobalHotkeyService();
        svc.Start(IntPtr.Zero);
        svc.Stop();
    }
}
