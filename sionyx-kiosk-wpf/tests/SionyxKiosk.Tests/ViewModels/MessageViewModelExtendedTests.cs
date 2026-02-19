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
            msg1 = new { toUserId = "user-123", body = "Hello!", fromName = "Admin", read = false, timestamp = 1700000000000 },
            msg2 = new { toUserId = "user-123", body = "Second message", fromName = "Manager", read = false, timestamp = 1700000001000 },
        });

        await _vm.LoadMessagesCommand.ExecuteAsync(null);

        _vm.Messages.Count.Should().Be(2);
        _vm.IsEmpty.Should().BeFalse();
        _vm.Messages[0].DisplaySender.Should().Be("Admin");
        _vm.Messages[0].DisplayBody.Should().Be("Hello!");
        _vm.Messages[1].DisplaySender.Should().Be("Manager");
        _vm.Messages[1].DisplayBody.Should().Be("Second message");
    }

    [Fact]
    public async Task LoadMessagesCommand_WhenEmpty_ShouldSetEmptyState()
    {
        _handler.WhenRaw("messages.json", "null");

        await _vm.LoadMessagesCommand.ExecuteAsync(null);

        _vm.Messages.Count.Should().Be(0);
        _vm.IsEmpty.Should().BeTrue();
    }

    [Fact]
    public async Task LoadMessagesCommand_ShouldOrderByTimestamp()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "Later", fromName = "Admin", read = false, timestamp = 1700000002000 },
            msg2 = new { toUserId = "user-123", body = "Earlier", fromName = "Admin", read = false, timestamp = 1700000000000 },
        });

        await _vm.LoadMessagesCommand.ExecuteAsync(null);

        _vm.Messages[0].DisplayBody.Should().Be("Earlier");
        _vm.Messages[1].DisplayBody.Should().Be("Later");
    }

    [Fact]
    public async Task LoadMessagesCommand_WithMissingFromName_ShouldDefaultToAdmin()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "Hello", read = false, timestamp = 1700000000000 },
        });

        await _vm.LoadMessagesCommand.ExecuteAsync(null);

        _vm.Messages[0].DisplaySender.Should().Be("מנהל");
    }

    [Fact]
    public async Task MarkAllReadAndClose_ShouldFireAllMessagesRead()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "Test", fromName = "Admin", read = false, timestamp = 1700000000000 },
        });
        _handler.SetDefaultSuccess();

        await _vm.LoadMessagesCommand.ExecuteAsync(null);

        var allRead = false;
        _vm.AllMessagesRead += () => allRead = true;

        await _vm.MarkAllReadAndCloseAsync();
        allRead.Should().BeTrue();
    }

    [Fact]
    public void PropertyChanged_ShouldFire()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        _vm.IsLoading = true;
        _vm.IsEmpty = true;

        changed.Should().Contain("IsLoading");
        changed.Should().Contain("IsEmpty");
    }
}
