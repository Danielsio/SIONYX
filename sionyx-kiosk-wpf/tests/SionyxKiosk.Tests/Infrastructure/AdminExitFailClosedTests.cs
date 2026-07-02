using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Fail-closed admin exit (H-3): a production kiosk without a configured
/// AdminExitPassword must deny exit instead of accepting the public
/// "dev-exit" constant.
/// </summary>
public class AdminExitFailClosedTests
{
    [Theory]
    [InlineData(null)]
    [InlineData("")]
    public void Production_WithMissingRegistryPassword_DeniesExit(string? registryPassword)
    {
        var result = AppConstants.ResolveAdminExitPassword(true, registryPassword, "env-password");

        result.Should().Be(AppConstants.ExitDeniedSentinel);
        result.Should().NotBe("dev-exit");
    }

    [Fact]
    public void Production_WithRegistryPassword_ReturnsIt()
    {
        AppConstants.ResolveAdminExitPassword(true, "real-kiosk-password", null)
            .Should().Be("real-kiosk-password");
    }

    [Fact]
    public void Production_NeverFallsBackToEnvOrDefault()
    {
        var result = AppConstants.ResolveAdminExitPassword(true, "", "env-password");

        result.Should().NotBe("env-password");
        result.Should().NotBe("dev-exit");
    }

    [Fact]
    public void ExitDeniedSentinel_CannotBeTypedFromKeyboard()
    {
        // NUL characters cannot be entered in a PasswordBox, so equality with
        // any typed password is impossible.
        AppConstants.ExitDeniedSentinel.Should().Contain("\0");
    }

    [Fact]
    public void Development_WithEnvPassword_ReturnsIt()
    {
        AppConstants.ResolveAdminExitPassword(false, null, "env-password")
            .Should().Be("env-password");
    }

    [Fact]
    public void Development_WithoutEnvPassword_ReturnsDevDefault()
    {
        AppConstants.ResolveAdminExitPassword(false, null, null).Should().Be("dev-exit");
        AppConstants.ResolveAdminExitPassword(false, null, "").Should().Be("dev-exit");
    }
}
