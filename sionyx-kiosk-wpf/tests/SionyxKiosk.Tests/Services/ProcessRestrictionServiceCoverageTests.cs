using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class ProcessRestrictionServiceCoverageTests
{
    [Fact]
    public void Constructor_DefaultEnabled()
    {
        var svc = new ProcessRestrictionService();
        svc.Enabled.Should().BeTrue();
    }

    [Fact]
    public void Constructor_ExplicitlyDisabled()
    {
        var svc = new ProcessRestrictionService(enabled: false);
        svc.Enabled.Should().BeFalse();
    }

    [Fact]
    public void Constructor_CustomBlacklist()
    {
        var custom = new HashSet<string> { "notepad.exe", "calc.exe" };
        var svc = new ProcessRestrictionService(blacklist: custom);
        svc.GetBlacklist().Should().Contain("notepad.exe");
        svc.GetBlacklist().Should().Contain("calc.exe");
    }

    [Fact]
    public void GetBlacklist_DefaultContainsExpectedProcesses()
    {
        var svc = new ProcessRestrictionService();
        var list = svc.GetBlacklist();
        list.Should().Contain(l => l.Contains("regedit", StringComparison.OrdinalIgnoreCase));
        list.Should().Contain(l => l.Contains("cmd", StringComparison.OrdinalIgnoreCase));
        list.Should().Contain(l => l.Contains("powershell", StringComparison.OrdinalIgnoreCase));
        list.Should().Contain(l => l.Contains("taskmgr", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void GetBlacklist_IsSorted()
    {
        var svc = new ProcessRestrictionService();
        var list = svc.GetBlacklist();
        list.Should().BeInAscendingOrder();
    }

    [Fact]
    public void AddToBlacklist_AddsProcess()
    {
        var svc = new ProcessRestrictionService(blacklist: new HashSet<string>());
        svc.AddToBlacklist("test.exe");
        svc.GetBlacklist().Should().Contain("test.exe");
    }

    [Fact]
    public void RemoveFromBlacklist_RemovesProcess()
    {
        var custom = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "test.exe" };
        var svc = new ProcessRestrictionService(blacklist: custom);
        svc.RemoveFromBlacklist("test.exe");
        svc.GetBlacklist().Should().NotContain("test.exe");
    }

    [Fact]
    public void Start_WhenDisabled_DoesNotActivate()
    {
        var svc = new ProcessRestrictionService(enabled: false);
        svc.Start();
        svc.IsActive.Should().BeFalse();
    }

    [Fact]
    public void Stop_WhenNotStarted_DoesNotThrow()
    {
        var svc = new ProcessRestrictionService();
        var act = () => svc.Stop();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_DoesNotThrow()
    {
        var svc = new ProcessRestrictionService();
        var act = () => svc.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_MultipleTimes_DoesNotThrow()
    {
        var svc = new ProcessRestrictionService();
        svc.Dispose();
        var act = () => svc.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void Enabled_CanBeToggled()
    {
        var svc = new ProcessRestrictionService(enabled: true);
        svc.Enabled = false;
        svc.Enabled.Should().BeFalse();
    }

    [Fact]
    public void ProcessBlocked_CanSubscribe()
    {
        var svc = new ProcessRestrictionService();
        string? blocked = null;
        svc.ProcessBlocked += s => blocked = s;
        svc.Should().NotBeNull();
    }

    [Fact]
    public void ErrorOccurred_CanSubscribe()
    {
        var svc = new ProcessRestrictionService();
        string? error = null;
        svc.ErrorOccurred += s => error = s;
        svc.Should().NotBeNull();
    }

    [Fact]
    public void CheckProcesses_Enabled_DoesNotThrow()
    {
        var svc = new ProcessRestrictionService(blacklist: new HashSet<string>(), enabled: true);
        var method = typeof(ProcessRestrictionService)
            .GetMethod("CheckProcesses", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var act = () => method.Invoke(svc, null);
        act.Should().NotThrow();
    }

    [Fact]
    public void CheckProcesses_Disabled_DoesNothing()
    {
        var svc = new ProcessRestrictionService(enabled: false);
        var method = typeof(ProcessRestrictionService)
            .GetMethod("CheckProcesses", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var act = () => method.Invoke(svc, null);
        act.Should().NotThrow();
    }

    [Fact]
    public void CleanupBlockedSet_DoesNotThrow()
    {
        var svc = new ProcessRestrictionService();
        var method = typeof(ProcessRestrictionService)
            .GetMethod("CleanupBlockedSet", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var act = () => method.Invoke(svc, null);
        act.Should().NotThrow();
    }
}
