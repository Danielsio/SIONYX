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
        vm.IsLoading.Should().BeFalse();
        vm.IsEmpty.Should().BeFalse();
    }
}
