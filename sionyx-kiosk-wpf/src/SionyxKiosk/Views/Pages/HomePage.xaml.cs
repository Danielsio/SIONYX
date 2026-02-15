using System.Windows.Controls;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Pages;

public partial class HomePage : Page
{
    public HomePage(HomeViewModel viewModel)
    {
        DataContext = viewModel;
        Resources["StringToVis"] = new Views.Controls.StringToVisibilityConverter();
        InitializeComponent();
    }
}
