using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>Message dialog ViewModel: read, next, finish flow.</summary>
public partial class MessageViewModel : ObservableObject
{
    private readonly ChatService _chat;

    [ObservableProperty] private ObservableCollection<Dictionary<string, object?>> _messages = new();
    [ObservableProperty] private int _currentIndex;
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private string _currentSender = "";
    [ObservableProperty] private string _currentBody = "";
    [ObservableProperty] private string _currentTimestamp = "";
    [ObservableProperty] private bool _hasNext;
    [ObservableProperty] private bool _hasPrevious;

    public event Action? AllMessagesRead;

    public MessageViewModel(ChatService chat)
    {
        _chat = chat;
    }

    [RelayCommand]
    private async Task LoadMessagesAsync()
    {
        IsLoading = true;
        var result = await _chat.GetUnreadMessagesAsync(useCache: false);
        IsLoading = false;

        if (result.IsSuccess && result.Data is List<Dictionary<string, object?>> messages && messages.Count > 0)
        {
            Messages = new ObservableCollection<Dictionary<string, object?>>(messages);
            CurrentIndex = 0;
            ShowMessage(0);
        }
    }

    [RelayCommand]
    private async Task NextMessageAsync()
    {
        // Mark current as read
        if (CurrentIndex < Messages.Count)
        {
            var msg = Messages[CurrentIndex];
            if (msg.TryGetValue("id", out var id) && id is string messageId)
                await _chat.MarkMessageAsReadAsync(messageId);
        }

        if (CurrentIndex < Messages.Count - 1)
        {
            CurrentIndex++;
            ShowMessage(CurrentIndex);
        }
        else
        {
            AllMessagesRead?.Invoke();
        }
    }

    [RelayCommand]
    private void PreviousMessage()
    {
        if (CurrentIndex > 0)
        {
            CurrentIndex--;
            ShowMessage(CurrentIndex);
        }
    }

    private void ShowMessage(int index)
    {
        if (index < 0 || index >= Messages.Count) return;
        var msg = Messages[index];

        CurrentSender = msg.TryGetValue("fromName", out var name) ? name?.ToString() ?? "מנהל" : "מנהל";
        CurrentBody = msg.TryGetValue("body", out var body) ? body?.ToString() ?? "" : "";
        CurrentTimestamp = msg.TryGetValue("timestamp", out var ts) ? ts?.ToString() ?? "" : "";
        HasNext = index < Messages.Count - 1;
        HasPrevious = index > 0;
    }
}
