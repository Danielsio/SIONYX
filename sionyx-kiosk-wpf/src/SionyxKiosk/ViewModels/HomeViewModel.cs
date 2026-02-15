using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>Home page ViewModel: stats, session controls, messages.</summary>
public partial class HomeViewModel : ObservableObject
{
    private readonly SessionService _session;
    private readonly ChatService _chat;
    private readonly UserData _user;

    [ObservableProperty] private string _remainingTime = "00:00:00";
    [ObservableProperty] private string _printBalance = "0.00 ₪";
    [ObservableProperty] private int _unreadMessages;
    [ObservableProperty] private bool _isSessionActive;
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private string _errorMessage = "";

    public HomeViewModel(SessionService session, ChatService chat, UserData user)
    {
        _session = session;
        _chat = chat;
        _user = user;

        UpdateStats();
        _session.TimeUpdated += OnTimeUpdated;
    }

    [RelayCommand]
    private async Task StartSessionAsync()
    {
        if (_session.IsActive) return;
        IsLoading = true;
        ErrorMessage = "";

        var result = await _session.StartSessionAsync(_user.RemainingTime);
        IsLoading = false;

        if (result.IsSuccess)
            IsSessionActive = true;
        else
            ErrorMessage = result.Error ?? "שגיאה";
    }

    [RelayCommand]
    private async Task EndSessionAsync()
    {
        if (!_session.IsActive) return;
        await _session.EndSessionAsync("user");
        IsSessionActive = false;
        UpdateStats();
    }

    private void OnTimeUpdated(int remaining)
    {
        var ts = TimeSpan.FromSeconds(Math.Max(0, remaining));
        RemainingTime = ts.ToString(@"hh\:mm\:ss");
    }

    private void UpdateStats()
    {
        var ts = TimeSpan.FromSeconds(Math.Max(0, _user.RemainingTime));
        RemainingTime = ts.ToString(@"hh\:mm\:ss");
        PrintBalance = $"{_user.PrintBalance:F2} ₪";
    }
}
