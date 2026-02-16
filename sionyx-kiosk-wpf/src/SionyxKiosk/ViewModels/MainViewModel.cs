using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>Main window ViewModel: navigation, user info, session state.</summary>
public partial class MainViewModel : ObservableObject
{
    private readonly AuthService _auth;

    [ObservableProperty] private string _currentPage = "Home";
    [ObservableProperty] private UserData? _currentUser;
    [ObservableProperty] private bool _isSidebarCollapsed;

    /// <summary>Raised when the user requests logout. App.xaml.cs handles the actual logout.</summary>
    public event Action? LogoutRequested;

    public MainViewModel(AuthService auth)
    {
        _auth = auth;
        CurrentUser = auth.CurrentUser;
    }

    [RelayCommand]
    private void Navigate(string page)
    {
        CurrentPage = page;
    }

    [RelayCommand]
    private void Logout()
    {
        // Don't call auth.LogoutAsync() here — the App.xaml.cs OnLogoutRequested
        // handler owns the full logout sequence (stop services → logout → show auth window).
        // Calling it here would double-logout and could race with service teardown.
        LogoutRequested?.Invoke();
    }

    [RelayCommand]
    private void ToggleSidebar()
    {
        IsSidebarCollapsed = !IsSidebarCollapsed;
    }
}
