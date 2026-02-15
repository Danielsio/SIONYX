using System.Windows;
using System.Windows.Controls;

namespace SionyxKiosk.Views.Controls;

public partial class MessageCard : UserControl
{
    public static readonly DependencyProperty SenderNameProperty =
        DependencyProperty.Register(nameof(SenderName), typeof(string), typeof(MessageCard), new PropertyMetadata(""));

    public static readonly DependencyProperty MessageTextProperty =
        DependencyProperty.Register(nameof(MessageText), typeof(string), typeof(MessageCard), new PropertyMetadata(""));

    public static readonly DependencyProperty TimestampProperty =
        DependencyProperty.Register(nameof(Timestamp), typeof(string), typeof(MessageCard), new PropertyMetadata(""));

    public string SenderName { get => (string)GetValue(SenderNameProperty); set => SetValue(SenderNameProperty, value); }
    public string MessageText { get => (string)GetValue(MessageTextProperty); set => SetValue(MessageTextProperty, value); }
    public string Timestamp { get => (string)GetValue(TimestampProperty); set => SetValue(TimestampProperty, value); }

    public MessageCard() { InitializeComponent(); }
}
