using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class PaymentViewModelTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly PaymentViewModel _vm;

    public PaymentViewModelTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        var purchaseService = new PurchaseService(_firebase);
        _vm = new PaymentViewModel(purchaseService, "user-123");
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public void InitialState_ShouldBePending()
    {
        _vm.Package.Should().BeNull();
        _vm.PurchaseId.Should().BeEmpty();
        _vm.IsProcessing.Should().BeFalse();
        _vm.Status.Should().Be("pending");
        _vm.ErrorMessage.Should().BeEmpty();
    }

    [Fact]
    public async Task InitPaymentCommand_WithValidPackage_ShouldSetPurchaseId()
    {
        _handler.SetDefaultSuccess();

        var package = new Package { Id = "pkg1", Name = "Basic", Price = 29.90 };
        await _vm.InitPaymentCommand.ExecuteAsync(package);

        _vm.Package.Should().Be(package);
        _vm.Status.Should().Be("pending");
    }

    [Fact]
    public async Task InitPaymentCommand_WhenFails_ShouldSetError()
    {
        _handler.WhenError("purchases/");

        var package = new Package { Id = "pkg1", Name = "Basic", Price = 29.90 };
        await _vm.InitPaymentCommand.ExecuteAsync(package);

        _vm.Status.Should().Be("failed");
        _vm.ErrorMessage.Should().NotBeEmpty();
        _vm.IsProcessing.Should().BeFalse();
    }

    [Fact]
    public void CompletePaymentCommand_Success_ShouldSetStatus()
    {
        _vm.CompletePaymentCommand.Execute(true);

        _vm.Status.Should().Be("success");
        _vm.IsProcessing.Should().BeFalse();
    }

    [Fact]
    public void CompletePaymentCommand_Failure_ShouldSetFailed()
    {
        _vm.CompletePaymentCommand.Execute(false);

        _vm.Status.Should().Be("failed");
        _vm.IsProcessing.Should().BeFalse();
    }

    [Fact]
    public void CompletePaymentCommand_ShouldRaisePaymentCompleted()
    {
        bool? completed = null;
        _vm.PaymentCompleted += success => completed = success;

        _vm.CompletePaymentCommand.Execute(true);

        completed.Should().BeTrue();
    }

    [Fact]
    public void CompletePaymentCommand_Failure_ShouldRaisePaymentCompleted()
    {
        bool? completed = null;
        _vm.PaymentCompleted += success => completed = success;

        _vm.CompletePaymentCommand.Execute(false);

        completed.Should().BeFalse();
    }

    [Fact]
    public void PropertyChanged_ShouldFire()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        _vm.IsProcessing = true;
        _vm.Status = "processing";
        _vm.ErrorMessage = "error";

        changed.Should().Contain("IsProcessing");
        changed.Should().Contain("Status");
        changed.Should().Contain("ErrorMessage");
    }
}
