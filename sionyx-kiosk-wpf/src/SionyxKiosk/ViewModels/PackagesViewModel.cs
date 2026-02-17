using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>Packages page ViewModel: list packages, purchase flow.</summary>
public partial class PackagesViewModel : ObservableObject
{
    private readonly PackageService _packageService;
    private readonly PurchaseService _purchaseService;
    private readonly string _userId;

    [ObservableProperty] private ObservableCollection<Package> _packages = new();
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private string _errorMessage = "";
    [ObservableProperty] private Package? _selectedPackage;

    /// <summary>Show empty state only when NOT loading and packages list is empty.</summary>
    public bool ShowEmptyState => !IsLoading && Packages.Count == 0;

    partial void OnIsLoadingChanged(bool value)
    {
        OnPropertyChanged(nameof(ShowEmptyState));
    }

    partial void OnPackagesChanged(ObservableCollection<Package> value)
    {
        OnPropertyChanged(nameof(ShowEmptyState));
    }

    public event Action<Package>? PurchaseRequested;

    public PackagesViewModel(PackageService packageService, PurchaseService purchaseService, string userId)
    {
        _packageService = packageService;
        _purchaseService = purchaseService;
        _userId = userId;
    }

    [RelayCommand]
    private async Task LoadPackagesAsync()
    {
        IsLoading = true;
        ErrorMessage = "";

        var result = await _packageService.GetAllPackagesAsync();
        IsLoading = false;

        if (result.IsSuccess && result.Data is List<Package> packages)
        {
            Packages = new ObservableCollection<Package>(packages);
        }
        else
        {
            ErrorMessage = result.Error ?? "שגיאה בטעינת חבילות";
        }
    }

    [RelayCommand]
    private void SelectPackage(Package package)
    {
        SelectedPackage = package;
        PurchaseRequested?.Invoke(package);
    }
}
