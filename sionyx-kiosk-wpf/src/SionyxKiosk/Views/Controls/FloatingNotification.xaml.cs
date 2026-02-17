using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Threading;

namespace SionyxKiosk.Views.Controls;

/// <summary>
/// Topmost floating notification that appears above the desktop — visible even
/// when the kiosk main window is minimized. Used for print job feedback, warnings, etc.
/// Auto-dismisses after a configurable duration.
/// </summary>
public partial class FloatingNotification : Window
{
    public enum NotificationType { Success, Error, Warning, Info }

    private readonly DispatcherTimer _autoClose;

    public FloatingNotification()
    {
        InitializeComponent();

        _autoClose = new DispatcherTimer();
        _autoClose.Tick += (_, _) =>
        {
            _autoClose.Stop();
            AnimateOut();
        };
    }

    /// <summary>Show a global floating notification above the taskbar.</summary>
    public static void Show(string title, string message,
        NotificationType type = NotificationType.Info, int durationMs = 4000)
    {
        // Must run on UI thread
        var dispatcher = Application.Current?.Dispatcher;
        if (dispatcher == null) return;

        if (!dispatcher.CheckAccess())
        {
            dispatcher.BeginInvoke(() => Show(title, message, type, durationMs));
            return;
        }

        var notif = new FloatingNotification();
        notif.Configure(title, message, type, durationMs);
        notif.PositionOnScreen();
        notif.Show();
        notif.AnimateIn();
    }

    private void Configure(string title, string message, NotificationType type, int durationMs)
    {
        TitleText.Text = title;
        MessageText.Text = message;

        // Theme by type
        var (bg, iconBg, icon) = type switch
        {
            NotificationType.Success => (
                new LinearGradientBrush(Color.FromRgb(0x05, 0x96, 0x69), Color.FromRgb(0x10, 0xB9, 0x81), 0),
                new SolidColorBrush(Color.FromArgb(0x33, 0xFF, 0xFF, 0xFF)),
                "✓"),
            NotificationType.Error => (
                new LinearGradientBrush(Color.FromRgb(0xDC, 0x26, 0x26), Color.FromRgb(0xEF, 0x44, 0x44), 0),
                new SolidColorBrush(Color.FromArgb(0x33, 0xFF, 0xFF, 0xFF)),
                "✕"),
            NotificationType.Warning => (
                new LinearGradientBrush(Color.FromRgb(0xD9, 0x77, 0x06), Color.FromRgb(0xF5, 0x9E, 0x0B), 0),
                new SolidColorBrush(Color.FromArgb(0x33, 0xFF, 0xFF, 0xFF)),
                "⚠"),
            _ => (
                new LinearGradientBrush(Color.FromRgb(0x31, 0x2E, 0x81), Color.FromRgb(0x63, 0x66, 0xF1), 0),
                new SolidColorBrush(Color.FromArgb(0x33, 0xFF, 0xFF, 0xFF)),
                "ℹ"),
        };

        CardBorder.Background = bg;
        IconBorder.Background = iconBg;
        IconText.Text = icon;

        _autoClose.Interval = TimeSpan.FromMilliseconds(durationMs);
    }

    private void PositionOnScreen()
    {
        var screen = SystemParameters.WorkArea;
        // Bottom-right, above where the FloatingTimer typically sits
        Left = screen.Right - Width - 20;
        Top = screen.Bottom - Height - 110; // Above the timer
    }

    private void AnimateIn()
    {
        var storyboard = (Storyboard)FindResource("ShowAnim");
        storyboard.Begin(this);
        _autoClose.Start();
    }

    private void AnimateOut()
    {
        var storyboard = (Storyboard)FindResource("HideAnim");
        storyboard.Completed += (_, _) => Close();
        storyboard.Begin(this);
    }
}
