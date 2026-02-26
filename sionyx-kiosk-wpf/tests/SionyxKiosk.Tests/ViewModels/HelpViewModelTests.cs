using FluentAssertions;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class HelpViewModelTests
{
    [Fact]
    public void FaqItems_ShouldHaveDefaultEntries()
    {
        var orgService = new OrganizationMetadataService(null!);
        var opHours = new OperatingHoursService(null!);
        var vm = new HelpViewModel(orgService, opHours);

        vm.FaqItems.Should().NotBeEmpty();
        vm.FaqItems.Count.Should().BeGreaterThanOrEqualTo(5);
    }

    [Fact]
    public void FaqItems_AllShouldHaveQuestionAndAnswer()
    {
        var orgService = new OrganizationMetadataService(null!);
        var opHours = new OperatingHoursService(null!);
        var vm = new HelpViewModel(orgService, opHours);

        foreach (var item in vm.FaqItems)
        {
            item.Question.Should().NotBeNullOrWhiteSpace();
            item.Answer.Should().NotBeNullOrWhiteSpace();
        }
    }

    [Fact]
    public void InitialState_ShouldHaveEmptyContact()
    {
        var orgService = new OrganizationMetadataService(null!);
        var opHours = new OperatingHoursService(null!);
        var vm = new HelpViewModel(orgService, opHours);

        vm.AdminPhone.Should().BeEmpty();
        vm.AdminEmail.Should().BeEmpty();
        vm.OrgName.Should().BeEmpty();
        vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public void InitialState_ShouldHaveEmptyFeedback()
    {
        var orgService = new OrganizationMetadataService(null!);
        var opHours = new OperatingHoursService(null!);
        var vm = new HelpViewModel(orgService, opHours);

        vm.FeedbackText.Should().BeEmpty();
        vm.FeedbackStatus.Should().BeEmpty();
    }

    [Fact]
    public async Task SendFeedback_WithEmptyText_ShouldShowError()
    {
        var orgService = new OrganizationMetadataService(null!);
        var opHours = new OperatingHoursService(null!);
        var vm = new HelpViewModel(orgService, opHours);

        vm.FeedbackText = "";
        await vm.SendFeedbackCommand.ExecuteAsync(null);

        vm.FeedbackStatus.Should().Contain("אנא כתוב הודעה");
    }

    [Fact]
    public async Task SendFeedback_WithWhitespace_ShouldShowError()
    {
        var orgService = new OrganizationMetadataService(null!);
        var opHours = new OperatingHoursService(null!);
        var vm = new HelpViewModel(orgService, opHours);

        vm.FeedbackText = "   ";
        await vm.SendFeedbackCommand.ExecuteAsync(null);

        vm.FeedbackStatus.Should().Contain("אנא כתוב הודעה");
    }
}
