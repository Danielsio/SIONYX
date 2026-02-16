using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class PurchaseServiceTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly PurchaseService _service;

    public PurchaseServiceTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new PurchaseService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public async Task CreatePendingPurchaseAsync_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();

        var package = new Package
        {
            Id = "pkg1",
            Name = "Basic",
            Price = 29.90,
            Minutes = 60,
            Prints = 10,
            ValidityDays = 30,
        };

        var result = await _service.CreatePendingPurchaseAsync("user-123", package);
        result.IsSuccess.Should().BeTrue();
        result.Data.Should().NotBeNull();
    }

    [Fact]
    public async Task CreatePendingPurchaseAsync_WhenDbFails_ShouldReturnError()
    {
        _handler.WhenError("purchases/");

        var package = new Package { Id = "pkg1", Name = "Basic", Price = 29.90 };

        var result = await _service.CreatePendingPurchaseAsync("user-123", package);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetPurchaseStatusAsync_WhenExists_ShouldReturnData()
    {
        _handler.When("purchases/purchase-123.json", new
        {
            userId = "user-123",
            status = "completed",
            amount = 29.90,
        });

        var result = await _service.GetPurchaseStatusAsync("purchase-123");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetPurchaseStatusAsync_WhenNotFound_ShouldReturnError()
    {
        _handler.WhenError("purchases/nonexistent.json");

        var result = await _service.GetPurchaseStatusAsync("nonexistent");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetUserPurchaseHistoryAsync_WithPurchases_ShouldReturnFiltered()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", packageId = "pkg1", packageName = "Basic", minutes = 60, prints = 10, printBudget = 10.0, validityDays = 30, amount = 29.90, status = "completed", createdAt = "2026-01-15T10:00:00", updatedAt = "2026-01-15T10:00:00" },
            p2 = new { userId = "other-user", packageId = "pkg1", packageName = "Basic", minutes = 60, prints = 10, printBudget = 10.0, validityDays = 30, amount = 29.90, status = "completed", createdAt = "2026-01-16T10:00:00", updatedAt = "2026-01-16T10:00:00" },
            p3 = new { userId = "user-123", packageId = "pkg2", packageName = "Premium", minutes = 120, prints = 20, printBudget = 20.0, validityDays = 30, amount = 49.90, status = "pending", createdAt = "2026-02-01T10:00:00", updatedAt = "2026-02-01T10:00:00" },
        });

        var result = await _service.GetUserPurchaseHistoryAsync("user-123");
        result.IsSuccess.Should().BeTrue();
        var purchases = (List<Purchase>)result.Data!;
        purchases.Count.Should().Be(2);
        purchases.Should().OnlyContain(p => p.UserId == "user-123");
    }

    [Fact]
    public async Task GetUserPurchaseHistoryAsync_ShouldSortNewestFirst()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", packageName = "Old", status = "completed", createdAt = "2026-01-01T10:00:00", updatedAt = "2026-01-01T10:00:00" },
            p2 = new { userId = "user-123", packageName = "New", status = "completed", createdAt = "2026-02-01T10:00:00", updatedAt = "2026-02-01T10:00:00" },
        });

        var result = await _service.GetUserPurchaseHistoryAsync("user-123");
        var purchases = (List<Purchase>)result.Data!;
        purchases.First().PackageName.Should().Be("New");
        purchases.Last().PackageName.Should().Be("Old");
    }

    [Fact]
    public async Task GetUserPurchaseHistoryAsync_WhenEmpty_ShouldReturnEmpty()
    {
        _handler.WhenRaw("purchases.json", "null");

        var result = await _service.GetUserPurchaseHistoryAsync("user-123");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetUserPurchaseHistoryAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("purchases.json");

        var result = await _service.GetUserPurchaseHistoryAsync("user-123");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetPurchaseStatisticsAsync_ShouldCalculateStats()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", amount = 29.90, status = "completed", createdAt = "2026-01-01", updatedAt = "2026-01-01" },
            p2 = new { userId = "user-123", amount = 49.90, status = "completed", createdAt = "2026-01-15", updatedAt = "2026-01-15" },
            p3 = new { userId = "user-123", amount = 39.90, status = "pending", createdAt = "2026-02-01", updatedAt = "2026-02-01" },
            p4 = new { userId = "user-123", amount = 19.90, status = "failed", createdAt = "2026-02-10", updatedAt = "2026-02-10" },
        });

        var result = await _service.GetPurchaseStatisticsAsync("user-123");
        result.IsSuccess.Should().BeTrue();

        var stats = result.Data!;
        var type = stats.GetType();
        ((double)type.GetProperty("totalSpent")!.GetValue(stats)!).Should().BeApproximately(79.80, 0.01);
        ((int)type.GetProperty("completedPurchases")!.GetValue(stats)!).Should().Be(2);
        ((int)type.GetProperty("pendingPurchases")!.GetValue(stats)!).Should().Be(1);
        ((int)type.GetProperty("failedPurchases")!.GetValue(stats)!).Should().Be(1);
        ((int)type.GetProperty("totalPurchases")!.GetValue(stats)!).Should().Be(4);
    }
}
