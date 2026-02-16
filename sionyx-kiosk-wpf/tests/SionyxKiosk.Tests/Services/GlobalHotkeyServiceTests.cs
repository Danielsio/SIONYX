using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class GlobalHotkeyServiceTests
{
    [Fact]
    public void Constructor_ShouldSetAdminExitHotkey()
    {
        var service = new GlobalHotkeyService();
        service.AdminExitHotkey.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void IsRunning_WhenNotStarted_ShouldBeFalse()
    {
        var service = new GlobalHotkeyService();
        service.IsRunning.Should().BeFalse();
    }

    [Fact]
    public void Stop_WithoutStart_ShouldNotThrow()
    {
        var service = new GlobalHotkeyService();
        var act = () => service.Stop();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_ShouldNotThrow()
    {
        var service = new GlobalHotkeyService();
        var act = () => service.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void AdminExitRequested_Event_ShouldBeSubscribable()
    {
        var service = new GlobalHotkeyService();
        service.AdminExitRequested += () => { };
        service.Should().NotBeNull();
    }

    [Fact]
    public void AdminExitHotkey_ShouldContainModifiers()
    {
        var service = new GlobalHotkeyService();
        // Default hotkey should contain Ctrl, Alt, or similar modifiers
        var hotkey = service.AdminExitHotkey.ToLower();
        (hotkey.Contains("ctrl") || hotkey.Contains("alt") || hotkey.Contains("+")).Should().BeTrue();
    }
}
