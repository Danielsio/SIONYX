using FluentAssertions;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class MessageViewModelTests
{
    [Fact]
    public void InitialState_ShouldBeEmpty()
    {
        var chatService = new ChatService(null!, "test-user-123");
        var vm = new MessageViewModel(chatService);

        vm.Messages.Should().BeEmpty();
        vm.CurrentIndex.Should().Be(0);
        vm.IsLoading.Should().BeFalse();
        vm.CurrentSender.Should().BeEmpty();
        vm.CurrentBody.Should().BeEmpty();
        vm.HasNext.Should().BeFalse();
        vm.HasPrevious.Should().BeFalse();
    }

    [Fact]
    public void PreviousMessage_AtStart_ShouldNotGoNegative()
    {
        var chatService = new ChatService(null!, "test-user-123");
        var vm = new MessageViewModel(chatService);

        vm.PreviousMessageCommand.Execute(null);
        vm.CurrentIndex.Should().Be(0);
    }
}
