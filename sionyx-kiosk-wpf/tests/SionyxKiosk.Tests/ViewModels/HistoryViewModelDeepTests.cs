using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

/// <summary>
/// Deep coverage for HistoryViewModel: filter, sort, search, totals.
/// </summary>
public class HistoryViewModelDeepTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;

    public HistoryViewModelDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.SetDefaultSuccess();
    }

    public void Dispose() => _firebase.Dispose();

    private HistoryViewModel CreateVm()
    {
        var purchaseService = new PurchaseService(_firebase);
        return new HistoryViewModel(purchaseService, "user-123");
    }

    // ==================== INITIAL STATE ====================

    [Fact]
    public void InitialState_ShouldHaveDefaults()
    {
        var vm = CreateVm();
        vm.IsLoading.Should().BeFalse();
        vm.ErrorMessage.Should().BeEmpty();
        vm.TotalSpent.Should().Be(0);
        vm.TotalPurchases.Should().Be(0);
        vm.SearchText.Should().BeEmpty();
        vm.SelectedStatus.Should().Be("הכל");
        vm.SortNewestFirst.Should().BeTrue();
    }

    [Fact]
    public void StatusOptions_ShouldContainExpectedValues()
    {
        var vm = CreateVm();
        vm.StatusOptions.Should().Contain("הכל");
        vm.StatusOptions.Should().Contain("הושלם");
        vm.StatusOptions.Should().Contain("ממתין");
        vm.StatusOptions.Should().Contain("נכשל");
        vm.StatusOptions.Should().HaveCount(4);
    }

    [Fact]
    public void FilteredPurchases_ShouldNotBeNull()
    {
        var vm = CreateVm();
        vm.FilteredPurchases.Should().NotBeNull();
    }

    // ==================== TOGGLE SORT ====================

    [Fact]
    public void ToggleSortCommand_ShouldFlipSortDirection()
    {
        var vm = CreateVm();
        vm.SortNewestFirst.Should().BeTrue();

        vm.ToggleSortCommand.Execute(null);
        vm.SortNewestFirst.Should().BeFalse();

        vm.ToggleSortCommand.Execute(null);
        vm.SortNewestFirst.Should().BeTrue();
    }

    [Fact]
    public void ToggleSortCommand_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.ToggleSortCommand.Execute(null);
        changed.Should().Contain("SortNewestFirst");
    }

    // ==================== LOAD HISTORY ====================

    [Fact]
    public async Task LoadHistoryCommand_WhenServiceFails_ShouldSetError()
    {
        _handler.WhenError("purchases");
        var vm = CreateVm();

        await vm.LoadHistoryCommand.ExecuteAsync(null);

        vm.ErrorMessage.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public async Task LoadHistoryCommand_WithPurchases_ShouldCalculateTotals()
    {
        _handler.When("purchases", new
        {
            p1 = new { userId = "user-123", packageId = "pkg1", packageName = "Basic", amount = 29.90, status = "completed", createdAt = "2025-01-15", updatedAt = "2025-01-15" },
            p2 = new { userId = "user-123", packageId = "pkg2", packageName = "Pro", amount = 49.90, status = "completed", createdAt = "2025-02-01", updatedAt = "2025-02-01" },
            p3 = new { userId = "user-123", packageId = "pkg3", packageName = "Trial", amount = 9.90, status = "pending", createdAt = "2025-03-01", updatedAt = "2025-03-01" },
        });

        var vm = CreateVm();
        await vm.LoadHistoryCommand.ExecuteAsync(null);

        vm.TotalPurchases.Should().Be(3);
        vm.TotalSpent.Should().BeApproximately(79.80, 0.01); // Only completed
    }

    [Fact]
    public async Task LoadHistoryCommand_ShouldSetIsLoading()
    {
        _handler.WhenRaw("purchases", "null");
        var vm = CreateVm();

        var loadingStates = new List<bool>();
        vm.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == "IsLoading")
                loadingStates.Add(vm.IsLoading);
        };

        await vm.LoadHistoryCommand.ExecuteAsync(null);

        loadingStates.Should().Contain(true);
        loadingStates.Should().Contain(false);
    }

    // ==================== SEARCH AND FILTER ====================

    [Fact]
    public void SearchText_Change_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.SearchText = "test search";
        changed.Should().Contain("SearchText");
    }

    [Fact]
    public void SelectedStatus_Change_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.SelectedStatus = "הושלם";
        changed.Should().Contain("SelectedStatus");
    }

    [Fact]
    public void TotalSpent_Change_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.TotalSpent = 100.50;
        changed.Should().Contain("TotalSpent");
    }

    [Fact]
    public void TotalPurchases_Change_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.TotalPurchases = 5;
        changed.Should().Contain("TotalPurchases");
    }

    [Fact]
    public async Task LoadHistoryCommand_EmptyResult_ShouldShowZeroTotals()
    {
        _handler.WhenRaw("purchases", "null");
        var vm = CreateVm();

        await vm.LoadHistoryCommand.ExecuteAsync(null);

        vm.TotalPurchases.Should().Be(0);
        vm.TotalSpent.Should().Be(0);
    }
}
