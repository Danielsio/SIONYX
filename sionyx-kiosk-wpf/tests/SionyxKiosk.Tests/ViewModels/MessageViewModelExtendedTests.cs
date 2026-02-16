using System.Collections.ObjectModel;
using FluentAssertions;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class MessageViewModelExtendedTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly MessageViewModel _vm;

    public MessageViewModelExtendedTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        var chatService = new ChatService(_firebase, "user-123");
        _vm = new MessageViewModel(chatService);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public async Task LoadMessagesCommand_WithMessages_ShouldPopulate()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "Hello!", fromName = "Admin", read = false, timestamp = "2026-01-01T10:00:00" },
            msg2 = new { toUserId = "user-123", body = "Second message", fromName = "Manager", read = false, timestamp = "2026-01-02T10:00:00" },
        });

        await _vm.LoadMessagesCommand.ExecuteAsync(null);

        _vm.Messages.Count.Should().Be(2);
        _vm.CurrentSender.Should().Be("Admin");
        _vm.CurrentBody.Should().Be("Hello!");
        _vm.HasNext.Should().BeTrue();
        _vm.HasPrevious.Should().BeFalse();
    }

    [Fact]
    public async Task LoadMessagesCommand_WhenEmpty_ShouldNotSet()
    {
        _handler.WhenRaw("messages.json", "null");

        await _vm.LoadMessagesCommand.ExecuteAsync(null);

        _vm.Messages.Count.Should().Be(0);
    }

    [Fact]
    public async Task NextMessageCommand_ShouldAdvance()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "First", fromName = "Admin", read = false, timestamp = "2026-01-01" },
            msg2 = new { toUserId = "user-123", body = "Second", fromName = "Manager", read = false, timestamp = "2026-01-02" },
        });
        _handler.SetDefaultSuccess(); // For mark as read

        await _vm.LoadMessagesCommand.ExecuteAsync(null);
        await _vm.NextMessageCommand.ExecuteAsync(null);

        _vm.CurrentIndex.Should().Be(1);
        _vm.CurrentBody.Should().Be("Second");
        _vm.HasPrevious.Should().BeTrue();
        _vm.HasNext.Should().BeFalse();
    }

    [Fact]
    public async Task NextMessageCommand_AtEnd_ShouldFireAllMessagesRead()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "Only", fromName = "Admin", read = false, timestamp = "2026-01-01" },
        });
        _handler.SetDefaultSuccess();

        await _vm.LoadMessagesCommand.ExecuteAsync(null);

        var allRead = false;
        _vm.AllMessagesRead += () => allRead = true;

        await _vm.NextMessageCommand.ExecuteAsync(null);
        allRead.Should().BeTrue();
    }

    [Fact]
    public async Task PreviousMessageCommand_ShouldGoBack()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "First", fromName = "Admin", read = false, timestamp = "2026-01-01" },
            msg2 = new { toUserId = "user-123", body = "Second", fromName = "Admin", read = false, timestamp = "2026-01-02" },
        });
        _handler.SetDefaultSuccess();

        await _vm.LoadMessagesCommand.ExecuteAsync(null);
        await _vm.NextMessageCommand.ExecuteAsync(null);

        _vm.PreviousMessageCommand.Execute(null);
        _vm.CurrentIndex.Should().Be(0);
        _vm.CurrentBody.Should().Be("First");
    }

    [Fact]
    public void PreviousMessageCommand_AtStart_ShouldStay()
    {
        _vm.PreviousMessageCommand.Execute(null);
        _vm.CurrentIndex.Should().Be(0);
    }

    [Fact]
    public async Task ShowMessage_ShouldDisplayTimestamp()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "Hello", fromName = "Admin", read = false, timestamp = "2026-01-15T14:30:00" },
        });

        await _vm.LoadMessagesCommand.ExecuteAsync(null);
        _vm.CurrentTimestamp.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public async Task ShowMessage_WithMissingFromName_ShouldDefaultToAdmin()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "Hello", read = false, timestamp = "2026-01-01" },
        });

        await _vm.LoadMessagesCommand.ExecuteAsync(null);
        _vm.CurrentSender.Should().Be("מנהל");
    }

    [Fact]
    public void PropertyChanged_ShouldFire()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        _vm.IsLoading = true;
        _vm.CurrentSender = "test";
        _vm.CurrentBody = "body";
        _vm.CurrentTimestamp = "ts";
        _vm.HasNext = true;
        _vm.HasPrevious = true;
        _vm.CurrentIndex = 5;

        changed.Should().Contain("IsLoading");
        changed.Should().Contain("CurrentSender");
        changed.Should().Contain("CurrentBody");
        changed.Should().Contain("CurrentTimestamp");
        changed.Should().Contain("HasNext");
        changed.Should().Contain("HasPrevious");
        changed.Should().Contain("CurrentIndex");
    }
}
