using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;
using SionyxKiosk.Views.Dialogs;

namespace SionyxKiosk.Services;

public class PaymentDialogFactory : IPaymentDialogFactory
{
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
}
