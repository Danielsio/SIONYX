using System.Text.Json;
using Serilog;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;
using SionyxKiosk.Views.Dialogs;

namespace SionyxKiosk.Services;

public class PaymentDialogFactory : IPaymentDialogFactory
{
    private static readonly ILogger Logger = Log.ForContext<PaymentDialogFactory>();

    private readonly PurchaseService _purchaseService;
    private readonly OrganizationMetadataService _metadataService;
    private readonly FirebaseClient _firebase;
    private readonly AuthService _authService;

    public PaymentDialogFactory(
        PurchaseService purchaseService,
        OrganizationMetadataService metadataService,
        FirebaseClient firebase,
        AuthService authService)
    {
        _purchaseService = purchaseService;
        _metadataService = metadataService;
        _firebase = firebase;
        _authService = authService;
    }

    public (bool Succeeded, object? Dialog) CreateAndShow(Package package, System.Windows.Window? owner = null)
    {
        var userId = _authService.CurrentUser?.Uid ?? "";
        var dialog = new PaymentDialog(_purchaseService, _metadataService, _firebase, userId, package);
        dialog.Owner = owner;
        dialog.ShowDialog();
        return (dialog.PaymentSucceeded, dialog);
    }

    public Task<bool> HasSavedCardAsync() => _firebase.HasSavedCardAsync();

    public async Task<bool> ChargeWithSavedCardAsync(Package package)
    {
        var (ok, purchaseId, error) = await _firebase.ChargeSavedCardAsync(package.Id);
        if (!ok || string.IsNullOrEmpty(purchaseId))
        {
            Logger.Warning("Saved-card charge failed for {Package}: {Error}", package.Name, error);
            return false;
        }

        // The gateway callback credits asynchronously; wait for the purchase to settle.
        for (int i = 0; i < 15; i++)
        {
            await Task.Delay(TimeSpan.FromSeconds(2));
            var result = await _firebase.DbGetAsync($"purchases/{purchaseId}");
            if (result.Success && result.Data is JsonElement data && data.ValueKind == JsonValueKind.Object)
            {
                var status = data.TryGetProperty("status", out var s) ? s.GetString() : null;
                if (status is "completed" or "approved")
                {
                    Logger.Information("Saved-card purchase {Id} confirmed", purchaseId);
                    return true;
                }
                if (status is "failed")
                {
                    Logger.Warning("Saved-card purchase {Id} reported failed", purchaseId);
                    return false;
                }
            }
        }

        Logger.Warning("Saved-card purchase {Id} did not confirm in time", purchaseId);
        return false;
    }
}
