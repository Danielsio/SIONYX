using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;
namespace SionyxKiosk.Views.Pages;

public partial class PackagesPage : Page
{
    private readonly IPaymentDialogFactory _dialogFactory;
    private readonly AuthService _auth;

    public static readonly DependencyProperty CardWidthProperty =
        DependencyProperty.Register(nameof(CardWidth), typeof(double), typeof(PackagesPage),
            new PropertyMetadata(320.0));

    public double CardWidth
    {
        get => (double)GetValue(CardWidthProperty);
        set => SetValue(CardWidthProperty, value);
    }

    public PackagesPage(PackagesViewModel viewModel, IPaymentDialogFactory dialogFactory, AuthService auth)
    {
        _dialogFactory = dialogFactory;
        _auth = auth;
        DataContext = viewModel;
        Resources["BoolToVis"] = new BooleanToVisibilityConverter();
        Resources["ZeroToVis"] = new ZeroToVisibilityConverter();
        Resources["NonZeroToVis"] = new NonZeroToVisibilityConverter();
        InitializeComponent();

        Loaded += async (_, _) => await viewModel.LoadPackagesCommand.ExecuteAsync(null);
        Loaded += (_, _) => UpdateCardWidth();
        SizeChanged += (_, _) => UpdateCardWidth();

        viewModel.PurchaseRequested += OnPurchaseRequested;
    }

    private void UpdateCardWidth()
    {
        var available = ActualWidth;
        if (available <= 0) return;

        const double minWidth = 280;
        const double maxWidth = 420;
        const double itemMargin = 24;
        const int maxColumns = 4;

        int columns = Math.Max(1, Math.Min(maxColumns, (int)(available / (minWidth + itemMargin))));
        double cardWidth = (available / columns) - itemMargin;
        CardWidth = Math.Clamp(cardWidth, minWidth, maxWidth);
    }

    private async void OnPurchaseRequested(Package package)
    {
        var (succeeded, _) = _dialogFactory.CreateAndShow(package, Window.GetWindow(this));

        if (succeeded)
        {
            await _auth.RefreshCurrentUserAsync();
            if (Window.GetWindow(this) is Windows.MainWindow mainWindow)
                mainWindow.NavigateHome();
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

public class NonZeroToVisibilityConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is int i) return i > 0 ? Visibility.Visible : Visibility.Collapsed;
        if (value is double d) return d > 0 ? Visibility.Visible : Visibility.Collapsed;
        return Visibility.Collapsed;
    }
    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotSupportedException();
}
