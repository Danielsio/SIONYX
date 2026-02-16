using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class DeviceInfoExtendedTests
{
    [Fact]
    public void GetComputerName_ShouldReturnNonEmpty()
    {
        var name = DeviceInfo.GetComputerName();
        name.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetComputerName_ShouldReturnMachineName()
    {
        var name = DeviceInfo.GetComputerName();
        name.Should().Be(Environment.MachineName);
    }

    [Fact]
    public void GetComputerInfo_ShouldContainExpectedKeys()
    {
        var info = DeviceInfo.GetComputerInfo();
        info.Should().ContainKey("computerName");
        info.Should().ContainKey("deviceId");
    }

    [Fact]
    public void GetComputerInfo_DeviceId_ShouldMatchGetDeviceId()
    {
        var info = DeviceInfo.GetComputerInfo();
        var deviceId = DeviceInfo.GetDeviceId();
        info["deviceId"].ToString().Should().Be(deviceId);
    }

    [Fact]
    public void GetDeviceId_ShouldHaveMinLength()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Length.Should().BeGreaterThanOrEqualTo(12);
    }

    [Fact]
    public void GetDeviceId_ShouldBeLowercase()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Should().Be(id.ToLowerInvariant());
    }
}
