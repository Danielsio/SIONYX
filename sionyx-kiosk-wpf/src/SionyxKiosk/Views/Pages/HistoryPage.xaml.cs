using System.Windows.Controls;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Pages;

public partial class HistoryPage : Page
{
    public HistoryPage(HistoryViewModel viewModel)
    {
        DataContext = viewModel;
        Resources["BoolToVis"] = new System.Windows.Controls.BooleanToVisibilityConverter();
        Resources["ZeroToVis"] = new ZeroToVisibilityConverter();
        InitializeComponent();

        Loaded += async (_, _) => await viewModel.LoadHistoryCommand.ExecuteAsync(null);
    }
}
