using FluentAssertions;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

/// <summary>
/// Deep coverage for MessageViewModel: load failure, ShowMessage edge cases,
/// HasNext/HasPrevious, mark-as-read.
/// </summary>
public class MessageViewModelDeepTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;

    public MessageViewModelDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.SetDefaultSuccess();
    }

    public void Dispose() => _firebase.Dispose();

    private MessageViewModel CreateVm()
    {
        var chat = new ChatService(_firebase, "user-123");
        return new MessageViewModel(chat);
    }

    // ==================== INITIAL STATE ====================

    [Fact]
    public void InitialState_ShouldHaveDefaults()
    {
        var vm = CreateVm();
        vm.Messages.Should().BeEmpty();
        vm.CurrentIndex.Should().Be(0);
        vm.IsLoading.Should().BeFalse();
        vm.CurrentSender.Should().BeEmpty();
        vm.CurrentBody.Should().BeEmpty();
        vm.CurrentTimestamp.Should().BeEmpty();
        vm.HasNext.Should().BeFalse();
        vm.HasPrevious.Should().BeFalse();
    }

    // ==================== LOAD MESSAGES ====================

    [Fact]
    public async Task LoadMessagesCommand_WhenServiceFails_ShouldNotPopulate()
    {
        _handler.WhenError("messages");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        vm.Messages.Should().BeEmpty();
    }

    [Fact]
    public async Task LoadMessagesCommand_WhenNoMessages_ShouldNotPopulate()
    {
        _handler.WhenRaw("messages.json", "null");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        vm.Messages.Should().BeEmpty();
    }

    [Fact]
    public async Task LoadMessagesCommand_WithMessages_ShouldPopulate()
    {
        _handler.WhenRaw("messages.json", @"{
            ""msg1"": { ""toUserId"": ""user-123"", ""message"": ""Hello"", ""read"": false, ""timestamp"": 1700000000000 },
            ""msg2"": { ""toUserId"": ""user-123"", ""message"": ""World"", ""read"": false, ""timestamp"": 1700000001000 }
        }");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        vm.Messages.Should().HaveCount(2);
    }

    [Fact]
    public async Task LoadMessagesCommand_ShouldSetIsLoading()
    {
        _handler.WhenRaw("messages.json", "null");
        var vm = CreateVm();

        var loadingStates = new List<bool>();
        vm.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == "IsLoading")
                loadingStates.Add(vm.IsLoading);
        };

        await vm.LoadMessagesCommand.ExecuteAsync(null);

        loadingStates.Should().Contain(true);
        loadingStates.Should().Contain(false);
    }

    [Fact]
    public async Task LoadMessagesCommand_SingleMessage_HasNextShouldBeFalse()
    {
        _handler.WhenRaw("messages.json", @"{
            ""msg1"": { ""toUserId"": ""user-123"", ""message"": ""Solo"", ""read"": false, ""timestamp"": 1700000000000 }
        }");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        vm.Messages.Should().HaveCount(1);
        vm.HasNext.Should().BeFalse();
        vm.HasPrevious.Should().BeFalse();
    }

    // ==================== NAVIGATION ====================

    [Fact]
    public async Task NextMessageCommand_WithMultipleMessages_ShouldAdvance()
    {
        _handler.WhenRaw("messages.json", @"{
            ""msg1"": { ""toUserId"": ""user-123"", ""message"": ""First"", ""read"": false, ""timestamp"": 1700000000000 },
            ""msg2"": { ""toUserId"": ""user-123"", ""message"": ""Second"", ""read"": false, ""timestamp"": 1700000001000 }
        }");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        vm.CurrentIndex.Should().Be(0);
        vm.HasNext.Should().BeTrue();

        await vm.NextMessageCommand.ExecuteAsync(null);
        vm.CurrentIndex.Should().Be(1);
        vm.HasPrevious.Should().BeTrue();
        vm.HasNext.Should().BeFalse();
    }

    [Fact]
    public async Task NextMessageCommand_AtLastMessage_ShouldFireAllMessagesRead()
    {
        _handler.WhenRaw("messages.json", @"{
            ""msg1"": { ""toUserId"": ""user-123"", ""message"": ""Only"", ""read"": false, ""timestamp"": 1700000000000 }
        }");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        bool allRead = false;
        vm.AllMessagesRead += () => allRead = true;

        await vm.NextMessageCommand.ExecuteAsync(null);
        allRead.Should().BeTrue();
    }

    [Fact]
    public void PreviousMessageCommand_AtFirstMessage_ShouldNotMove()
    {
        var vm = CreateVm();
        vm.CurrentIndex.Should().Be(0);

        vm.PreviousMessageCommand.Execute(null);
        vm.CurrentIndex.Should().Be(0);
    }

    // ==================== SHOW MESSAGE EDGE CASES ====================

    [Fact]
    public async Task ShowMessage_WithMissingFromName_ShouldDefaultToAdmin()
    {
        _handler.WhenRaw("messages.json", @"{
            ""msg1"": { ""toUserId"": ""user-123"", ""body"": ""Test body"", ""read"": false, ""timestamp"": 1700000000000 }
        }");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        vm.CurrentSender.Should().Be("מנהל");
    }

    [Fact]
    public async Task ShowMessage_WithTimestamp_ShouldDisplayTimestamp()
    {
        _handler.WhenRaw("messages.json", @"{
            ""msg1"": { ""toUserId"": ""user-123"", ""message"": ""Test"", ""read"": false, ""timestamp"": 1700000000000 }
        }");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        vm.CurrentTimestamp.Should().NotBeNull();
    }

    // ==================== PROPERTY CHANGED ====================

    [Fact]
    public void CurrentSender_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.CurrentSender = "Admin";
        changed.Should().Contain("CurrentSender");
    }

    [Fact]
    public void CurrentBody_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.CurrentBody = "Hello world";
        changed.Should().Contain("CurrentBody");
    }

    [Fact]
    public void HasNext_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.HasNext = true;
        changed.Should().Contain("HasNext");
    }

    [Fact]
    public void HasPrevious_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.HasPrevious = true;
        changed.Should().Contain("HasPrevious");
    }
}
