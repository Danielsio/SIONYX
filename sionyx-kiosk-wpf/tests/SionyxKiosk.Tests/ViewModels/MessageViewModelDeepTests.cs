using FluentAssertions;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

/// <summary>
/// Deep coverage for MessageViewModel and MessageItem.
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

    [Fact]
    public void InitialState_ShouldHaveDefaults()
    {
        var vm = CreateVm();
        vm.Messages.Should().BeEmpty();
        vm.IsLoading.Should().BeFalse();
        vm.IsEmpty.Should().BeFalse();
    }

    [Fact]
    public async Task LoadMessagesCommand_WhenServiceFails_ShouldSetEmpty()
    {
        _handler.WhenError("messages");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        vm.Messages.Should().BeEmpty();
        vm.IsEmpty.Should().BeTrue();
    }

    [Fact]
    public async Task LoadMessagesCommand_WhenNoMessages_ShouldSetEmpty()
    {
        _handler.WhenRaw("messages.json", "null");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        vm.Messages.Should().BeEmpty();
        vm.IsEmpty.Should().BeTrue();
    }

    [Fact]
    public async Task LoadMessagesCommand_WithMessages_ShouldPopulate()
    {
        _handler.WhenRaw("messages.json", @"{
            ""msg1"": { ""toUserId"": ""user-123"", ""body"": ""Hello"", ""read"": false, ""timestamp"": 1700000000000 },
            ""msg2"": { ""toUserId"": ""user-123"", ""body"": ""World"", ""read"": false, ""timestamp"": 1700000001000 }
        }");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        vm.Messages.Should().HaveCount(2);
        vm.IsEmpty.Should().BeFalse();
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
    public async Task LoadMessagesCommand_SingleMessage_ShouldShowOne()
    {
        _handler.WhenRaw("messages.json", @"{
            ""msg1"": { ""toUserId"": ""user-123"", ""body"": ""Solo"", ""read"": false, ""timestamp"": 1700000000000 }
        }");

        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        vm.Messages.Should().HaveCount(1);
        vm.Messages[0].DisplayBody.Should().Be("Solo");
    }

    [Fact]
    public async Task MarkAllReadAndClose_WhenNoMessages_ShouldNotThrow()
    {
        _handler.WhenRaw("messages.json", "null");
        var vm = CreateVm();
        await vm.LoadMessagesCommand.ExecuteAsync(null);

        var allRead = false;
        vm.AllMessagesRead += () => allRead = true;

        await vm.MarkAllReadAndCloseAsync();
        allRead.Should().BeTrue();
    }

    [Fact]
    public void IsEmpty_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.IsEmpty = true;
        changed.Should().Contain("IsEmpty");
    }

    [Fact]
    public void IsLoading_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.IsLoading = true;
        changed.Should().Contain("IsLoading");
    }
}
