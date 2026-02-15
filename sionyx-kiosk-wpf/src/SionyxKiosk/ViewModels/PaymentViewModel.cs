using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>Payment dialog ViewModel: manages WebView2 payment flow.</summary>
public partial class PaymentViewModel : ObservableObject
{
    private readonly PurchaseService _purchaseService;
    private readonly string _userId;

    [ObservableProperty] private Package? _package;
    [ObservableProperty] private string _purchaseId = "";
    [ObservableProperty] private bool _isProcessing;
    [ObservableProperty] private string _status = "pending";  // pending, success, failed
    [ObservableProperty] private string _errorMessage = "";

    public event Action<bool>? PaymentCompleted; // true = success

    public PaymentViewModel(PurchaseService purchaseService, string userId)
    {
        _purchaseService = purchaseService;
        _userId = userId;
    }

    [RelayCommand]
    private async Task InitPaymentAsync(Package package)
    {
        Package = package;
        IsProcessing = true;
        Status = "pending";

        var result = await _purchaseService.CreatePendingPurchaseAsync(_userId, package);
        if (result.IsSuccess && result.Data is { } data)
        {
            var type = data.GetType();
            PurchaseId = type.GetProperty("purchaseId")?.GetValue(data)?.ToString() ?? "";
        }
        else
        {
            ErrorMessage = result.Error ?? "שגיאה ביצירת רכישה";
            Status = "failed";
            IsProcessing = false;
        }
    }

    [RelayCommand]
    private void CompletePayment(bool success)
    {
        Status = success ? "success" : "failed";
        IsProcessing = false;
        PaymentCompleted?.Invoke(success);
    }
}
