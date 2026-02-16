using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Deep tests for DeviceInfo covering all public methods.
/// </summary>
public class DeviceInfoDeepTests
{
    [Fact]
    public void GetDeviceId_ShouldReturnNonEmptyString()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetDeviceId_ShouldReturnConsistentId()
    {
        var id1 = DeviceInfo.GetDeviceId();
        var id2 = DeviceInfo.GetDeviceId();
        id1.Should().Be(id2);
    }

    [Fact]
    public void GetDeviceId_ShouldBeLowercase()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Should().Be(id.ToLowerInvariant());
    }

    [Fact]
    public void GetDeviceId_ShouldBeReasonableLength()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Length.Should().BeGreaterThanOrEqualTo(12);
    }

    [Fact]
    public void GetDeviceId_ShouldNotContainColons()
    {
        // MAC addresses have colons removed
        var id = DeviceInfo.GetDeviceId();
        id.Should().NotContain(":");
    }

    [Fact]
    public void GetComputerName_ShouldReturnNonEmptyString()
    {
        var name = DeviceInfo.GetComputerName();
        name.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetComputerName_ShouldMatchMachineName()
    {
        var name = DeviceInfo.GetComputerName();
        name.Should().Be(Environment.MachineName);
    }

    [Fact]
    public void GetComputerInfo_ShouldReturnDictionary()
    {
        var info = DeviceInfo.GetComputerInfo();
        info.Should().NotBeNull();
        info.Should().ContainKey("computerName");
        info.Should().ContainKey("deviceId");
    }

    [Fact]
    public void GetComputerInfo_ComputerName_ShouldMatchGetComputerName()
    {
        var info = DeviceInfo.GetComputerInfo();
        info["computerName"].Should().Be(DeviceInfo.GetComputerName());
    }

    [Fact]
    public void GetComputerInfo_DeviceId_ShouldMatchGetDeviceId()
    {
        var info = DeviceInfo.GetComputerInfo();
        info["deviceId"].Should().Be(DeviceInfo.GetDeviceId());
    }

    [Fact]
    public void GetDeviceId_ShouldContainOnlyHexOrAlphanumeric()
    {
        var id = DeviceInfo.GetDeviceId();
        // Should be all hex characters (a-f, 0-9) since it's either MAC or SHA256 hash
        id.Should().MatchRegex("^[a-f0-9]+$");
    }
}
