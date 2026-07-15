using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// The kiosk shows a branded background only for a genuinely usable http(s)
/// URL that the org enabled — anything else falls back to the built-in look, so
/// a bad value can never leave the login screen broken.
/// </summary>
public class KioskBrandingTests
{
    [Theory]
    [InlineData("https://cdn.example.com/bg.jpg")]
    [InlineData("http://example.com/a.png")]
    public void EnabledWithAValidUrl_ShowsBackground(string url)
    {
        KioskSettings.ShouldShowBackground(true, url).Should().BeTrue();
    }

    [Fact]
    public void DisabledNeverShows_EvenWithAValidUrl()
    {
        KioskSettings.ShouldShowBackground(false, "https://cdn.example.com/bg.jpg")
            .Should().BeFalse();
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    [InlineData("not a url")]
    [InlineData("/relative/path.jpg")]
    [InlineData("ftp://example.com/bg.jpg")]
    [InlineData("file:///c:/evil.png")]
    [InlineData("javascript:alert(1)")]
    public void EnabledWithABadUrl_FallsBackToBuiltIn(string? url)
    {
        KioskSettings.ShouldShowBackground(true, url).Should().BeFalse();
    }

    [Fact]
    public void DefaultsHaveNoBackground()
    {
        KioskSettings.Defaults.BackgroundEnabled.Should().BeFalse();
        KioskSettings.Defaults.HasUsableBackground.Should().BeFalse();
    }

    [Fact]
    public void HasUsableBackground_MirrorsTheStaticCheck()
    {
        var on = new KioskSettings { BackgroundEnabled = true, BackgroundUrl = "https://x.example/y.png" };
        on.HasUsableBackground.Should().BeTrue();

        var bad = new KioskSettings { BackgroundEnabled = true, BackgroundUrl = "nope" };
        bad.HasUsableBackground.Should().BeFalse();
    }
}
