using System.Windows;
using System.Windows.Input;
using System.Windows.Media;

namespace SionyxKiosk.Views.Controls;

/// <summary>
/// Topmost draggable floating timer window that shows remaining session time.
/// Changes color based on warning state.
/// </summary>
public partial class FloatingTimer : Window
{
    public event Action? ReturnRequested;

    public FloatingTimer()
    {
        InitializeComponent();

        // Position bottom-right by default
        var screen = SystemParameters.WorkArea;
        Left = screen.Right - Width - 20;
        Top = screen.Bottom - Height - 20;
    }

    /// <summary>Update the displayed time.</summary>
    public void UpdateTime(int remainingSeconds)
    {
        var ts = TimeSpan.FromSeconds(Math.Max(0, remainingSeconds));
        TimeText.Text = ts.ToString(@"hh\:mm\:ss");

        // Warning states
        if (remainingSeconds <= 60)
        {
            TimerBorder.Background = new SolidColorBrush(Color.FromArgb(0xF0, 0xFE, 0xE2, 0xE2)); // Error light
            TimeText.Foreground = new SolidColorBrush(Color.FromRgb(0xEF, 0x44, 0x44));
        }
        else if (remainingSeconds <= 300)
        {
            TimerBorder.Background = new SolidColorBrush(Color.FromArgb(0xF0, 0xFE, 0xF3, 0xC7)); // Warning light
            TimeText.Foreground = new SolidColorBrush(Color.FromRgb(0xF5, 0x9E, 0x0B));
        }
        else
        {
            TimerBorder.Background = new SolidColorBrush(Color.FromArgb(0xE6, 0xFF, 0xFF, 0xFF)); // Normal
            TimeText.Foreground = (Brush)FindResource("TextPrimaryBrush");
        }
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
