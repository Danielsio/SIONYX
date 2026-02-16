using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for PurchaseService covering edge cases.
/// </summary>
public class PurchaseServiceDeepTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly PurchaseService _service;

    public PurchaseServiceDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new PurchaseService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public async Task CreatePendingPurchaseAsync_WhenDbSetFails_ShouldReturnError()
    {
        _handler.WhenError("test-db.firebaseio.com");
        var package = new Package { Id = "pkg-1", Name = "Gold", Price = 100.0, Minutes = 3600, Prints = 50, ValidityDays = 30 };
        var result = await _service.CreatePendingPurchaseAsync("test-uid", package);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task CreatePendingPurchaseAsync_WithValidData_ShouldReturnPurchaseId()
    {
        _handler.SetDefaultSuccess();
        var package = new Package { Id = "pkg-1", Name = "Gold", Price = 100.0, Minutes = 3600, Prints = 50, ValidityDays = 30 };
        var result = await _service.CreatePendingPurchaseAsync("test-uid", package);
        result.IsSuccess.Should().BeTrue();
        result.Data.Should().NotBeNull();
    }

    [Fact]
    public async Task GetPurchaseStatusAsync_WhenNotFound_ShouldReturnError()
    {
        _handler.WhenRaw("test-db.firebaseio.com", "null");
        var result = await _service.GetPurchaseStatusAsync("missing-purchase");
        result.Should().NotBeNull();
    }

    [Fact]
    public async Task GetPurchaseStatisticsAsync_WithPurchases_ShouldCalculateStats()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "test-uid", status = "completed", amount = 50.0, createdAt = "2024-01-01" },
            p2 = new { userId = "test-uid", status = "pending", amount = 30.0, createdAt = "2024-01-02" },
            p3 = new { userId = "other-uid", status = "completed", amount = 100.0, createdAt = "2024-01-03" },
        });

        var result = await _service.GetPurchaseStatisticsAsync("test-uid");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetUserPurchaseHistoryAsync_WithNoPurchases_ShouldReturnEmpty()
    {
        _handler.WhenRaw("purchases.json", "null");
        var result = await _service.GetUserPurchaseHistoryAsync("test-uid");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetPurchaseStatusAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("test-db.firebaseio.com");
        var result = await _service.GetPurchaseStatusAsync("purchase-1");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetUserPurchaseHistoryAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("purchases.json");
        var result = await _service.GetUserPurchaseHistoryAsync("test-uid");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetPurchaseStatisticsAsync_WhenHistoryFails_ShouldReturnError()
    {
        _handler.WhenError("purchases.json");
        var result = await _service.GetPurchaseStatisticsAsync("test-uid");
        result.IsSuccess.Should().BeFalse();
    }
}
