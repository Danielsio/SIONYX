using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Release-channel gate: a fork publishing its own releases (different
/// channel) must never be auto-installed onto these kiosks; releases without
/// a channel (published before the edition scheme) stay installable.
/// </summary>
public class UpdateChannelTests
{
    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("origin")]
    [InlineData("ORIGIN")]
    public void AcceptsOwnChannelAndLegacyReleases(string? channel)
    {
        AutoUpdateService.IsAcceptableChannel(channel).Should().BeTrue();
    }

    [Theory]
    [InlineData("fork")]
    [InlineData("maxmax264")]
    [InlineData("beta")]
    public void RefusesForeignChannels(string channel)
    {
        AutoUpdateService.IsAcceptableChannel(channel).Should().BeFalse();
    }

    [Fact]
    public void ThisBuildIsTheOriginChannel()
    {
        AutoUpdateService.UpdateChannel.Should().Be("origin");
    }
}
