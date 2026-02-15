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

    public string Text { get => (string)GetValue(TextProperty); set => SetValue(TextProperty, value); }
    public Brush BadgeBackground { get => (Brush)GetValue(BadgeBackgroundProperty); set => SetValue(BadgeBackgroundProperty, value); }
    public Brush BadgeForeground { get => (Brush)GetValue(BadgeForegroundProperty); set => SetValue(BadgeForegroundProperty, value); }

    public StatusBadge() { InitializeComponent(); }
}
