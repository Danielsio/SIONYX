using System.Windows;

namespace SionyxKiosk.Views.Dialogs;

public partial class ModernDialog : Window
{
    public enum DialogType { Confirm, Info, Warning }

    public ModernDialog(string title, string message, DialogType type = DialogType.Confirm, bool showCancel = true)
    {
        InitializeComponent();
        TitleText.Text = title;
        MessageText.Text = message;
        CancelButton.Visibility = showCancel ? Visibility.Visible : Visibility.Collapsed;

        IconText.Text = type switch
        {
            DialogType.Warning => "⚠️",
            DialogType.Info => "ℹ️",
            _ => "❓"
        };
    }

    private void ConfirmButton_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = true;
        Close();
    }

    private void CancelButton_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }

    /// <summary>Show a confirmation dialog. Returns true if confirmed.</summary>
    public static bool Confirm(string title, string message, Window? owner = null)
    {
        var dialog = new ModernDialog(title, message, DialogType.Confirm);
        if (owner != null) dialog.Owner = owner;
        return dialog.ShowDialog() == true;
    }

    /// <summary>Show an info dialog (OK only).</summary>
    public static void Info(string title, string message, Window? owner = null)
    {
        var dialog = new ModernDialog(title, message, DialogType.Info, showCancel: false);
        if (owner != null) dialog.Owner = owner;
        dialog.ShowDialog();
    }
}
