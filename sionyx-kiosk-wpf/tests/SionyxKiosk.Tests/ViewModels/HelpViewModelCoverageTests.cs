using FluentAssertions;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class HelpViewModelCoverageTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly HelpViewModel _vm;

    public HelpViewModelCoverageTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        var orgService = new OrganizationMetadataService(_firebase);
        _vm = new HelpViewModel(orgService);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public void FaqItems_HasExpectedCount()
    {
        _vm.FaqItems.Should().HaveCount(5);
    }

    [Fact]
    public void FaqItems_FirstQuestion_IsAboutStarting()
    {
        _vm.FaqItems[0].Question.Should().Contain("מתחילים");
    }

    [Fact]
    public void InitialState_ContactFieldsEmpty()
    {
        _vm.AdminPhone.Should().BeEmpty();
        _vm.AdminEmail.Should().BeEmpty();
        _vm.OrgName.Should().BeEmpty();
    }

    [Fact]
    public void InitialState_CopyFeedbackEmpty()
    {
        _vm.CopyFeedback.Should().BeEmpty();
    }

    [Fact]
    public void InitialState_IsLoadingFalse()
    {
        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public async Task LoadContactCommand_WithData_SetsFields()
    {
        _handler.When("metadata.json", new
        {
            admin_phone = "050-1234567",
            admin_email = "admin@test.com",
            name = "Test Org"
        });

        await _vm.LoadContactCommand.ExecuteAsync(null);

        _vm.AdminPhone.Should().Be("050-1234567");
        _vm.AdminEmail.Should().Be("admin@test.com");
        _vm.OrgName.Should().Be("Test Org");
        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public async Task LoadContactCommand_WhenFails_FieldsStayEmpty()
    {
        _handler.WhenError("metadata.json");

        await _vm.LoadContactCommand.ExecuteAsync(null);

        _vm.AdminPhone.Should().BeEmpty();
        _vm.AdminEmail.Should().BeEmpty();
        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public void PropertyChanged_FiresForFields()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        _vm.AdminPhone = "123";
        _vm.AdminEmail = "a@b";
        _vm.OrgName = "Test";
        _vm.IsLoading = true;
        _vm.CopyFeedback = "done";

        changed.Should().Contain("AdminPhone");
        changed.Should().Contain("AdminEmail");
        changed.Should().Contain("OrgName");
        changed.Should().Contain("IsLoading");
        changed.Should().Contain("CopyFeedback");
    }
}
