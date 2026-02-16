using System.Collections.ObjectModel;
using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class PackagesViewModelTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly PackagesViewModel _vm;

    public PackagesViewModelTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        var packageService = new PackageService(_firebase);
        var purchaseService = new PurchaseService(_firebase);
        _vm = new PackagesViewModel(packageService, purchaseService, "user-123");
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public void InitialState_ShouldBeEmpty()
    {
        _vm.Packages.Should().BeEmpty();
        _vm.IsLoading.Should().BeFalse();
        _vm.ErrorMessage.Should().BeEmpty();
        _vm.SelectedPackage.Should().BeNull();
    }

    [Fact]
    public async Task LoadPackagesCommand_WithPackages_ShouldPopulateList()
    {
        _handler.When("packages.json", new
        {
            pkg1 = new { name = "Basic", price = 29.90, minutes = 60, prints = 10, discountPercent = 0, validityDays = 30, isFeatured = false },
            pkg2 = new { name = "Premium", price = 49.90, minutes = 120, prints = 20, discountPercent = 10, validityDays = 30, isFeatured = true },
        });

        await _vm.LoadPackagesCommand.ExecuteAsync(null);

        _vm.Packages.Count.Should().Be(2);
        _vm.IsLoading.Should().BeFalse();
        _vm.ErrorMessage.Should().BeEmpty();
    }

    [Fact]
    public async Task LoadPackagesCommand_WhenFails_ShouldSetError()
    {
        _handler.WhenError("packages.json");

        await _vm.LoadPackagesCommand.ExecuteAsync(null);

        _vm.ErrorMessage.Should().NotBeEmpty();
        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public void SelectPackageCommand_ShouldSetSelectedPackage()
    {
        var package = new Package { Id = "pkg1", Name = "Basic", Price = 29.90 };

        _vm.SelectPackageCommand.Execute(package);

        _vm.SelectedPackage.Should().Be(package);
    }

    [Fact]
    public void SelectPackageCommand_ShouldRaisePurchaseRequested()
    {
        Package? requested = null;
        _vm.PurchaseRequested += pkg => requested = pkg;

        var package = new Package { Id = "pkg1", Name = "Basic", Price = 29.90 };
        _vm.SelectPackageCommand.Execute(package);

        requested.Should().Be(package);
    }

    [Fact]
    public void PropertyChanged_ShouldFire()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        _vm.IsLoading = true;
        _vm.ErrorMessage = "error";

        changed.Should().Contain("IsLoading");
        changed.Should().Contain("ErrorMessage");
    }
}
