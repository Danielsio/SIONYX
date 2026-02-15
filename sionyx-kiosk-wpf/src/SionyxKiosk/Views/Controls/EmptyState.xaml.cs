using System.Windows;
using System.Windows.Controls;

namespace SionyxKiosk.Views.Controls;

public partial class EmptyState : UserControl
{
    public static readonly DependencyProperty IconProperty =
        DependencyProperty.Register(nameof(Icon), typeof(string), typeof(EmptyState), new PropertyMetadata("📭"));

    public static readonly DependencyProperty MessageProperty =
        DependencyProperty.Register(nameof(Message), typeof(string), typeof(EmptyState), new PropertyMetadata("אין נתונים"));

    public string Icon { get => (string)GetValue(IconProperty); set => SetValue(IconProperty, value); }
    public string Message { get => (string)GetValue(MessageProperty); set => SetValue(MessageProperty, value); }

    public EmptyState() { InitializeComponent(); }
}
