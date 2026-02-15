using System.Windows.Controls;
using SionyxKiosk.ViewModels;
using SionyxKiosk.Views.Windows;

namespace SionyxKiosk.Views.Pages;

public partial class HomePage : Page
{
    public HomePage(HomeViewModel viewModel)
    {
        DataContext = viewModel;
        Resources["StringToVis"] = new Views.Controls.StringToVisibilityConverter();
        Resources["InverseBool"] = new InverseBoolConverter();
        InitializeComponent();
    }
}
