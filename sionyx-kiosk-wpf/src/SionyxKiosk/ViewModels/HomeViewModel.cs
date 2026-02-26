using System.Collections.ObjectModel;
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
    private readonly AnnouncementService? _announcements;
    private readonly UserData _user;
    private bool _disposed;

    [ObservableProperty] private string _remainingTime = "00:00:00";
    [ObservableProperty] private string _printBalance = "0.00 ₪";
    [ObservableProperty] private string _timeExpiry = "—";
    [ObservableProperty] private int _unreadMessages;
    [ObservableProperty] private bool _isSessionActive;
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private bool _isEndingSession;
    [ObservableProperty] private string _errorMessage = "";
    [ObservableProperty] private string _welcomeMessage = "";
    [ObservableProperty] private bool _hasNoTime;
    [ObservableProperty] private string _primaryButtonText = "▶  התחל הפעלה";

    public ObservableCollection<Announcement> GlobalAnnouncements { get; } = new();
    public bool HasAnnouncements => GlobalAnnouncements.Count > 0;

    public bool IsSessionInactive => !IsSessionActive;

    /// <summary>Raised when the user wants to view unread messages.</summary>
    public event Action? ViewMessagesRequested;
    /// <summary>Raised when user clicks "buy package" button.</summary>
    public event Action? NavigateToPackagesRequested;
    /// <summary>Raised after a session is successfully started.</summary>
    public event Action? SessionStartedSuccessfully;
    /// <summary>Raised when user wants to resume an active session.</summary>
    public event Action? ResumeSessionRequested;

    partial void OnIsSessionActiveChanged(bool value)
    {
        OnPropertyChanged(nameof(IsSessionInactive));
    }

    partial void OnIsLoadingChanged(bool value)
    {
        if (!HasNoTime)
            PrimaryButtonText = value ? "מתחיל..." : "▶  התחל הפעלה";
    }

    public HomeViewModel(SessionService session, ChatService chat, OperatingHoursService operatingHours, UserData user,
        AnnouncementService? announcements = null)
    {
        _session = session;
        _chat = chat;
        _operatingHours = operatingHours;
        _announcements = announcements;
        _user = user;

        WelcomeMessage = $"שלום, {_user.FullName}!";
        IsSessionActive = _session.IsActive;
        UpdateStats();

        _session.TimeUpdated += OnTimeUpdated;
        _session.SessionStarted += OnSessionStarted;
        _session.SessionEnded += OnSessionEnded;
        _chat.MessagesReceived += OnMessagesReceived;

        _ = LoadUnreadCountAsync();
        _ = LoadAnnouncementsAsync();
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
            {
                IsSessionActive = true;
                SessionStartedSuccessfully?.Invoke();
            }
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

    [RelayCommand]
    private void BuyPackage()
    {
        NavigateToPackagesRequested?.Invoke();
    }

    [RelayCommand]
    private void ResumeSession()
    {
        ResumeSessionRequested?.Invoke();
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
        HasNoTime = _user.RemainingTime <= 0;

        if (_user.RemainingTime > 0)
        {
            var ts = TimeSpan.FromSeconds(_user.RemainingTime);
            RemainingTime = ts.ToString(@"hh\:mm\:ss");
        }
        else
        {
            RemainingTime = "—";
        }

        PrintBalance = _user.PrintBalance > 0 ? $"{_user.PrintBalance:F2} ₪" : "—";
        PrimaryButtonText = HasNoTime ? "קנה חבילה" : "▶  התחל הפעלה";
        TimeExpiry = FormatExpiry(_user.TimeExpiresAt, _user.RemainingTime);
    }

    private async Task LoadAnnouncementsAsync()
    {
        if (_announcements == null) return;
        try
        {
            var result = await _announcements.GetActiveAnnouncementsAsync();
            if (result.IsSuccess && result.Data is List<Announcement> list)
            {
                GlobalAnnouncements.Clear();
                foreach (var a in list)
                    GlobalAnnouncements.Add(a);
                OnPropertyChanged(nameof(HasAnnouncements));
            }
        }
        catch (Exception ex)
        {
            Serilog.Log.Error(ex, "Failed to load announcements");
        }
    }

    internal static string FormatExpiry(string? expiresAt, int remainingTime = -1)
    {
        if (string.IsNullOrEmpty(expiresAt) || !DateTime.TryParse(expiresAt, out var dt))
        {
            // No expiry date set: "unlimited" only makes sense if user actually has time
            return remainingTime > 0 ? "ללא הגבלה" : "אין";
        }

        var remaining = dt - DateTime.Now;
        if (remaining.TotalSeconds <= 0)
            return "פג תוקף";

        if (remaining.TotalDays >= 2)
            return $"{(int)remaining.TotalDays} ימים";
        if (remaining.TotalHours >= 1)
            return $"{(int)remaining.TotalHours} שעות";

        return $"{(int)remaining.TotalMinutes} דקות";
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
