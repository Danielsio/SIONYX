using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Exit-unlock decision table. A remote (web-console) password, when configured,
/// is authoritative; otherwise the installer-provisioned local password applies —
/// and stays fail-closed (H-3) when none was provisioned.
/// </summary>
public class ExitPasswordVerifierTests
{
    private const string Local = "local-pass";

    [Fact]
    public void RemoteConfiguredAndValid_Unlocks()
    {
        ExitPasswordVerifier.IsAllowed("whatever", remoteConfigured: true, remoteValid: true, Local)
            .Should().BeTrue();
    }

    [Fact]
    public void RemoteConfiguredAndInvalid_Denies()
    {
        ExitPasswordVerifier.IsAllowed("wrong", remoteConfigured: true, remoteValid: false, Local)
            .Should().BeFalse();
    }

    [Fact]
    public void RotatingTheRemotePasswordInvalidatesTheOldLocalOne()
    {
        // The whole point of remote rotation: once the org sets a password, the
        // stale installer password must NOT still open the kiosk.
        ExitPasswordVerifier.IsAllowed(Local, remoteConfigured: true, remoteValid: false, Local)
            .Should().BeFalse();
    }

    [Fact]
    public void NoRemotePassword_LocalPasswordUnlocks()
    {
        ExitPasswordVerifier.IsAllowed(Local, remoteConfigured: false, remoteValid: false, Local)
            .Should().BeTrue();
    }

    [Fact]
    public void NoRemotePassword_WrongLocalPasswordDenies()
    {
        ExitPasswordVerifier.IsAllowed("nope", remoteConfigured: false, remoteValid: false, Local)
            .Should().BeFalse();
    }

    [Fact]
    public void BackendUnreachable_FallsBackToTheLocalPassword()
    {
        // VerifyExitPasswordAsync reports (configured: false) when it cannot reach
        // the server, so the kiosk stays openable by the provisioned password.
        ExitPasswordVerifier.IsAllowed(Local, remoteConfigured: false, remoteValid: false, Local)
            .Should().BeTrue();
    }

    [Fact]
    public void FailsClosedWhenNoPasswordIsProvisionedAtAll()
    {
        // AppConstants returns an untypeable sentinel on a misconfigured
        // production kiosk; nothing the operator types may match it.
        var sentinel = AppConstants.ExitDeniedSentinel;
        ExitPasswordVerifier.IsAllowed("", remoteConfigured: false, remoteValid: false, sentinel)
            .Should().BeFalse();
        ExitPasswordVerifier.IsAllowed("1234", remoteConfigured: false, remoteValid: false, sentinel)
            .Should().BeFalse();
    }

    [Fact]
    public void EmptyInputNeverUnlocksAnEmptyLocalPassword()
    {
        ExitPasswordVerifier.IsAllowed("", remoteConfigured: false, remoteValid: false, "")
            .Should().BeFalse();
    }
}
