using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Windows.Data;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>History page ViewModel: purchase history with search, filter, sort.</summary>
public partial class HistoryViewModel : ObservableObject
{
    private readonly PurchaseService _purchaseService;
    private readonly string _userId;

    private ObservableCollection<Purchase> _allPurchases = new();

    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private string _errorMessage = "";
    [ObservableProperty] private double _totalSpent;
    [ObservableProperty] private int _totalPurchases;
    [ObservableProperty] private string _searchText = "";
    [ObservableProperty] private string _selectedStatus = "הכל";
    [ObservableProperty] private bool _sortNewestFirst = true;

    /// <summary>Filtered and sorted view of purchases, bound to the UI.</summary>
    public ICollectionView FilteredPurchases { get; }

    /// <summary>Status options for the filter dropdown.</summary>
    public List<string> StatusOptions { get; } = new() { "הכל", "הושלם", "ממתין", "נכשל" };

    public HistoryViewModel(PurchaseService purchaseService, string userId)
    {
        _purchaseService = purchaseService;
        _userId = userId;

        FilteredPurchases = CollectionViewSource.GetDefaultView(_allPurchases);
        FilteredPurchases.Filter = ApplyFilter;
        FilteredPurchases.SortDescriptions.Add(
            new SortDescription(nameof(Purchase.CreatedAt), ListSortDirection.Descending));
    }

    partial void OnSearchTextChanged(string value) => FilteredPurchases.Refresh();
    partial void OnSelectedStatusChanged(string value) => FilteredPurchases.Refresh();

    [RelayCommand]
    private void ToggleSort()
    {
        SortNewestFirst = !SortNewestFirst;
        FilteredPurchases.SortDescriptions.Clear();
        FilteredPurchases.SortDescriptions.Add(new SortDescription(
            nameof(Purchase.CreatedAt),
            SortNewestFirst ? ListSortDirection.Descending : ListSortDirection.Ascending));
    }

    [RelayCommand]
    private async Task LoadHistoryAsync()
    {
        IsLoading = true;
        ErrorMessage = "";

        var result = await _purchaseService.GetUserPurchaseHistoryAsync(_userId);
        IsLoading = false;

        if (result.IsSuccess && result.Data is List<Purchase> purchases)
        {
            _allPurchases.Clear();
            foreach (var p in purchases)
                _allPurchases.Add(p);

            TotalPurchases = purchases.Count;
            TotalSpent = purchases.Where(p => p.Status == "completed").Sum(p => p.Amount);
            FilteredPurchases.Refresh();
        }
        else
        {
            ErrorMessage = result.Error ?? "שגיאה בטעינת היסטוריה";
        }
    }

    private bool ApplyFilter(object obj)
    {
        if (obj is not Purchase purchase) return false;

        // Status filter
        if (SelectedStatus != "הכל")
        {
            var statusLabel = PurchaseStatusExtensions.Parse(purchase.Status).ToHebrewLabel();
            if (statusLabel != SelectedStatus) return false;
        }

        // Search filter
        if (!string.IsNullOrWhiteSpace(SearchText))
        {
            var term = SearchText.Trim();
            if (!purchase.PackageName.Contains(term, StringComparison.OrdinalIgnoreCase) &&
                !purchase.Amount.ToString("F2").Contains(term) &&
                !purchase.CreatedAt.Contains(term))
                return false;
        }

        return true;
    }
}
