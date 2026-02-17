using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Tests for DeviceInfo: device ID generation, computer name, computer info.
/// </summary>
public class DeviceInfoTests
{
    // ==================== GET DEVICE ID ====================

    [Fact]
    public void GetDeviceId_ShouldReturnNonEmptyString()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetDeviceId_ShouldReturnConsistentResult()
    {
        var id1 = DeviceInfo.GetDeviceId();
        var id2 = DeviceInfo.GetDeviceId();
        id1.Should().Be(id2);
    }

    [Fact]
    public void GetDeviceId_ShouldReturnLowercase()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Should().Be(id.ToLowerInvariant());
    }

    [Fact]
    public void GetDeviceId_ShouldBeAtLeast8Characters()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Length.Should().BeGreaterThanOrEqualTo(8);
    }

    // ==================== GET COMPUTER NAME ====================

    [Fact]
    public void GetComputerName_ShouldReturnNonEmptyString()
    {
        var name = DeviceInfo.GetComputerName();
        name.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetComputerName_ShouldReturnConsistentResult()
    {
        var name1 = DeviceInfo.GetComputerName();
        var name2 = DeviceInfo.GetComputerName();
        name1.Should().Be(name2);
    }

    [Fact]
    public void GetComputerName_ShouldNotBeUnknownPC()
    {
        // On a real machine, we should get the actual name
        var name = DeviceInfo.GetComputerName();
        name.Should().NotBe("Unknown-PC");
    }

    // ==================== GET COMPUTER INFO ====================

    [Fact]
    public void GetComputerInfo_ShouldContainComputerName()
    {
        var info = DeviceInfo.GetComputerInfo();
        info.Should().ContainKey("computerName");
        info["computerName"].Should().NotBeNull();
        info["computerName"].ToString().Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetComputerInfo_ShouldContainDeviceId()
    {
        var info = DeviceInfo.GetComputerInfo();
        info.Should().ContainKey("deviceId");
        info["deviceId"].Should().NotBeNull();
        info["deviceId"].ToString().Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetComputerInfo_DeviceId_ShouldMatchGetDeviceId()
    {
        var info = DeviceInfo.GetComputerInfo();
        var directId = DeviceInfo.GetDeviceId();
        info["deviceId"].ToString().Should().Be(directId);
    }

    [Fact]
    public void GetComputerInfo_ComputerName_ShouldMatchGetComputerName()
    {
        var info = DeviceInfo.GetComputerInfo();
        var directName = DeviceInfo.GetComputerName();
        info["computerName"].ToString().Should().Be(directName);
    }
}
