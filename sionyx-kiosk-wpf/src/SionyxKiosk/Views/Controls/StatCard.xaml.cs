using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace SionyxKiosk.Views.Controls;

public partial class StatCard : UserControl
{
    public static readonly DependencyProperty TitleProperty =
        DependencyProperty.Register(nameof(Title), typeof(string), typeof(StatCard), new PropertyMetadata(""));

    public static readonly DependencyProperty ValueProperty =
        DependencyProperty.Register(nameof(Value), typeof(string), typeof(StatCard), new PropertyMetadata(""));

    public static readonly DependencyProperty IconProperty =
        DependencyProperty.Register(nameof(Icon), typeof(string), typeof(StatCard), new PropertyMetadata(""));

    public static readonly DependencyProperty AccentColorProperty =
        DependencyProperty.Register(nameof(AccentColor), typeof(Color), typeof(StatCard),
            new PropertyMetadata(Color.FromRgb(99, 102, 241)));

    public static readonly DependencyProperty AccentBgColorProperty =
        DependencyProperty.Register(nameof(AccentBgColor), typeof(Color), typeof(StatCard),
            new PropertyMetadata(Color.FromRgb(238, 242, 255)));

    public string Title { get => (string)GetValue(TitleProperty); set => SetValue(TitleProperty, value); }
    public string Value { get => (string)GetValue(ValueProperty); set => SetValue(ValueProperty, value); }
    public string Icon { get => (string)GetValue(IconProperty); set => SetValue(IconProperty, value); }
    public Color AccentColor { get => (Color)GetValue(AccentColorProperty); set => SetValue(AccentColorProperty, value); }
    public Color AccentBgColor { get => (Color)GetValue(AccentBgColorProperty); set => SetValue(AccentBgColorProperty, value); }

    public StatCard() { InitializeComponent(); }
}
