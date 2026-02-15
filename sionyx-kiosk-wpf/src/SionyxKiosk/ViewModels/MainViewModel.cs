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
    private async Task LogoutAsync()
    {
        await _auth.LogoutAsync();
        LogoutRequested?.Invoke();
    }

    [RelayCommand]
    private void ToggleSidebar()
    {
        IsSidebarCollapsed = !IsSidebarCollapsed;
    }
}
