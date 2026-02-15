using System.Windows;
using SionyxKiosk.ViewModels;
using SionyxKiosk.Views.Pages;

namespace SionyxKiosk.Views.Windows;

public partial class MainWindow : Window
{
    private readonly MainViewModel _vm;
    private readonly IServiceProvider _services;

    public MainWindow(MainViewModel viewModel, IServiceProvider services)
    {
        _vm = viewModel;
        _services = services;
        DataContext = viewModel;
        InitializeComponent();

        _vm.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(MainViewModel.CurrentPage))
                NavigateToPage(_vm.CurrentPage);
        };

        // Navigate to home on startup
        NavigateToPage("Home");
    }

    private void NavigateToPage(string page)
    {
        object? pageInstance = page switch
        {
            "Home" => _services.GetService(typeof(HomePage)),
            "Packages" => _services.GetService(typeof(PackagesPage)),
            "History" => _services.GetService(typeof(HistoryPage)),
            "Help" => _services.GetService(typeof(HelpPage)),
            _ => _services.GetService(typeof(HomePage))
        };

        if (pageInstance is System.Windows.Controls.Page p)
            ContentFrame.Navigate(p);
    }
}
