using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Animation;

namespace SionyxKiosk.Views.Controls;

/// <summary>
/// Auto-dismiss toast notification control.
/// Place in a Grid overlay on MainWindow.
/// </summary>
public partial class ToastNotification : UserControl
{
    public enum ToastType { Info, Success, Warning, Error }

    private readonly Queue<(string title, string message, ToastType type)> _queue = new();
    private bool _isShowing;

    public ToastNotification()
    {
        InitializeComponent();
    }

    /// <summary>Show a toast notification. Queues if one is already showing.</summary>
    public void Show(string title, string message, ToastType type = ToastType.Info, int durationMs = 3000)
    {
        _queue.Enqueue((title, message, type));
        if (!_isShowing)
            _ = ProcessQueueAsync(durationMs);
    }

    private async Task ProcessQueueAsync(int durationMs)
    {
        _isShowing = true;

        while (_queue.Count > 0)
        {
            var (title, message, type) = _queue.Dequeue();
            ShowToast(title, message, type);
            await Task.Delay(durationMs);
            HideToast();
            await Task.Delay(300); // gap between toasts
        }

        _isShowing = false;
    }

    private void ShowToast(string title, string message, ToastType type)
    {
        TitleText.Text = title;
        MessageText.Text = message;
        MessageText.Visibility = string.IsNullOrEmpty(message)
            ? Visibility.Collapsed
            : Visibility.Visible;

        (IconText.Text, ToastBorder.Background) = type switch
        {
            ToastType.Success => ("✅", new SolidColorBrush(Color.FromRgb(0x06, 0x5F, 0x46))),
            ToastType.Warning => ("⚠️", new SolidColorBrush(Color.FromRgb(0x78, 0x35, 0x0F))),
            ToastType.Error => ("❌", new SolidColorBrush(Color.FromRgb(0x7F, 0x1D, 0x1D))),
            _ => ("ℹ️", new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B))),
        };

        ToastBorder.Visibility = Visibility.Visible;

        // Slide in + fade in animation
        var slideIn = new DoubleAnimation(-20, 0, TimeSpan.FromMilliseconds(200))
        {
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut }
        };
        var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(200));
        SlideTransform.BeginAnimation(TranslateTransform.YProperty, slideIn);
        ToastBorder.BeginAnimation(OpacityProperty, fadeIn);
    }

    private void HideToast()
    {
        var slideOut = new DoubleAnimation(0, -20, TimeSpan.FromMilliseconds(200))
        {
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseIn }
        };
        var fadeOut = new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(200));
        fadeOut.Completed += (_, _) => ToastBorder.Visibility = Visibility.Collapsed;
        SlideTransform.BeginAnimation(TranslateTransform.YProperty, slideOut);
        ToastBorder.BeginAnimation(OpacityProperty, fadeOut);
    }
}
