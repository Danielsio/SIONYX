using System.Windows;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Dialogs;

public partial class PaymentDialog : Window
{
    private readonly PaymentViewModel _vm;

    public PaymentDialog(PaymentViewModel viewModel)
    {
        _vm = viewModel;
        DataContext = viewModel;
        InitializeComponent();

        viewModel.PaymentCompleted += success =>
        {
            DialogResult = success;
            Close();
        };
    }

    private void CloseButton_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
