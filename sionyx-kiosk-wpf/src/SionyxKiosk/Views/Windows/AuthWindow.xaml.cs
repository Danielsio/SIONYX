using System.Globalization;
using System.Windows;
using System.Windows.Data;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Windows;

public partial class AuthWindow : Window
{
    public AuthWindow(AuthViewModel viewModel)
    {
        DataContext = viewModel;
        Resources["StringToVis"] = new Views.Controls.StringToVisibilityConverter();
        Resources["InverseBool"] = new InverseBoolConverter();
        InitializeComponent();

        viewModel.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(AuthViewModel.IsLoginMode))
            {
                var isLogin = viewModel.IsLoginMode;
                RegisterFields.Visibility = isLogin ? Visibility.Collapsed : Visibility.Visible;
                SubtitleText.Text = isLogin ? "התחבר לחשבון שלך" : "צור חשבון חדש";
                ActionButton.Content = isLogin ? "התחבר" : "הירשם";
                ActionButton.Command = isLogin ? viewModel.LoginCommand : viewModel.RegisterCommand;
                ToggleButton.Content = isLogin ? "אין לך חשבון? הירשם" : "יש לך חשבון? התחבר";
            }
        };
    }
}

public class InverseBoolConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        => value is bool b ? !b : value;
    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => value is bool b ? !b : value;
}
