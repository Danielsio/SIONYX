using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>History page ViewModel: purchase history, statistics.</summary>
public partial class HistoryViewModel : ObservableObject
{
    private readonly PurchaseService _purchaseService;
    private readonly string _userId;

    [ObservableProperty] private ObservableCollection<Purchase> _purchases = new();
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private string _errorMessage = "";
    [ObservableProperty] private double _totalSpent;
    [ObservableProperty] private int _totalPurchases;

    public HistoryViewModel(PurchaseService purchaseService, string userId)
    {
        _purchaseService = purchaseService;
        _userId = userId;
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
            Purchases = new ObservableCollection<Purchase>(purchases);
            TotalPurchases = purchases.Count;
            TotalSpent = purchases.Where(p => p.Status == "completed").Sum(p => p.Amount);
        }
        else
        {
            ErrorMessage = result.Error ?? "שגיאה בטעינת היסטוריה";
        }
    }
}
