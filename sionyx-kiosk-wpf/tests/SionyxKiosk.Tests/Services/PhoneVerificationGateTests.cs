using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Session gate: a user is blocked only when the org requires phone
/// verification AND an admin has not verified them. Off by default, so orgs
/// that never enable it are unaffected.
/// </summary>
public class PhoneVerificationGateTests
{
    [Fact]
    public void RequiredAndUnverified_Blocks()
    {
        KioskSettings.IsSessionBlocked(requireVerification: true, userVerified: false)
            .Should().BeTrue();
    }

    [Fact]
    public void RequiredAndVerified_Allows()
    {
        KioskSettings.IsSessionBlocked(requireVerification: true, userVerified: true)
            .Should().BeFalse();
    }

    [Fact]
    public void NotRequired_AlwaysAllows_EvenWhenUnverified()
    {
        KioskSettings.IsSessionBlocked(requireVerification: false, userVerified: false)
            .Should().BeFalse();
    }

    [Fact]
    public void DefaultSettingsDoNotRequireVerification()
    {
        KioskSettings.Defaults.RequirePhoneVerification.Should().BeFalse();
        KioskSettings.IsSessionBlocked(
            KioskSettings.Defaults.RequirePhoneVerification, userVerified: false)
            .Should().BeFalse();
    }
}
