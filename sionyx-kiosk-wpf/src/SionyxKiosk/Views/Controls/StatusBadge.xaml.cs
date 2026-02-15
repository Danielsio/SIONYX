using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace SionyxKiosk.Views.Controls;

public partial class StatusBadge : UserControl
{
    public static readonly DependencyProperty TextProperty =
        DependencyProperty.Register(nameof(Text), typeof(string), typeof(StatusBadge), new PropertyMetadata(""));

    public static readonly DependencyProperty BadgeBackgroundProperty =
        DependencyProperty.Register(nameof(BadgeBackground), typeof(Brush), typeof(StatusBadge),
            new PropertyMetadata(new SolidColorBrush(Color.FromRgb(0xE0, 0xE7, 0xFF))));

    public static readonly DependencyProperty BadgeForegroundProperty =
        DependencyProperty.Register(nameof(BadgeForeground), typeof(Brush), typeof(StatusBadge),
            new PropertyMetadata(new SolidColorBrush(Color.FromRgb(0x63, 0x66, 0xF1))));

    /// <summary>
    /// Status string. Setting this auto-maps Text, BadgeBackground, and BadgeForeground
    /// based on the status value (pending, completed, approved, failed, cancelled, etc.)
    /// </summary>
    public static readonly DependencyProperty StatusProperty =
        DependencyProperty.Register(nameof(Status), typeof(string), typeof(StatusBadge),
            new PropertyMetadata("", OnStatusChanged));

    public string Text { get => (string)GetValue(TextProperty); set => SetValue(TextProperty, value); }
    public Brush BadgeBackground { get => (Brush)GetValue(BadgeBackgroundProperty); set => SetValue(BadgeBackgroundProperty, value); }
    public Brush BadgeForeground { get => (Brush)GetValue(BadgeForegroundProperty); set => SetValue(BadgeForegroundProperty, value); }
    public string Status { get => (string)GetValue(StatusProperty); set => SetValue(StatusProperty, value); }

    public StatusBadge() { InitializeComponent(); }

    private static void OnStatusChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is not StatusBadge badge) return;
        var status = (e.NewValue as string ?? "").ToLowerInvariant();

        var (label, bg, fg) = status switch
        {
            "completed" or "approved" => ("הושלם", "#D1FAE5", "#065F46"),
            "pending" => ("ממתין", "#FEF3C7", "#92400E"),
            "processing" => ("בעיבוד", "#DBEAFE", "#1E40AF"),
            "failed" or "error" => ("נכשל", "#FEE2E2", "#991B1B"),
            "cancelled" or "canceled" => ("בוטל", "#F3F4F6", "#374151"),
            "refunded" => ("הוחזר", "#E0E7FF", "#3730A3"),
            _ => (status, "#E0E7FF", "#4338CA"),
        };

        badge.Text = label;
        badge.BadgeBackground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(bg));
        badge.BadgeForeground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(fg));
    }
}
