using System.Windows;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Views.Dialogs;

public partial class MessageDialog : Window
{
    public MessageDialog(MessageViewModel viewModel)
    {
        DataContext = viewModel;
        InitializeComponent();

        viewModel.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(MessageViewModel.CurrentIndex) ||
                e.PropertyName == nameof(MessageViewModel.Messages))
            {
                CounterText.Text = $"{viewModel.CurrentIndex + 1}/{viewModel.Messages.Count}";
            }
        };

        viewModel.AllMessagesRead += () =>
        {
            DialogResult = true;
            Close();
        };

        Loaded += async (_, _) => await viewModel.LoadMessagesCommand.ExecuteAsync(null);
    }
}
