using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>Home page ViewModel: stats, session controls, messages, operating hours check.</summary>
public partial class HomeViewModel : ObservableObject, IDisposable
{
    private readonly SessionService _session;
    private readonly ChatService _chat;
    private readonly OperatingHoursService _operatingHours;
    private readonly UserData _user;
    private bool _disposed;

    [ObservableProperty] private string _remainingTime = "00:00:00";
    [ObservableProperty] private string _printBalance = "0.00 ₪";
    [ObservableProperty] private int _unreadMessages;
    [ObservableProperty] private bool _isSessionActive;
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private bool _isEndingSession;
    [ObservableProperty] private string _errorMessage = "";
    [ObservableProperty] private string _welcomeMessage = "";

    public bool IsSessionInactive => !IsSessionActive;

    /// <summary>Raised when the user wants to view unread messages. The View opens the MessageDialog.</summary>
    public event Action? ViewMessagesRequested;

    partial void OnIsSessionActiveChanged(bool value)
    {
        OnPropertyChanged(nameof(IsSessionInactive));
    }

    public HomeViewModel(SessionService session, ChatService chat, OperatingHoursService operatingHours, UserData user)
    {
        _session = session;
        _chat = chat;
        _operatingHours = operatingHours;
        _user = user;

        WelcomeMessage = $"שלום, {_user.FullName}!";
        IsSessionActive = _session.IsActive;
        UpdateStats();

        _session.TimeUpdated += OnTimeUpdated;
        _session.SessionStarted += OnSessionStarted;
        _session.SessionEnded += OnSessionEnded;
        _chat.MessagesReceived += OnMessagesReceived;

        _ = LoadUnreadCountAsync();
    }

    private async Task LoadUnreadCountAsync()
    {
        var result = await _chat.GetUnreadMessagesAsync();
        if (result.IsSuccess && result.Data is List<Dictionary<string, object?>> msgs)
            UnreadMessages = msgs.Count;
    }

    [RelayCommand]
    private async Task StartSessionAsync()
    {
        if (_session.IsActive) return;
        IsLoading = true;
        ErrorMessage = "";

        try
        {
            // Check operating hours before starting
            var (isAllowed, reason) = _operatingHours.IsWithinOperatingHours();
            if (!isAllowed)
            {
                ErrorMessage = reason ?? "לא ניתן להתחיל הפעלה מחוץ לשעות הפעילות";
                return;
            }

            if (_user.RemainingTime <= 0)
            {
                ErrorMessage = "אין לך זמן שימוש זמין. אנא רכוש חבילה.";
                return;
            }

            var result = await _session.StartSessionAsync(_user.RemainingTime);

            if (result.IsSuccess)
                IsSessionActive = true;
            else
                ErrorMessage = result.Error ?? "שגיאה";
        }
        catch (Exception ex)
        {
            Serilog.Log.Error(ex, "StartSession failed");
            ErrorMessage = "שגיאה בהתחלת הפעלה. נסה שוב.";
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand]
    private async Task EndSessionAsync()
    {
        if (!_session.IsActive || IsEndingSession) return;
        IsEndingSession = true;
        ErrorMessage = "";

        try
        {
            await _session.EndSessionAsync("user");
            IsSessionActive = false;
            UpdateStats();
        }
        catch (Exception ex)
        {
            Serilog.Log.Error(ex, "EndSession failed");
            ErrorMessage = "שגיאה בסיום הפעלה. נסה שוב.";
        }
        finally
        {
            IsEndingSession = false;
        }
    }

    [RelayCommand]
    private void ViewMessages()
    {
        if (UnreadMessages > 0)
            ViewMessagesRequested?.Invoke();
    }

    // ── Event handlers ──────────────────────────────────────────

    private void OnTimeUpdated(int remaining)
    {
        var ts = TimeSpan.FromSeconds(Math.Max(0, remaining));
        RemainingTime = ts.ToString(@"hh\:mm\:ss");
    }

    private void OnSessionStarted()
    {
        IsSessionActive = true;
    }

    private void OnSessionEnded(string reason)
    {
        IsSessionActive = false;
        RefreshUserData();
    }

    private void OnMessagesReceived(List<Dictionary<string, object?>> msgs)
    {
        UnreadMessages = msgs.Count;
    }

    // ── Helpers ─────────────────────────────────────────────────

    private void UpdateStats()
    {
        var ts = TimeSpan.FromSeconds(Math.Max(0, _user.RemainingTime));
        RemainingTime = ts.ToString(@"hh\:mm\:ss");
        PrintBalance = $"{_user.PrintBalance:F2} ₪";
    }

    /// <summary>Refresh display after session ends (remaining time may have changed).</summary>
    private void RefreshUserData()
    {
        var remaining = _session.RemainingTime;
        var ts = TimeSpan.FromSeconds(Math.Max(0, remaining));
        RemainingTime = ts.ToString(@"hh\:mm\:ss");
    }

    // ── Cleanup ─────────────────────────────────────────────────

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;

        _session.TimeUpdated -= OnTimeUpdated;
        _session.SessionStarted -= OnSessionStarted;
        _session.SessionEnded -= OnSessionEnded;
        _chat.MessagesReceived -= OnMessagesReceived;

        GC.SuppressFinalize(this);
    }
}
