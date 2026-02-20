using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class DeviceInfoCoverageTests
{
    [Fact]
    public void GetDeviceId_ReturnsNonEmptyString()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetDeviceId_ReturnsLowercase()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Should().Be(id.ToLowerInvariant());
    }

    [Fact]
    public void GetDeviceId_IsDeterministic()
    {
        var id1 = DeviceInfo.GetDeviceId();
        var id2 = DeviceInfo.GetDeviceId();
        id1.Should().Be(id2);
    }

    [Fact]
    public void GetDeviceId_DoesNotContainColons()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Should().NotContain(":");
    }

    [Fact]
    public void GetComputerName_ReturnsNonEmpty()
    {
        var name = DeviceInfo.GetComputerName();
        name.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetComputerName_MatchesEnvironment()
    {
        var name = DeviceInfo.GetComputerName();
        name.Should().Be(Environment.MachineName);
    }

    [Fact]
    public void GetComputerName_IsDeterministic()
    {
        var n1 = DeviceInfo.GetComputerName();
        var n2 = DeviceInfo.GetComputerName();
        n1.Should().Be(n2);
    }

    [Fact]
    public void GetComputerInfo_ReturnsExpectedKeys()
    {
        var info = DeviceInfo.GetComputerInfo();
        info.Should().ContainKey("computerName");
        info.Should().ContainKey("deviceId");
    }

    [Fact]
    public void GetComputerInfo_ValuesAreNonEmpty()
    {
        var info = DeviceInfo.GetComputerInfo();
        ((string)info["computerName"]).Should().NotBeNullOrEmpty();
        ((string)info["deviceId"]).Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetComputerInfo_MatchesIndividualCalls()
    {
        var info = DeviceInfo.GetComputerInfo();
        ((string)info["computerName"]).Should().Be(DeviceInfo.GetComputerName());
        ((string)info["deviceId"]).Should().Be(DeviceInfo.GetDeviceId());
    }

    [Fact]
    public void GetDeviceId_HasReasonableLength()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Length.Should().BeGreaterThanOrEqualTo(12);
    }
}
