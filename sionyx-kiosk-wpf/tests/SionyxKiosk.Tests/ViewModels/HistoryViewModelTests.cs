using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class HistoryViewModelTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly HistoryViewModel _vm;

    public HistoryViewModelTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        var purchaseService = new PurchaseService(_firebase);
        _vm = new HistoryViewModel(purchaseService, "user-123");
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public void InitialState_ShouldBeEmpty()
    {
        _vm.FilteredPurchases.Cast<object>().Should().BeEmpty();
        _vm.IsLoading.Should().BeFalse();
        _vm.ErrorMessage.Should().BeEmpty();
        _vm.TotalSpent.Should().Be(0);
        _vm.TotalPurchases.Should().Be(0);
    }

    [Fact]
    public async Task LoadHistoryCommand_WithPurchases_ShouldPopulate()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", packageName = "Basic", amount = 29.90, status = "completed", createdAt = "2026-01-01", updatedAt = "2026-01-01" },
            p2 = new { userId = "user-123", packageName = "Premium", amount = 49.90, status = "completed", createdAt = "2026-01-15", updatedAt = "2026-01-15" },
            p3 = new { userId = "user-123", packageName = "Basic", amount = 29.90, status = "pending", createdAt = "2026-02-01", updatedAt = "2026-02-01" },
        });

        await _vm.LoadHistoryCommand.ExecuteAsync(null);

        _vm.FilteredPurchases.Cast<object>().Count().Should().Be(3);
        _vm.TotalPurchases.Should().Be(3);
        _vm.TotalSpent.Should().BeApproximately(79.80, 0.01); // Only completed
        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public async Task LoadHistoryCommand_WhenFails_ShouldSetError()
    {
        _handler.WhenError("purchases.json");

        await _vm.LoadHistoryCommand.ExecuteAsync(null);

        _vm.ErrorMessage.Should().NotBeEmpty();
        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public async Task LoadHistoryCommand_WhenEmpty_ShouldNotFail()
    {
        _handler.WhenRaw("purchases.json", "null");

        await _vm.LoadHistoryCommand.ExecuteAsync(null);

        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public void PropertyChanged_ShouldFire()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        _vm.IsLoading = true;
        _vm.ErrorMessage = "test error";
        _vm.TotalSpent = 100.0;
        _vm.TotalPurchases = 5;

        changed.Should().Contain("IsLoading");
        changed.Should().Contain("ErrorMessage");
        changed.Should().Contain("TotalSpent");
        changed.Should().Contain("TotalPurchases");
    }
}
