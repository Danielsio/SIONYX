using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

/// <summary>
/// Deep coverage for PaymentViewModel: init edge cases, processing states.
/// </summary>
public class PaymentViewModelDeepTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;

    public PaymentViewModelDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.SetDefaultSuccess();
    }

    public void Dispose() => _firebase.Dispose();

    private PaymentViewModel CreateVm()
    {
        var purchaseService = new PurchaseService(_firebase);
        return new PaymentViewModel(purchaseService, "user-123");
    }

    // ==================== INITIAL STATE ====================

    [Fact]
    public void InitialState_ShouldHaveDefaults()
    {
        var vm = CreateVm();
        vm.Package.Should().BeNull();
        vm.PurchaseId.Should().BeEmpty();
        vm.IsProcessing.Should().BeFalse();
        vm.Status.Should().Be("pending");
        vm.ErrorMessage.Should().BeEmpty();
    }

    // ==================== INIT PAYMENT ====================

    [Fact]
    public async Task InitPaymentCommand_ShouldSetPackage()
    {
        var package = new Package { Id = "pkg1", Name = "Basic", Price = 29.90 };
        var vm = CreateVm();

        await vm.InitPaymentCommand.ExecuteAsync(package);

        vm.Package.Should().NotBeNull();
        vm.Package!.Name.Should().Be("Basic");
    }

    [Fact]
    public async Task InitPaymentCommand_ShouldSetIsProcessing()
    {
        var package = new Package { Id = "pkg1", Name = "Basic", Price = 29.90 };
        var vm = CreateVm();

        bool wasProcessing = false;
        vm.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == "IsProcessing" && vm.IsProcessing)
                wasProcessing = true;
        };

        await vm.InitPaymentCommand.ExecuteAsync(package);

        wasProcessing.Should().BeTrue();
    }

    [Fact]
    public async Task InitPaymentCommand_WhenServiceFails_ShouldSetError()
    {
        _handler.WhenError("purchases");
        var package = new Package { Id = "pkg1", Name = "Basic", Price = 29.90 };
        var vm = CreateVm();

        await vm.InitPaymentCommand.ExecuteAsync(package);

        vm.ErrorMessage.Should().NotBeNullOrEmpty();
        vm.Status.Should().Be("failed");
        vm.IsProcessing.Should().BeFalse();
    }

    // ==================== COMPLETE PAYMENT ====================

    [Fact]
    public void CompletePaymentCommand_WithSuccess_ShouldSetStatusSuccess()
    {
        var vm = CreateVm();
        vm.CompletePaymentCommand.Execute(true);

        vm.Status.Should().Be("success");
        vm.IsProcessing.Should().BeFalse();
    }

    [Fact]
    public void CompletePaymentCommand_WithFailure_ShouldSetStatusFailed()
    {
        var vm = CreateVm();
        vm.CompletePaymentCommand.Execute(false);

        vm.Status.Should().Be("failed");
        vm.IsProcessing.Should().BeFalse();
    }

    [Fact]
    public void CompletePaymentCommand_ShouldFirePaymentCompletedEvent()
    {
        var vm = CreateVm();
        bool? completedSuccess = null;
        vm.PaymentCompleted += success => completedSuccess = success;

        vm.CompletePaymentCommand.Execute(true);

        completedSuccess.Should().BeTrue();
    }

    [Fact]
    public void CompletePaymentCommand_WithFailed_ShouldFirePaymentCompletedEvent()
    {
        var vm = CreateVm();
        bool? completedSuccess = null;
        vm.PaymentCompleted += success => completedSuccess = success;

        vm.CompletePaymentCommand.Execute(false);

        completedSuccess.Should().BeFalse();
    }

    // ==================== PROPERTY CHANGED ====================

    [Fact]
    public void Status_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.Status = "success";
        changed.Should().Contain("Status");
    }

    [Fact]
    public void ErrorMessage_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.ErrorMessage = "Payment failed";
        changed.Should().Contain("ErrorMessage");
    }

    [Fact]
    public void PurchaseId_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.PurchaseId = "purchase-123";
        changed.Should().Contain("PurchaseId");
    }

    [Fact]
    public void Package_ShouldNotifyPropertyChanged()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.Package = new Package { Id = "p1", Name = "Test" };
        changed.Should().Contain("Package");
    }
}
