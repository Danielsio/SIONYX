using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;
using SionyxKiosk.Views.Dialogs;

namespace SionyxKiosk.Views.Pages;

public partial class PackagesPage : Page
{
    private readonly IPaymentDialogFactory _dialogFactory;

    public PackagesPage(PackagesViewModel viewModel, IPaymentDialogFactory dialogFactory)
    {
        _dialogFactory = dialogFactory;
        DataContext = viewModel;
        Resources["BoolToVis"] = new BooleanToVisibilityConverter();
        Resources["ZeroToVis"] = new ZeroToVisibilityConverter();
        InitializeComponent();

        Loaded += async (_, _) => await viewModel.LoadPackagesCommand.ExecuteAsync(null);

        viewModel.PurchaseRequested += OnPurchaseRequested;
    }

    private void OnPurchaseRequested(Package package)
    {
        var (succeeded, _) = _dialogFactory.CreateAndShow(package, Window.GetWindow(this));

        if (succeeded)
        {
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
