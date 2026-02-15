using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;
using SionyxKiosk.Views.Dialogs;

namespace SionyxKiosk.Views.Pages;

public partial class PackagesPage : Page
{
    private readonly IServiceProvider _services;

    public PackagesPage(PackagesViewModel viewModel, IServiceProvider services)
    {
        _services = services;
        DataContext = viewModel;
        Resources["BoolToVis"] = new BooleanToVisibilityConverter();
        Resources["ZeroToVis"] = new ZeroToVisibilityConverter();
        InitializeComponent();

        Loaded += async (_, _) => await viewModel.LoadPackagesCommand.ExecuteAsync(null);

        viewModel.PurchaseRequested += OnPurchaseRequested;
    }

    private void OnPurchaseRequested(Package package)
    {
        var purchaseService = (PurchaseService)_services.GetService(typeof(PurchaseService))!;
        var metadataService = (OrganizationMetadataService)_services.GetService(typeof(OrganizationMetadataService))!;
        var firebase = (FirebaseClient)_services.GetService(typeof(FirebaseClient))!;
        var auth = (AuthService)_services.GetService(typeof(AuthService))!;
        var userId = auth.CurrentUser?.Uid ?? "";

        var dialog = new PaymentDialog(purchaseService, metadataService, firebase, userId, package);
        dialog.Owner = Window.GetWindow(this);
        dialog.ShowDialog();

        if (dialog.PaymentSucceeded)
        {
            // Payment succeeded — refresh data
            AlertDialog.Show("הצלחה", "התשלום בוצע בהצלחה! הזמן נוסף לחשבונך.", AlertDialog.AlertType.Success);
        }
    }
}

public class ZeroToVisibilityConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        => value is int count && count == 0 ? Visibility.Visible : Visibility.Collapsed;
    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotSupportedException();
}
