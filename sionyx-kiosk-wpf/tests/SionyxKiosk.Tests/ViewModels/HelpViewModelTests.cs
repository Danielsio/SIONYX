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
        var vm = new HelpViewModel(orgService);

        vm.FaqItems.Should().NotBeEmpty();
        vm.FaqItems.Count.Should().BeGreaterThanOrEqualTo(5);
    }

    [Fact]
    public void FaqItems_AllShouldHaveQuestionAndAnswer()
    {
        var orgService = new OrganizationMetadataService(null!);
        var vm = new HelpViewModel(orgService);

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
        var vm = new HelpViewModel(orgService);

        vm.AdminPhone.Should().BeEmpty();
        vm.AdminEmail.Should().BeEmpty();
        vm.OrgName.Should().BeEmpty();
        vm.IsLoading.Should().BeFalse();
    }
}
