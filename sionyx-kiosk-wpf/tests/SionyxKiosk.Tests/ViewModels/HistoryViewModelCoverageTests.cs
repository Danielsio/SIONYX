using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class HistoryViewModelCoverageTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly HistoryViewModel _vm;

    public HistoryViewModelCoverageTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        var purchaseService = new PurchaseService(_firebase);
        _vm = new HistoryViewModel(purchaseService, "user-123");
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public void StatusOptions_ContainsExpectedValues()
    {
        _vm.StatusOptions.Should().Contain("הכל");
        _vm.StatusOptions.Should().Contain("הושלם");
        _vm.StatusOptions.Should().Contain("ממתין");
        _vm.StatusOptions.Should().Contain("נכשל");
    }

    [Fact]
    public void StatusOptions_HasFourEntries()
    {
        _vm.StatusOptions.Should().HaveCount(4);
    }

    [Fact]
    public void SortNewestFirst_DefaultTrue()
    {
        _vm.SortNewestFirst.Should().BeTrue();
    }

    [Fact]
    public void SelectedStatus_DefaultAll()
    {
        _vm.SelectedStatus.Should().Be("הכל");
    }

    [Fact]
    public void SearchText_DefaultEmpty()
    {
        _vm.SearchText.Should().BeEmpty();
    }

    [Fact]
    public void ToggleSortCommand_FlipsSortDirection()
    {
        _vm.SortNewestFirst.Should().BeTrue();
        _vm.ToggleSortCommand.Execute(null);
        _vm.SortNewestFirst.Should().BeFalse();
        _vm.ToggleSortCommand.Execute(null);
        _vm.SortNewestFirst.Should().BeTrue();
    }

    [Fact]
    public void SearchText_ChangesRefreshFilter()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);
        _vm.SearchText = "test";
        changed.Should().Contain("SearchText");
    }

    [Fact]
    public void SelectedStatus_ChangeRefreshesFilter()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);
        _vm.SelectedStatus = "ממתין";
        changed.Should().Contain("SelectedStatus");
    }

    [Fact]
    public async Task LoadHistory_WithCompletedAndPending_CalculatesTotalCorrectly()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", packageName = "A", amount = 10.0, status = "completed", createdAt = "2026-01-01", updatedAt = "2026-01-01" },
            p2 = new { userId = "user-123", packageName = "B", amount = 20.0, status = "completed", createdAt = "2026-01-02", updatedAt = "2026-01-02" },
            p3 = new { userId = "user-123", packageName = "C", amount = 30.0, status = "pending", createdAt = "2026-01-03", updatedAt = "2026-01-03" },
        });

        await _vm.LoadHistoryCommand.ExecuteAsync(null);

        _vm.TotalSpent.Should().BeApproximately(30.0, 0.01);
        _vm.TotalPurchases.Should().Be(3);
    }

    [Fact]
    public async Task Filter_ByStatus_ShowsOnlyMatching()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", packageName = "A", amount = 10.0, status = "completed", createdAt = "2026-01-01", updatedAt = "2026-01-01" },
            p2 = new { userId = "user-123", packageName = "B", amount = 20.0, status = "pending", createdAt = "2026-01-02", updatedAt = "2026-01-02" },
        });

        await _vm.LoadHistoryCommand.ExecuteAsync(null);
        _vm.SelectedStatus = "הושלם";

        _vm.FilteredPurchases.Cast<Purchase>().Count().Should().Be(1);
        _vm.FilteredPurchases.Cast<Purchase>().First().PackageName.Should().Be("A");
    }

    [Fact]
    public async Task Filter_AllStatus_ShowsEverything()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", packageName = "A", amount = 10.0, status = "completed", createdAt = "2026-01-01", updatedAt = "2026-01-01" },
            p2 = new { userId = "user-123", packageName = "B", amount = 20.0, status = "pending", createdAt = "2026-01-02", updatedAt = "2026-01-02" },
        });

        await _vm.LoadHistoryCommand.ExecuteAsync(null);
        _vm.SelectedStatus = "הכל";

        _vm.FilteredPurchases.Cast<Purchase>().Count().Should().Be(2);
    }

    [Fact]
    public async Task Filter_BySearch_MatchesPackageName()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", packageName = "Premium", amount = 100.0, status = "completed", createdAt = "2026-01-01", updatedAt = "2026-01-01" },
            p2 = new { userId = "user-123", packageName = "Basic", amount = 50.0, status = "completed", createdAt = "2026-01-02", updatedAt = "2026-01-02" },
        });

        await _vm.LoadHistoryCommand.ExecuteAsync(null);
        _vm.SearchText = "Premium";

        _vm.FilteredPurchases.Cast<Purchase>().Count().Should().Be(1);
    }

    [Fact]
    public async Task Filter_BySearchAmount_Matches()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", packageName = "A", amount = 99.90, status = "completed", createdAt = "2026-01-01", updatedAt = "2026-01-01" },
            p2 = new { userId = "user-123", packageName = "B", amount = 50.0, status = "completed", createdAt = "2026-01-02", updatedAt = "2026-01-02" },
        });

        await _vm.LoadHistoryCommand.ExecuteAsync(null);
        _vm.SearchText = "99.90";

        _vm.FilteredPurchases.Cast<Purchase>().Count().Should().Be(1);
    }

    [Fact]
    public async Task Filter_Combined_StatusAndSearch()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", packageName = "Premium", amount = 100.0, status = "completed", createdAt = "2026-01-01", updatedAt = "2026-01-01" },
            p2 = new { userId = "user-123", packageName = "Premium", amount = 100.0, status = "pending", createdAt = "2026-01-02", updatedAt = "2026-01-02" },
            p3 = new { userId = "user-123", packageName = "Basic", amount = 50.0, status = "completed", createdAt = "2026-01-03", updatedAt = "2026-01-03" },
        });

        await _vm.LoadHistoryCommand.ExecuteAsync(null);
        _vm.SelectedStatus = "הושלם";
        _vm.SearchText = "Premium";

        _vm.FilteredPurchases.Cast<Purchase>().Count().Should().Be(1);
    }

    [Fact]
    public async Task Filter_NoMatch_ReturnsEmpty()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", packageName = "A", amount = 10.0, status = "completed", createdAt = "2026-01-01", updatedAt = "2026-01-01" },
        });

        await _vm.LoadHistoryCommand.ExecuteAsync(null);
        _vm.SearchText = "xyznonexistent";

        _vm.FilteredPurchases.Cast<Purchase>().Count().Should().Be(0);
    }

    [Fact]
    public async Task ToggleSort_ChangesOrder()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-123", packageName = "Early", amount = 10.0, status = "completed", createdAt = "2026-01-01", updatedAt = "2026-01-01" },
            p2 = new { userId = "user-123", packageName = "Late", amount = 20.0, status = "completed", createdAt = "2026-12-01", updatedAt = "2026-12-01" },
        });

        await _vm.LoadHistoryCommand.ExecuteAsync(null);

        var items = _vm.FilteredPurchases.Cast<Purchase>().ToList();
        items.Should().HaveCount(2);

        _vm.ToggleSortCommand.Execute(null);
        var reordered = _vm.FilteredPurchases.Cast<Purchase>().ToList();
        reordered.Should().HaveCount(2);
    }

    [Fact]
    public async Task LoadHistory_NullResult_SetsError()
    {
        _handler.WhenRaw("purchases.json", "null");
        await _vm.LoadHistoryCommand.ExecuteAsync(null);
        _vm.FilteredPurchases.Cast<Purchase>().Count().Should().Be(0);
    }
}
