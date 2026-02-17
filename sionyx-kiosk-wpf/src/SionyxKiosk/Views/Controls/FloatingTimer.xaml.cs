using System.Windows;
using System.Windows.Input;
using System.Windows.Media;

namespace SionyxKiosk.Views.Controls;

/// <summary>
/// Topmost draggable floating timer window shown during active sessions.
/// Displays: remaining time, usage time, print balance, offline indicator.
/// Changes color based on warning state (normal → orange → red).
/// </summary>
public partial class FloatingTimer : Window
{
    public event Action? ReturnRequested;

    private const double CompactWidth = 230;

    public FloatingTimer()
    {
        InitializeComponent();

        // Start compact — only the timer visible
        Width = CompactWidth;

        // Position bottom-right of the work area
        var screen = SystemParameters.WorkArea;
        Left = screen.Right - CompactWidth - 20;
        Top = screen.Bottom - Height - 20;
    }

    /// <summary>Update the displayed remaining time and apply warning colors.</summary>
    public void UpdateTime(int remainingSeconds)
    {
        var ts = TimeSpan.FromSeconds(Math.Max(0, remainingSeconds));
        TimeText.Text = ts.ToString(@"hh\:mm\:ss");

        if (remainingSeconds <= 60)
        {
            // Critical: red-tinted dark background
            TimerBorder.Background = new LinearGradientBrush(
                Color.FromRgb(0x4C, 0x10, 0x10), Color.FromRgb(0x7F, 0x1D, 0x1D),
                new Point(0, 0), new Point(1, 1));
            TimeText.Foreground = new SolidColorBrush(Color.FromRgb(0xFE, 0xCA, 0xCA));
        }
        else if (remainingSeconds <= 300)
        {
            // Warning: amber-tinted dark background
            TimerBorder.Background = new LinearGradientBrush(
                Color.FromRgb(0x45, 0x32, 0x05), Color.FromRgb(0x71, 0x3F, 0x12),
                new Point(0, 0), new Point(1, 1));
            TimeText.Foreground = new SolidColorBrush(Color.FromRgb(0xFD, 0xE6, 0x8A));
        }
        else
        {
            // Normal: indigo
            TimerBorder.Background = new LinearGradientBrush(
                Color.FromRgb(0x1E, 0x1B, 0x4B), Color.FromRgb(0x31, 0x2E, 0x81),
                new Point(0, 0), new Point(1, 1));
            TimeText.Foreground = new SolidColorBrush(Colors.White);
        }
    }

    /// <summary>Update the displayed usage time.</summary>
    public void UpdateUsageTime(int usedSeconds)
    {
        var ts = TimeSpan.FromSeconds(Math.Max(0, usedSeconds));
        UsageText.Text = ts.TotalHours >= 1
            ? ts.ToString(@"h\:mm\:ss")
            : ts.ToString(@"mm\:ss");
    }

    /// <summary>Update the displayed print balance.</summary>
    public void UpdatePrintBalance(double balance)
    {
        PrintText.Text = $"{balance:F2} ₪";
    }

    /// <summary>Show or hide the offline indicator.</summary>
    public void SetOfflineMode(bool isOffline)
    {
        OfflineBadge.Visibility = isOffline ? Visibility.Visible : Visibility.Collapsed;
    }

    private void Window_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        DragMove();
    }

    private void ReturnButton_Click(object sender, RoutedEventArgs e)
    {
        ReturnRequested?.Invoke();
    }
}
