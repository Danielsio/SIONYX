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
        Resources["BoolToVis"] = new BooleanToVisibilityConverter();
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
