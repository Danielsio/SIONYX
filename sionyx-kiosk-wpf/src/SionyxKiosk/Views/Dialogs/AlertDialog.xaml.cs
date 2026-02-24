using System.Windows;
using System.Windows.Media;

namespace SionyxKiosk.Views.Dialogs;

public partial class AlertDialog : Window
{
    public enum AlertType { Info, Success, Warning, Error }

    public AlertDialog(string title, string message, AlertType type = AlertType.Info, bool showCancel = false)
    {
        InitializeComponent();
        TitleText.Text = title;
        BodyText.Text = message;

        (IconText.Text, HeaderBorder.Background) = type switch
        {
            AlertType.Success => ("✅", new LinearGradientBrush(
                Color.FromRgb(0x10, 0xB9, 0x81), Color.FromRgb(0x05, 0x96, 0x69), 135)),
            AlertType.Warning => ("⚠️", new LinearGradientBrush(
                Color.FromRgb(0xF5, 0x9E, 0x0B), Color.FromRgb(0xD9, 0x77, 0x06), 135)),
            AlertType.Error => ("❌", new LinearGradientBrush(
                Color.FromRgb(0xEF, 0x44, 0x44), Color.FromRgb(0xDC, 0x26, 0x26), 135)),
            _ => ("ℹ️", (Brush)FindResource("HeroGradient")),
        };

        if (showCancel)
        {
            CancelButton.Visibility = Visibility.Visible;
            OkButton.Content = "אישור";
        }
    }

    private void OkButton_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = true;
        Close();
    }

    private void CancelButton_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }

    /// <summary>Show a modal alert dialog.</summary>
    public static bool? Show(string title, string message, AlertType type = AlertType.Info, Window? owner = null)
    {
        var dialog = new AlertDialog(title, message, type);
        if (owner != null) dialog.Owner = owner;
        return dialog.ShowDialog();
    }

    /// <summary>Show a confirmation dialog with OK/Cancel buttons. Returns true if confirmed.</summary>
    public static bool Confirm(string title, string message, AlertType type = AlertType.Warning, Window? owner = null)
    {
        var dialog = new AlertDialog(title, message, type, showCancel: true);
        if (owner != null) dialog.Owner = owner;
        return dialog.ShowDialog() == true;
    }
}
