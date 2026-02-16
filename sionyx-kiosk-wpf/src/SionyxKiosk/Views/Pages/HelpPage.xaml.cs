using System.Windows.Controls;
using System.Windows.Input;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Pages;

public partial class HelpPage : Page
{
    private readonly HelpViewModel _vm;

    public HelpPage(HelpViewModel viewModel)
    {
        _vm = viewModel;
        DataContext = viewModel;
        InitializeComponent();

        Loaded += async (_, _) => await viewModel.LoadContactCommand.ExecuteAsync(null);
    }

    private void PhoneRow_Click(object sender, MouseButtonEventArgs e)
    {
        if (!string.IsNullOrEmpty(_vm.AdminPhone))
            _vm.CopyToClipboardCommand.Execute(_vm.AdminPhone);
    }

    private void EmailRow_Click(object sender, MouseButtonEventArgs e)
    {
        if (!string.IsNullOrEmpty(_vm.AdminEmail))
            _vm.CopyToClipboardCommand.Execute(_vm.AdminEmail);
    }
}
