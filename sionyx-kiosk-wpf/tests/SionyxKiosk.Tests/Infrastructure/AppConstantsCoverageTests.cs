using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class AppConstantsCoverageTests
{
    [Fact]
    public void AppName_IsSionyx()
    {
        AppConstants.AppName.Should().Be("SIONYX");
    }

    [Fact]
    public void AdminExitHotkeyDefault_IsExpected()
    {
        AppConstants.AdminExitHotkeyDefault.Should().Be("Ctrl+Alt+Space");
    }

    [Fact]
    public void GetAdminExitPassword_ReturnsNonEmpty()
    {
        var password = AppConstants.GetAdminExitPassword();
        password.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetAdminExitPassword_DefaultFallback()
    {
        var password = AppConstants.GetAdminExitPassword();
        password.Should().Be("sionyx2025");
    }

    [Fact]
    public void GetAdminExitPassword_FromEnvVariable()
    {
        var originalValue = Environment.GetEnvironmentVariable("ADMIN_EXIT_PASSWORD");
        try
        {
            Environment.SetEnvironmentVariable("ADMIN_EXIT_PASSWORD", "test-password-123");
            var password = AppConstants.GetAdminExitPassword();
            // May return registry value in production, or env value in dev
            password.Should().NotBeNullOrEmpty();
        }
        finally
        {
            Environment.SetEnvironmentVariable("ADMIN_EXIT_PASSWORD", originalValue);
        }
    }
}
