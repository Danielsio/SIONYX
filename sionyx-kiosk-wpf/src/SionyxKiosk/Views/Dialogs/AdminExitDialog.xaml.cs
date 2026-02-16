using System.Windows;

namespace SionyxKiosk.Views.Dialogs;

public partial class AdminExitDialog : Window
{
    public string EnteredPassword => PasswordInput.Password;

    public AdminExitDialog()
    {
        InitializeComponent();
        Loaded += (_, _) => PasswordInput.Focus();
    }

    private void OK_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = true;
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
    }
}
