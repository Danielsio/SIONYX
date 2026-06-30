using System.Net;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>Covers the kiosk's server-mediated saved-card charge path.</summary>
public class FirebaseClientSavedCardTests : IDisposable
{
    private readonly FirebaseClient _client;
    private readonly MockHttpHandler _handler;

    public FirebaseClientSavedCardTests()
    {
        (_client, _handler) = TestFirebaseFactory.Create();
    }

    public void Dispose() => _client.Dispose();

    [Fact]
    public async Task ChargeSavedCardAsync_WhenServerSucceeds_ReturnsPurchaseId()
    {
        _handler.When("payments/charge-saved-card", new { success = true, purchaseId = "purch-123" });

        var (ok, purchaseId, err) = await _client.ChargeSavedCardAsync("pkg-1");

        ok.Should().BeTrue();
        purchaseId.Should().Be("purch-123");
        err.Should().BeNull();
    }

    [Fact]
    public async Task ChargeSavedCardAsync_WhenServerRejects_ReturnsError()
    {
        _handler.WhenError("payments/charge-saved-card", HttpStatusCode.BadRequest);

        var (ok, _, err) = await _client.ChargeSavedCardAsync("pkg-1");

        ok.Should().BeFalse();
        err.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public async Task HasSavedCardAsync_WhenTokenPresent_ReturnsTrue()
    {
        _handler.WhenRaw("savedCard/kevaId.json", "\"keva-abc\"");

        (await _client.HasSavedCardAsync()).Should().BeTrue();
    }

    [Fact]
    public async Task HasSavedCardAsync_WhenAbsent_ReturnsFalse()
    {
        _handler.WhenRaw("savedCard/kevaId.json", "null");

        (await _client.HasSavedCardAsync()).Should().BeFalse();
    }
}
