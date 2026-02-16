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

    public FloatingTimer()
    {
        InitializeComponent();

        // Position bottom-right of the work area
        var screen = SystemParameters.WorkArea;
        Left = screen.Right - Width - 20;
        Top = screen.Bottom - Height - 20;
    }

    /// <summary>Update the displayed remaining time and apply warning colors.</summary>
    public void UpdateTime(int remainingSeconds)
    {
        var ts = TimeSpan.FromSeconds(Math.Max(0, remainingSeconds));
        TimeText.Text = ts.ToString(@"hh\:mm\:ss");

        if (remainingSeconds <= 60)
        {
            // Critical: red
            TimerBorder.Background = new SolidColorBrush(Color.FromArgb(0xF0, 0xFE, 0xE2, 0xE2));
            TimeText.Foreground = new SolidColorBrush(Color.FromRgb(0xEF, 0x44, 0x44));
        }
        else if (remainingSeconds <= 300)
        {
            // Warning: orange
            TimerBorder.Background = new SolidColorBrush(Color.FromArgb(0xF0, 0xFE, 0xF3, 0xC7));
            TimeText.Foreground = new SolidColorBrush(Color.FromRgb(0xF5, 0x9E, 0x0B));
        }
        else
        {
            // Normal: white
            TimerBorder.Background = new SolidColorBrush(Color.FromArgb(0xE6, 0xFF, 0xFF, 0xFF));
            TimeText.Foreground = (Brush)FindResource("TextPrimaryBrush");
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
