using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class DeviceInfoTests
{
    [Fact]
    public void GetDeviceId_ShouldReturnNonEmptyString()
    {
        var id = DeviceInfo.GetDeviceId();
        id.Should().NotBeNullOrWhiteSpace();
    }

    [Fact]
    public void GetDeviceId_ShouldBeConsistent()
    {
        var id1 = DeviceInfo.GetDeviceId();
        var id2 = DeviceInfo.GetDeviceId();
        id1.Should().Be(id2);
    }
}
