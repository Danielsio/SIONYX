using System.Windows.Controls;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Pages;

public partial class HelpPage : Page
{
    public HelpPage(HelpViewModel viewModel)
    {
        DataContext = viewModel;
        InitializeComponent();

        Loaded += async (_, _) => await viewModel.LoadContactCommand.ExecuteAsync(null);
    }
}
