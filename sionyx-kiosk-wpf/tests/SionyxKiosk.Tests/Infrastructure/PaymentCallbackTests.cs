using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Payment callback resolution (H-4): an unset NedarimCallbackUrl must resolve
/// to empty (gateway's mosad-configured callback), never to the deleted Cloud
/// Function URL — that charged the card but never credited the purchase.
/// </summary>
public class PaymentCallbackTests
{
    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void UnsetCallback_ResolvesToEmpty_NotToADeadEndpoint(string? configured)
    {
        var result = PaymentCallback.Resolve(configured);

        result.Should().BeEmpty();
        result.Should().NotContain("cloudfunctions.net");
    }

    [Theory]
    [InlineData("none")]
    [InlineData("NONE")]
    [InlineData("None")]
    [InlineData("  none  ")]
    public void NoneSentinel_ResolvesToEmpty(string configured)
    {
        PaymentCallback.Resolve(configured).Should().BeEmpty();
    }

    [Fact]
    public void ConfiguredUrl_IsUsedAsIs()
    {
        const string url = "https://sionyx-server.sionyx-server.workers.dev/payments/nedarim-callback?secret=x";
        PaymentCallback.Resolve(url).Should().Be(url);
    }

    [Fact]
    public void ConfiguredUrl_IsTrimmed()
    {
        PaymentCallback.Resolve("  https://example.com/cb  ").Should().Be("https://example.com/cb");
    }
}
