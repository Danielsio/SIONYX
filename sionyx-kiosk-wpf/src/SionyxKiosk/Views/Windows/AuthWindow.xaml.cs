using System.Globalization;
using System.Windows;
using System.Windows.Data;
using System.Windows.Input;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Windows;

public partial class AuthWindow : Window
{
    private bool _allowClose;

    public AuthWindow(AuthViewModel viewModel)
    {
        DataContext = viewModel;
        Resources["StringToVis"] = new Views.Controls.StringToVisibilityConverter();
        Resources["InverseBool"] = new InverseBoolConverter();
        InitializeComponent();

        // WPF PasswordBox doesn't support binding for security.
        // Wire it manually via PasswordChanged event.
        PasswordInput.PasswordChanged += (_, _) => viewModel.Password = PasswordInput.Password;

        viewModel.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(AuthViewModel.IsLoginMode))
            {
                var isLogin = viewModel.IsLoginMode;
                RegisterFields.Visibility = isLogin ? Visibility.Collapsed : Visibility.Visible;
                ForgotPasswordButton.Visibility = isLogin ? Visibility.Visible : Visibility.Collapsed;
                SubtitleText.Text = isLogin ? "התחבר לחשבון שלך" : "צור חשבון חדש";
                ActionButton.Content = isLogin ? "התחבר" : "הירשם";
                ActionButton.Command = isLogin ? viewModel.LoginCommand : viewModel.RegisterCommand;
                ToggleButton.Content = isLogin ? "אין לך חשבון? הירשם" : "יש לך חשבון? התחבר";
            }
        };
    }

    /// <summary>Allow the window to close (called when transitioning to MainWindow).</summary>
    public void AllowClose() => _allowClose = true;

    protected override void OnClosing(System.ComponentModel.CancelEventArgs e)
    {
        if (!_allowClose)
        {
            e.Cancel = true;
            return;
        }
        base.OnClosing(e);
    }

    protected override void OnKeyDown(KeyEventArgs e)
    {
        if (e.Key == Key.Escape || e.Key == Key.System)
        {
            e.Handled = true;
            return;
        }
        base.OnKeyDown(e);
    }
}

public class InverseBoolConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        => value is bool b ? !b : value;
    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => value is bool b ? !b : value;
}
