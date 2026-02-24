using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using SionyxKiosk.ViewModels;
using SionyxKiosk.Views.Dialogs;
using SionyxKiosk.Views.Windows;

namespace SionyxKiosk.Views.Pages;

public partial class HomePage : Page
{
    private readonly HomeViewModel _vm;
    private readonly IServiceProvider _services;

    public HomePage(HomeViewModel viewModel, IServiceProvider services)
    {
        _vm = viewModel;
        _services = services;
        DataContext = viewModel;
        Resources["StringToVis"] = new Views.Controls.StringToVisibilityConverter();
        Resources["InverseBool"] = new InverseBoolConverter();
        Resources["InverseBoolToVis"] = new InverseBoolToVisibilityConverter();
        InitializeComponent();

        viewModel.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(HomeViewModel.UnreadMessages))
                UpdateMessageCard(viewModel.UnreadMessages);
            if (e.PropertyName == nameof(HomeViewModel.HasAnnouncements))
                UpdateAnnouncementsSection();
        };

        viewModel.ViewMessagesRequested += OpenMessageDialog;
        viewModel.NavigateToPackagesRequested += NavigateToPackages;
        viewModel.SessionStartedSuccessfully += OnSessionStarted;

        UpdateMessageCard(viewModel.UnreadMessages);
        UpdateAnnouncementsSection();
    }

    private void UpdateMessageCard(int count)
    {
        if (count > 0)
        {
            MessageCard.Visibility = Visibility.Visible;
            MessageCountText.Text = count == 1
                ? "הודעה חדשה אחת"
                : $"{count} הודעות חדשות";
        }
        else
        {
            MessageCard.Visibility = Visibility.Collapsed;
        }
    }

    private void UpdateAnnouncementsSection()
    {
        var count = _vm.GlobalAnnouncements.Count;
        if (count > 0)
        {
            AnnouncementsSection.Visibility = Visibility.Visible;
            AnnouncementCountText.Text = count.ToString();
        }
        else
        {
            AnnouncementsSection.Visibility = Visibility.Collapsed;
        }
    }

    private void MessageCard_Click(object sender, MouseButtonEventArgs e)
    {
        _vm.ViewMessagesCommand.Execute(null);
    }

    private void OpenMessageDialog()
    {
        var msgVm = (MessageViewModel)_services.GetService(typeof(MessageViewModel))!;
        var dialog = new MessageDialog(msgVm);
        dialog.Owner = Window.GetWindow(this);
        dialog.ShowDialog();

        _vm.UnreadMessages = 0;
    }

    private void NavigateToPackages()
    {
        var mainWindow = Window.GetWindow(this) as Windows.MainWindow;
        mainWindow?.NavigateToPackages();
    }

    private void OnSessionStarted()
    {
        Dispatcher.Invoke(() =>
        {
            if (Window.GetWindow(this) is MainWindow main)
                main.ShowToast("ההפעלה התחילה!", "הזמן שלך רץ, בהצלחה!",
                    Controls.ToastNotification.ToastType.Success);
        });
    }

    private void EndSession_Click(object sender, RoutedEventArgs e)
    {
        var confirmed = AlertDialog.Confirm(
            "סיום הפעלה",
            "האם אתה בטוח שברצונך לסיים את ההפעלה?",
            AlertDialog.AlertType.Warning,
            Window.GetWindow(this));

        if (confirmed)
            _vm.EndSessionCommand.Execute(null);
    }

    private void ResumeSession_Click(object sender, RoutedEventArgs e)
    {
        if (Application.Current is App app)
            app.ResumeSession();
    }
}
