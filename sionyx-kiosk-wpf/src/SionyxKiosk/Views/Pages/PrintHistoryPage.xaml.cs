using System.Windows.Controls;
using SionyxKiosk.ViewModels;
using SionyxKiosk.Views.Windows;

namespace SionyxKiosk.Views.Pages;

public partial class PrintHistoryPage : Page
{
    public PrintHistoryPage(PrintHistoryViewModel viewModel)
    {
        DataContext = viewModel;
        Resources["InverseBoolToVis"] = new InverseBoolToVisibilityConverter();
        InitializeComponent();
    }
}
