using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media.Animation;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Pages;

public partial class HelpPage : Page
{
    private readonly HelpViewModel _vm;

    public HelpPage(HelpViewModel viewModel)
    {
        _vm = viewModel;
        DataContext = viewModel;
        InitializeComponent();

        Loaded += async (_, _) => await viewModel.LoadContactCommand.ExecuteAsync(null);
    }

    private void PhoneRow_Click(object sender, MouseButtonEventArgs e)
    {
        if (!string.IsNullOrEmpty(_vm.AdminPhone))
            _vm.CopyToClipboardCommand.Execute(_vm.AdminPhone);
    }

    private void EmailRow_Click(object sender, MouseButtonEventArgs e)
    {
        if (!string.IsNullOrEmpty(_vm.AdminEmail))
            _vm.CopyToClipboardCommand.Execute(_vm.AdminEmail);
    }

    private void FaqItem_Click(object sender, MouseButtonEventArgs e)
    {
        if (sender is not FrameworkElement element) return;

        var answerBlock = FindChild<TextBlock>(element, "AnswerBlock");
        var chevron = FindChild<TextBlock>(element, "Chevron");

        if (answerBlock == null) return;

        var ease = new CubicEase { EasingMode = EasingMode.EaseInOut };
        var duration = TimeSpan.FromMilliseconds(250);

        if (answerBlock.Visibility == Visibility.Collapsed)
        {
            answerBlock.Visibility = Visibility.Visible;
            answerBlock.Measure(new Size(answerBlock.MaxWidth > 0 ? answerBlock.MaxWidth : ActualWidth, double.PositiveInfinity));
            var targetHeight = answerBlock.DesiredSize.Height;

            answerBlock.Opacity = 0;
            var fadeIn = new DoubleAnimation(0, 1, duration) { EasingFunction = ease };
            answerBlock.BeginAnimation(OpacityProperty, fadeIn);

            if (chevron != null) chevron.Text = "▲";
        }
        else
        {
            var fadeOut = new DoubleAnimation(1, 0, duration) { EasingFunction = ease };
            fadeOut.Completed += (_, _) => answerBlock.Visibility = Visibility.Collapsed;
            answerBlock.BeginAnimation(OpacityProperty, fadeOut);

            if (chevron != null) chevron.Text = "▼";
        }
    }

    private static T? FindChild<T>(DependencyObject parent, string name) where T : FrameworkElement
    {
        for (int i = 0; i < System.Windows.Media.VisualTreeHelper.GetChildrenCount(parent); i++)
        {
            var child = System.Windows.Media.VisualTreeHelper.GetChild(parent, i);
            if (child is T t && t.Name == name) return t;
            var result = FindChild<T>(child, name);
            if (result != null) return result;
        }
        return null;
    }
}
