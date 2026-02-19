using System.Windows;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Dialogs;

public partial class MessageDialog : Window
{
    private readonly MessageViewModel _vm;

    public MessageDialog(MessageViewModel viewModel)
    {
        _vm = viewModel;
        DataContext = viewModel;
        InitializeComponent();

        viewModel.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(MessageViewModel.Messages))
                UpdateSubtitle();
            if (e.PropertyName == nameof(MessageViewModel.IsEmpty))
                UpdateStates();
            if (e.PropertyName == nameof(MessageViewModel.IsLoading))
                UpdateStates();
        };

        viewModel.AllMessagesRead += () =>
        {
            DialogResult = true;
            Close();
        };

        Loaded += async (_, _) =>
        {
            await viewModel.LoadMessagesCommand.ExecuteAsync(null);
            ScrollToBottom();
        };
    }

    private void UpdateSubtitle()
    {
        var count = _vm.Messages.Count;
        SubtitleText.Text = count switch
        {
            0 => "אין הודעות חדשות",
            1 => "הודעה אחת שלא נקראה",
            _ => $"{count} הודעות שלא נקראו",
        };
    }

    private void UpdateStates()
    {
        var empty = _vm.IsEmpty && !_vm.IsLoading;
        var hasMessages = !_vm.IsEmpty && !_vm.IsLoading;

        EmptyState.Visibility = empty ? Visibility.Visible : Visibility.Collapsed;
        MessageScroll.Visibility = hasMessages ? Visibility.Visible : Visibility.Collapsed;
        MarkReadBtn.IsEnabled = hasMessages;
    }

    private void ScrollToBottom()
    {
        MessageScroll.ScrollToEnd();
    }

    private void CloseBtn_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }

    private async void MarkReadBtn_Click(object sender, RoutedEventArgs e)
    {
        MarkReadBtn.IsEnabled = false;
        await _vm.MarkAllReadAndCloseAsync();
    }
}
