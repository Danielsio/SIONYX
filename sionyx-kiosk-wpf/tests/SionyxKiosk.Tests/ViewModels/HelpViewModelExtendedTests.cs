using FluentAssertions;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class HelpViewModelExtendedTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly HelpViewModel _vm;

    public HelpViewModelExtendedTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        var orgService = new OrganizationMetadataService(_firebase);
        _vm = new HelpViewModel(orgService);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public async Task LoadContactCommand_WithData_ShouldPopulateFields()
    {
        _handler.When("metadata.json", new
        {
            admin_phone = "0501234567",
            admin_email = "admin@test.com",
            name = "Test Organization",
        });

        await _vm.LoadContactCommand.ExecuteAsync(null);

        _vm.AdminPhone.Should().Be("0501234567");
        _vm.AdminEmail.Should().Be("admin@test.com");
        _vm.OrgName.Should().Be("Test Organization");
        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public async Task LoadContactCommand_WhenFails_ShouldNotThrow()
    {
        _handler.WhenError("metadata.json");

        await _vm.LoadContactCommand.ExecuteAsync(null);

        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public void PropertyChanged_ShouldFire()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        _vm.AdminPhone = "123";
        _vm.AdminEmail = "test@test.com";
        _vm.OrgName = "Org";
        _vm.IsLoading = true;

        changed.Should().Contain("AdminPhone");
        changed.Should().Contain("AdminEmail");
        changed.Should().Contain("OrgName");
        changed.Should().Contain("IsLoading");
    }

    [Fact]
    public void FaqItems_ShouldContainExpectedTopics()
    {
        var questions = _vm.FaqItems.Select(f => f.Question).ToList();
        // Should have FAQ about starting session, purchasing, printing, etc.
        questions.Should().Contain(q => q.Contains("הפעלה"));
        questions.Should().Contain(q => q.Contains("חבילה"));
        questions.Should().Contain(q => q.Contains("דפ"));
    }
}
