using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Pages;

public partial class PackagesPage : Page
{
    public PackagesPage(PackagesViewModel viewModel)
    {
        DataContext = viewModel;
        Resources["BoolToVis"] = new BooleanToVisibilityConverter();
        Resources["ZeroToVis"] = new ZeroToVisibilityConverter();
        InitializeComponent();

        Loaded += async (_, _) => await viewModel.LoadPackagesCommand.ExecuteAsync(null);
    }
}

public class ZeroToVisibilityConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        => value is int count && count == 0 ? Visibility.Visible : Visibility.Collapsed;
    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotSupportedException();
}
