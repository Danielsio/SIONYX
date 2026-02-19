using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>Display-friendly wrapper for a chat message.</summary>
public class MessageItem
{
    public string Id { get; init; } = "";
    public string DisplaySender { get; init; } = "מנהל";
    public string DisplayBody { get; init; } = "";
    public string DisplayTime { get; init; } = "";
    public long RawTimestamp { get; init; }

    public static MessageItem FromDictionary(Dictionary<string, object?> msg)
    {
        var sender = msg.TryGetValue("fromName", out var name) ? name?.ToString() ?? "" : "";
        if (string.IsNullOrWhiteSpace(sender)) sender = "מנהל";

        var body = msg.TryGetValue("body", out var b) ? b?.ToString() ?? "" : "";
        if (string.IsNullOrEmpty(body) && msg.TryGetValue("message", out var m))
            body = m?.ToString() ?? "";
        var id = msg.TryGetValue("id", out var mid) ? mid?.ToString() ?? "" : "";

        long rawTs = 0;
        var timeDisplay = "";
        if (msg.TryGetValue("timestamp", out var ts))
        {
            if (ts is double d) rawTs = (long)d;
            else if (ts is string s && long.TryParse(s, out var parsed)) rawTs = parsed;

            if (rawTs > 0)
            {
                var dt = DateTimeOffset.FromUnixTimeMilliseconds(rawTs).LocalDateTime;
                var now = DateTime.Now;
                timeDisplay = dt.Date == now.Date
                    ? dt.ToString("HH:mm")
                    : dt.Date == now.Date.AddDays(-1)
                        ? $"אתמול {dt:HH:mm}"
                        : dt.ToString("dd/MM HH:mm");
            }
        }

        return new MessageItem
        {
            Id = id,
            DisplaySender = sender,
            DisplayBody = body,
            DisplayTime = timeDisplay,
            RawTimestamp = rawTs,
        };
    }
}

/// <summary>Message dialog ViewModel: loads unread messages, mark all read.</summary>
public partial class MessageViewModel : ObservableObject
{
    private readonly ChatService _chat;

    [ObservableProperty] private ObservableCollection<MessageItem> _messages = new();
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private bool _isEmpty;

    public event Action? AllMessagesRead;

    public MessageViewModel(ChatService chat)
    {
        _chat = chat;
    }

    [RelayCommand]
    private async Task LoadMessagesAsync()
    {
        IsLoading = true;
        IsEmpty = false;

        try
        {
            var result = await _chat.GetUnreadMessagesAsync(useCache: false);

            if (result.IsSuccess && result.Data is List<Dictionary<string, object?>> rawMessages && rawMessages.Count > 0)
            {
                var items = rawMessages
                    .Select(MessageItem.FromDictionary)
                    .OrderBy(m => m.RawTimestamp)
                    .ToList();

                Messages = new ObservableCollection<MessageItem>(items);
            }
            else
            {
                Messages = new ObservableCollection<MessageItem>();
                IsEmpty = true;
            }
        }
        catch (Exception ex)
        {
            Serilog.Log.Error(ex, "Failed to load messages");
            Messages = new ObservableCollection<MessageItem>();
            IsEmpty = true;
        }
        finally
        {
            IsLoading = false;
        }
    }

    public async Task MarkAllReadAndCloseAsync()
    {
        try
        {
            await _chat.MarkAllMessagesAsReadAsync();
        }
        catch (Exception ex)
        {
            Serilog.Log.Error(ex, "Failed to mark messages as read");
        }

        AllMessagesRead?.Invoke();
    }
}
