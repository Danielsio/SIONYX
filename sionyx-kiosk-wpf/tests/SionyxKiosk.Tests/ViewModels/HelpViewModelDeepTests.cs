using FluentAssertions;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

/// <summary>
/// Deep coverage for HelpViewModel: LoadContact edge cases, CopyToClipboard paths.
/// </summary>
public class HelpViewModelDeepTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;

    public HelpViewModelDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.SetDefaultSuccess();
    }

    public void Dispose() => _firebase.Dispose();

    private HelpViewModel CreateVm()
    {
        var orgService = new OrganizationMetadataService(_firebase);
        return new HelpViewModel(orgService);
    }

    // ==================== INITIAL STATE ====================

    [Fact]
    public void InitialState_ShouldHaveDefaults()
    {
        var vm = CreateVm();
        vm.AdminPhone.Should().BeEmpty();
        vm.AdminEmail.Should().BeEmpty();
        vm.OrgName.Should().BeEmpty();
        vm.IsLoading.Should().BeFalse();
        vm.CopyFeedback.Should().BeEmpty();
    }

    [Fact]
    public void FaqItems_ShouldHaveFiveEntries()
    {
        var vm = CreateVm();
        vm.FaqItems.Should().HaveCount(5);
    }

    [Fact]
    public void FaqItems_ShouldHaveNonEmptyQuestionsAndAnswers()
    {
        var vm = CreateVm();
        foreach (var item in vm.FaqItems)
        {
            item.Question.Should().NotBeNullOrWhiteSpace();
            item.Answer.Should().NotBeNullOrWhiteSpace();
        }
    }

    // ==================== LOAD CONTACT ====================

    [Fact]
    public async Task LoadContactCommand_WithFullData_ShouldPopulateAll()
    {
        // The service reads admin_phone and admin_email from Firebase metadata
        _handler.When("metadata.json", new
        {
            admin_phone = "050-1234567",
            admin_email = "admin@test.com",
            name = "Test Org",
        });

        var vm = CreateVm();
        await vm.LoadContactCommand.ExecuteAsync(null);

        vm.AdminPhone.Should().Be("050-1234567");
        vm.AdminEmail.Should().Be("admin@test.com");
        vm.OrgName.Should().Be("Test Org");
    }

    [Fact]
    public async Task LoadContactCommand_WhenServiceFails_ShouldNotThrow()
    {
        _handler.WhenError("metadata");

        var vm = CreateVm();

        var act = async () => await vm.LoadContactCommand.ExecuteAsync(null);
        await act.Should().NotThrowAsync();
    }

    [Fact]
    public async Task LoadContactCommand_ShouldSetIsLoadingDuringCall()
    {
        _handler.WhenRaw("metadata.json", "null");

        var vm = CreateVm();
        var loadingStates = new List<bool>();
        vm.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == "IsLoading")
                loadingStates.Add(vm.IsLoading);
        };

        await vm.LoadContactCommand.ExecuteAsync(null);

        loadingStates.Should().Contain(true);
        loadingStates.Should().Contain(false);
    }

    [Fact]
    public async Task LoadContactCommand_WithNullResponse_ShouldLeaveFieldsEmpty()
    {
        _handler.WhenRaw("metadata.json", "null");

        var vm = CreateVm();
        await vm.LoadContactCommand.ExecuteAsync(null);

        vm.AdminPhone.Should().BeEmpty();
        vm.AdminEmail.Should().BeEmpty();
        vm.OrgName.Should().BeEmpty();
    }

    // ==================== COPY TO CLIPBOARD ====================

    [Fact]
    public async Task CopyToClipboardCommand_WithNullText_ShouldNotSetFeedback()
    {
        var vm = CreateVm();
        await vm.CopyToClipboardCommand.ExecuteAsync(null!);
        vm.CopyFeedback.Should().BeEmpty();
    }

    [Fact]
    public async Task CopyToClipboardCommand_WithEmptyText_ShouldNotSetFeedback()
    {
        var vm = CreateVm();
        await vm.CopyToClipboardCommand.ExecuteAsync("");
        vm.CopyFeedback.Should().BeEmpty();
    }

    [Fact]
    public async Task CopyToClipboardCommand_WithWhitespace_ShouldNotSetFeedback()
    {
        var vm = CreateVm();
        await vm.CopyToClipboardCommand.ExecuteAsync("   ");
        vm.CopyFeedback.Should().BeEmpty();
    }

    // Note: Clipboard.SetText requires STA thread and WPF, so we can't test
    // the success path in a unit test. But the guard clauses are covered.

    // ==================== PROPERTY CHANGED ====================

    [Fact]
    public void AdminPhone_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.AdminPhone = "050-9999999";
        changed.Should().Contain("AdminPhone");
    }

    [Fact]
    public void AdminEmail_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.AdminEmail = "new@email.com";
        changed.Should().Contain("AdminEmail");
    }

    [Fact]
    public void OrgName_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.OrgName = "New Org Name";
        changed.Should().Contain("OrgName");
    }

    [Fact]
    public void CopyFeedback_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.CopyFeedback = "Copied!";
        changed.Should().Contain("CopyFeedback");
    }
}
