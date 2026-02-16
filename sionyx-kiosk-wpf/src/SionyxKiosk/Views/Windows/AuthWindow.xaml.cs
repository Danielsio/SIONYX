using System.Globalization;
using System.Windows;
using System.Windows.Data;
using System.Windows.Input;
using System.Windows.Media.Animation;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Windows;

public partial class AuthWindow : Window
{
    private bool _allowClose;
    private bool _isLoginMode = true;
    private readonly AuthViewModel _vm;

    public AuthWindow(AuthViewModel viewModel)
    {
        _vm = viewModel;
        DataContext = viewModel;
        Resources["StringToVis"] = new Views.Controls.StringToVisibilityConverter();
        Resources["InverseBool"] = new InverseBoolConverter();
        InitializeComponent();

        // WPF PasswordBox doesn't support binding — wire manually.
        LoginPasswordInput.PasswordChanged += (_, _) => viewModel.Password = LoginPasswordInput.Password;
        RegPasswordInput.PasswordChanged += (_, _) => viewModel.Password = RegPasswordInput.Password;

        // Enter key submits the form
        LoginPasswordInput.KeyDown += OnLoginKeyDown;
        LoginPhoneInput.KeyDown += OnLoginKeyDown;
        RegPasswordInput.KeyDown += OnRegisterKeyDown;

        Loaded += (_, _) => LoginPhoneInput.Focus();
    }

    public void AllowClose() => _allowClose = true;

    // ── Toggle animations ──

    private void ToggleToRegister_Click(object sender, RoutedEventArgs e)
    {
        if (!_isLoginMode) return;
        _isLoginMode = false;
        _vm.IsLoginMode = false;
        _vm.ErrorMessage = "";

        // Sync password to register box
        RegPasswordInput.Password = LoginPasswordInput.Password;

        RegisterPanel.IsHitTestVisible = true;
        LoginPanel.IsHitTestVisible = false;

        var sb = (Storyboard)FindResource("SlideToRegister");
        sb.Begin(this);

        BrandSubtitle.Text = "הצטרף אלינו היום";
        RegPhoneInput.Focus();
    }

    private void ToggleToLogin_Click(object sender, RoutedEventArgs e)
    {
        if (_isLoginMode) return;
        _isLoginMode = true;
        _vm.IsLoginMode = true;
        _vm.ErrorMessage = "";

        // Sync password to login box
        LoginPasswordInput.Password = RegPasswordInput.Password;

        LoginPanel.IsHitTestVisible = true;
        RegisterPanel.IsHitTestVisible = false;

        var sb = (Storyboard)FindResource("SlideToLogin");
        sb.Begin(this);

        BrandSubtitle.Text = "ניהול מחשבים חכם";
        LoginPhoneInput.Focus();
    }

    // ── Enter key to submit ──

    private void OnLoginKeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter && _vm.LoginCommand.CanExecute(null))
        {
            _vm.LoginCommand.Execute(null);
            e.Handled = true;
        }
    }

    private void OnRegisterKeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter && _vm.RegisterCommand.CanExecute(null))
        {
            _vm.RegisterCommand.Execute(null);
            e.Handled = true;
        }
    }

    // ── Window chrome ──

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
