using System.Windows;
using System.Windows.Controls;

namespace SionyxKiosk.Views.Controls;

public partial class LoadingOverlay : UserControl
{
    public static readonly DependencyProperty IsOverlayVisibleProperty =
        DependencyProperty.Register(nameof(IsOverlayVisible), typeof(bool), typeof(LoadingOverlay),
            new PropertyMetadata(false, OnIsVisibleChanged));

    public static readonly DependencyProperty LoadingTextProperty =
        DependencyProperty.Register(nameof(LoadingText), typeof(string), typeof(LoadingOverlay),
            new PropertyMetadata("טוען..."));

    public bool IsOverlayVisible { get => (bool)GetValue(IsOverlayVisibleProperty); set => SetValue(IsOverlayVisibleProperty, value); }
    public string LoadingText { get => (string)GetValue(LoadingTextProperty); set => SetValue(LoadingTextProperty, value); }

    public LoadingOverlay() { InitializeComponent(); }

    private static void OnIsVisibleChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is LoadingOverlay overlay)
            overlay.Visibility = (bool)e.NewValue ? Visibility.Visible : Visibility.Collapsed;
    }
}
