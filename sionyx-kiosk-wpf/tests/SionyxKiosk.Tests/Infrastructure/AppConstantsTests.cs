using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class AppConstantsTests
{
    [Fact]
    public void AppName_ShouldBeSionyx()
    {
        AppConstants.AppName.Should().Be("SIONYX");
    }
}
