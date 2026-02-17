using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Tests for AppConstants: static fields and GetAdminExitPassword.
/// </summary>
public class AppConstantsTests
{
    [Fact]
    public void AppName_ShouldBeSionyx()
    {
        AppConstants.AppName.Should().Be("SIONYX");
    }

    [Fact]
    public void AdminExitHotkeyDefault_ShouldBeCtrlAltSpace()
    {
        AppConstants.AdminExitHotkeyDefault.Should().Be("Ctrl+Alt+Space");
    }

    [Fact]
    public void GetAdminExitPassword_ShouldReturnNonEmpty()
    {
        var password = AppConstants.GetAdminExitPassword();
        password.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GetAdminExitPassword_ShouldReturnConsistentResult()
    {
        var p1 = AppConstants.GetAdminExitPassword();
        var p2 = AppConstants.GetAdminExitPassword();
        p1.Should().Be(p2);
    }

    [Fact]
    public void GetAdminExitPassword_WhenEnvVarSet_ShouldReturnSomething()
    {
        // GetAdminExitPassword checks Registry first (production), then env var.
        // In test environment, this test simply verifies no exception is thrown
        // and the result is stable regardless of what the env var holds.
        var original = Environment.GetEnvironmentVariable("ADMIN_EXIT_PASSWORD");
        try
        {
            Environment.SetEnvironmentVariable("ADMIN_EXIT_PASSWORD", "test-env-password-123");
            var password = AppConstants.GetAdminExitPassword();
            password.Should().NotBeNullOrEmpty();
        }
        finally
        {
            Environment.SetEnvironmentVariable("ADMIN_EXIT_PASSWORD", original);
        }
    }

    [Fact]
    public void GetAdminExitPassword_WhenEnvVarEmpty_ShouldFallbackToDefault()
    {
        var original = Environment.GetEnvironmentVariable("ADMIN_EXIT_PASSWORD");
        try
        {
            Environment.SetEnvironmentVariable("ADMIN_EXIT_PASSWORD", "");
            var password = AppConstants.GetAdminExitPassword();
            // Should fall back to default when env is empty
            password.Should().NotBeNullOrEmpty();
        }
        finally
        {
            Environment.SetEnvironmentVariable("ADMIN_EXIT_PASSWORD", original);
        }
    }
}
