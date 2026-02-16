using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class ProcessRestrictionExtendedTests
{
    [Fact]
    public void AddToBlacklist_ShouldAddProcess()
    {
        var service = new ProcessRestrictionService(enabled: false);
        var initialCount = service.GetBlacklist().Count;

        service.AddToBlacklist("custom_app.exe");

        service.GetBlacklist().Should().Contain("custom_app.exe");
        service.GetBlacklist().Count.Should().Be(initialCount + 1);
    }

    [Fact]
    public void RemoveFromBlacklist_ShouldRemoveProcess()
    {
        var service = new ProcessRestrictionService(enabled: false);
        service.AddToBlacklist("custom_app.exe");

        service.RemoveFromBlacklist("custom_app.exe");

        service.GetBlacklist().Should().NotContain("custom_app.exe");
    }

    [Fact]
    public void GetBlacklist_ShouldReturnSortedList()
    {
        var service = new ProcessRestrictionService(enabled: false);
        var list = service.GetBlacklist();

        list.Should().BeInAscendingOrder();
    }

    [Fact]
    public void GetBlacklist_ShouldContainDefaultItems()
    {
        var service = new ProcessRestrictionService(enabled: false);
        var list = service.GetBlacklist();

        list.Should().Contain(l => l.Contains("regedit", StringComparison.OrdinalIgnoreCase));
        list.Should().Contain(l => l.Contains("cmd", StringComparison.OrdinalIgnoreCase));
        list.Should().Contain(l => l.Contains("powershell", StringComparison.OrdinalIgnoreCase));
        list.Should().Contain(l => l.Contains("taskmgr", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void Constructor_WithCustomBlacklist_ShouldUseIt()
    {
        var custom = new HashSet<string> { "app1.exe", "app2.exe" };
        var service = new ProcessRestrictionService(blacklist: custom, enabled: false);

        service.GetBlacklist().Count.Should().Be(2);
    }

    [Fact]
    public void Enabled_ShouldBeConfigurable()
    {
        var service = new ProcessRestrictionService(enabled: false);
        service.Enabled.Should().BeFalse();

        service.Enabled = true;
        service.Enabled.Should().BeTrue();
    }

    [Fact]
    public void IsActive_WhenDisabled_ShouldBeFalse()
    {
        var service = new ProcessRestrictionService(enabled: false);
        service.IsActive.Should().BeFalse();
    }

    [Fact]
    public void Start_WhenDisabled_ShouldNotActivate()
    {
        var service = new ProcessRestrictionService(enabled: false);
        service.Start();
        service.IsActive.Should().BeFalse();
    }

    [Fact]
    public void ProcessBlocked_Event_ShouldBeSubscribable()
    {
        var service = new ProcessRestrictionService(enabled: false);
        service.ProcessBlocked += _ => { };
        service.ErrorOccurred += _ => { };
    }

    [Fact]
    public void Dispose_ShouldNotThrow()
    {
        var service = new ProcessRestrictionService(enabled: false);
        service.Start();
        var act = () => service.Dispose();
        act.Should().NotThrow();
    }
}
