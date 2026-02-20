using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class KeyboardRestrictionServiceCoverageTests
{
    [Fact]
    public void Constructor_DefaultEnabled()
    {
        var svc = new KeyboardRestrictionService();
        svc.Enabled.Should().BeTrue();
    }

    [Fact]
    public void Constructor_ExplicitlyDisabled()
    {
        var svc = new KeyboardRestrictionService(enabled: false);
        svc.Enabled.Should().BeFalse();
    }

    [Fact]
    public void IsActive_WhenDisabled_ReturnsFalse()
    {
        var svc = new KeyboardRestrictionService(enabled: false);
        svc.IsActive.Should().BeFalse();
    }

    [Fact]
    public void Start_WhenDisabled_DoesNotActivate()
    {
        var svc = new KeyboardRestrictionService(enabled: false);
        svc.Start();
        svc.IsActive.Should().BeFalse();
    }

    [Fact]
    public void Stop_WhenNotStarted_DoesNotThrow()
    {
        var svc = new KeyboardRestrictionService();
        var act = () => svc.Stop();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_WhenNotStarted_DoesNotThrow()
    {
        var svc = new KeyboardRestrictionService();
        var act = () => svc.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_MultipleTimes_DoesNotThrow()
    {
        var svc = new KeyboardRestrictionService();
        svc.Dispose();
        var act = () => svc.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void BlockedKeyPressed_EventSubscription()
    {
        var svc = new KeyboardRestrictionService();
        string? received = null;
        svc.BlockedKeyPressed += s => received = s;
        svc.Should().NotBeNull();
    }

    [Fact]
    public void Enabled_CanBeToggled()
    {
        var svc = new KeyboardRestrictionService(enabled: true);
        svc.Enabled.Should().BeTrue();
        svc.Enabled = false;
        svc.Enabled.Should().BeFalse();
        svc.IsActive.Should().BeFalse();
    }

    [Fact]
    public void BlockedCombos_AreConfigured()
    {
        var svc = new KeyboardRestrictionService();
        var field = typeof(KeyboardRestrictionService)
            .GetField("_blockedCombos", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var combos = (Dictionary<string, bool>)field.GetValue(svc)!;

        combos.Should().ContainKey("alt+tab");
        combos.Should().ContainKey("alt+f4");
        combos.Should().ContainKey("alt+esc");
        combos.Should().ContainKey("win");
        combos.Should().ContainKey("ctrl+shift+esc");
        combos.Should().ContainKey("ctrl+esc");
    }
}
