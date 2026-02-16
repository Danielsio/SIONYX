using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class PackageServiceTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly PackageService _service;

    public PackageServiceTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new PackageService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public async Task GetAllPackagesAsync_WithPackages_ShouldReturnList()
    {
        _handler.When("packages.json", new
        {
            pkg1 = new { name = "Basic", price = 29.90, minutes = 60, prints = 10, discountPercent = 0, validityDays = 30, isFeatured = false },
            pkg2 = new { name = "Premium", price = 49.90, minutes = 120, prints = 20, discountPercent = 10, validityDays = 30, isFeatured = true },
        });

        var result = await _service.GetAllPackagesAsync();

        result.IsSuccess.Should().BeTrue();
        var packages = result.Data as List<Package>;
        packages.Should().NotBeNull();
        packages!.Count.Should().Be(2);
    }

    [Fact]
    public async Task GetAllPackagesAsync_WithEmptyData_ShouldReturnEmptyList()
    {
        _handler.WhenRaw("packages.json", "null");

        var result = await _service.GetAllPackagesAsync();

        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetAllPackagesAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("packages.json");

        var result = await _service.GetAllPackagesAsync();

        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetAllPackagesAsync_ShouldParsePackageProperties()
    {
        _handler.When("packages.json", new
        {
            pkg1 = new { name = "Test Package", price = 39.90, minutes = 90, prints = 15, discountPercent = 5.0, validityDays = 14, isFeatured = true },
        });

        var result = await _service.GetAllPackagesAsync();
        var packages = result.Data as List<Package>;
        var pkg = packages!.First();

        pkg.Id.Should().Be("pkg1");
        pkg.Name.Should().Be("Test Package");
        pkg.Price.Should().Be(39.90);
        pkg.Minutes.Should().Be(90);
        pkg.Prints.Should().Be(15);
        pkg.DiscountPercent.Should().Be(5.0);
        pkg.ValidityDays.Should().Be(14);
        pkg.IsFeatured.Should().BeTrue();
    }

    [Fact]
    public async Task GetPackageByIdAsync_WhenExists_ShouldReturnPackage()
    {
        _handler.When("packages/pkg1.json", new
        {
            name = "Premium",
            price = 49.90,
            minutes = 120,
            prints = 20,
        });

        var result = await _service.GetPackageByIdAsync("pkg1");

        result.IsSuccess.Should().BeTrue();
        var pkg = result.Data as Package;
        pkg.Should().NotBeNull();
        pkg!.Name.Should().Be("Premium");
    }

    [Fact]
    public async Task GetPackageByIdAsync_WhenNotFound_ShouldReturnError()
    {
        _handler.WhenRaw("packages/nonexistent.json", "null");

        var result = await _service.GetPackageByIdAsync("nonexistent");

        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetPackageByIdAsync_WhenHttpFails_ShouldReturnError()
    {
        _handler.WhenError("packages/pkg1.json");

        var result = await _service.GetPackageByIdAsync("pkg1");

        result.IsSuccess.Should().BeFalse();
    }
}
