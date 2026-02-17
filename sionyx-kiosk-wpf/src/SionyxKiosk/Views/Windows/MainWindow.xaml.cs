using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Data;
using System.Windows.Input;
using SionyxKiosk.ViewModels;
using SionyxKiosk.Views.Pages;

namespace SionyxKiosk.Views.Windows;

public partial class MainWindow : Window
{
    private readonly MainViewModel _vm;
    private readonly IServiceProvider _services;
    private bool _initialized;
    private bool _allowClose;
    private Page? _currentPage;

    public MainWindow(MainViewModel viewModel, IServiceProvider services)
    {
        _vm = viewModel;
        _services = services;
        DataContext = viewModel;
        InitializeComponent();
        Resources["InverseBool"] = new InverseBoolConverter();
        _initialized = true;

        Loaded += (_, _) =>
        {
            NavigateToPage("Home");
            UpdateAvatarInitials();
        };

        viewModel.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(MainViewModel.CurrentUser))
                UpdateAvatarInitials();
        };
    }

    private void UpdateAvatarInitials()
    {
        var name = _vm.CurrentUser?.FullName;
        if (string.IsNullOrWhiteSpace(name))
        {
            AvatarInitials.Text = "?";
            return;
        }
        var parts = name.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries);
        AvatarInitials.Text = parts.Length >= 2
            ? $"{parts[0][0]}{parts[^1][0]}"
            : $"{parts[0][0]}";
    }

    /// <summary>Allow the window to close (called from admin exit or proper logout).</summary>
    public void AllowClose() => _allowClose = true;

    private void NavButton_Checked(object sender, RoutedEventArgs e)
    {
        if (!_initialized) return;
        if (sender is RadioButton rb && rb.Tag is string page)
        {
            _vm.CurrentPage = page;
            NavigateToPage(page);
        }
    }

    private void NavigateToPage(string page)
    {
        if (ContentFrame == null) return;

        try
        {
            // Dispose previous page's ViewModel if it implements IDisposable.
            // This prevents event subscription leaks on singleton services.
            if (_currentPage?.DataContext is IDisposable disposableVm)
                disposableVm.Dispose();

            var pageInstance = page switch
            {
                "Home" => _services.GetService(typeof(HomePage)),
                "Packages" => _services.GetService(typeof(PackagesPage)),
                "History" => _services.GetService(typeof(HistoryPage)),
                "Help" => _services.GetService(typeof(HelpPage)),
                _ => _services.GetService(typeof(HomePage))
            };

            if (pageInstance is Page p)
            {
                _currentPage = p;
                // Set Content directly instead of Navigate() to avoid
                // WPF Frame journal accumulation (keeps all old pages in memory).
                ContentFrame.Content = p;
            }
        }
        catch (Exception ex)
        {
            Serilog.Log.Error(ex, "Failed to navigate to page {Page}", page);
        }
    }

    /// <summary>Navigate back to Home page (called after session ends to refresh the view).</summary>
    public void NavigateHome()
    {
        NavHome.IsChecked = true;
        _vm.CurrentPage = "Home";
        NavigateToPage("Home");
    }

    /// <summary>Show a toast notification in the content area.</summary>
    public void ShowToast(string title, string message,
        Controls.ToastNotification.ToastType type = Controls.ToastNotification.ToastType.Info,
        int durationMs = 3000)
    {
        Toast.Show(title, message, type, durationMs);
    }

    protected override void OnClosing(System.ComponentModel.CancelEventArgs e)
    {
        // Dispose current page ViewModel on window close
        if (_currentPage?.DataContext is IDisposable disposable)
            disposable.Dispose();

        if (!_allowClose)
        {
            e.Cancel = true;
            return;
        }
        base.OnClosing(e);
    }

    protected override void OnKeyDown(KeyEventArgs e)
    {
        if (e.Key == Key.Escape || e.Key == Key.System)
        {
            e.Handled = true;
            return;
        }
        base.OnKeyDown(e);
    }
}
