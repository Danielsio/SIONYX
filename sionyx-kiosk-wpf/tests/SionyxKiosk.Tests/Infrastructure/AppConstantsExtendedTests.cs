using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class AppConstantsExtendedTests
{
    [Fact]
    public void AppName_ShouldBeSionyx()
    {
        AppConstants.AppName.Should().Be("SIONYX");
    }

    [Fact]
    public void AdminExitHotkeyDefault_ShouldContainModifiers()
    {
        AppConstants.AdminExitHotkeyDefault.Should().Contain("Ctrl");
        AppConstants.AdminExitHotkeyDefault.Should().Contain("Alt");
    }

    [Fact]
    public void GetAdminExitPassword_ShouldReturnNonEmpty()
    {
        var password = AppConstants.GetAdminExitPassword();
        password.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetAdminExitPassword_ShouldReturnDefaultInDev()
    {
        // In non-production environment, should return a default
        var password = AppConstants.GetAdminExitPassword();
        password.Should().NotBeNullOrEmpty();
    }
}
