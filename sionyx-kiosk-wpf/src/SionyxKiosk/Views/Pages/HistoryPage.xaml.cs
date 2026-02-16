using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Pages;

public partial class HistoryPage : Page
{
    public HistoryPage(HistoryViewModel viewModel)
    {
        DataContext = viewModel;
        // SortLabelConverter must be added before InitializeComponent because it's
        // referenced in XAML bindings.  BoolToVis is defined in XAML — do NOT add it
        // here or InitializeComponent will throw a duplicate-key exception.
        Resources["SortLabelConverter"] = new SortLabelConverter();
        InitializeComponent();

        Loaded += async (_, _) => await viewModel.LoadHistoryCommand.ExecuteAsync(null);

        // Show/hide empty state based on filtered count
        viewModel.FilteredPurchases.CollectionChanged += (_, _) =>
        {
            var count = viewModel.FilteredPurchases.Cast<object>().Count();
            EmptyPanel.Visibility = count == 0 && !viewModel.IsLoading
                ? Visibility.Visible
                : Visibility.Collapsed;
        };
    }
}

/// <summary>Converts SortNewestFirst bool to Hebrew label.</summary>
public class SortLabelConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        => value is true ? "חדש → ישן" : "ישן → חדש";

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotSupportedException();
}
