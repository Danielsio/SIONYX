using System.Text;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class OrganizationMetadataServiceTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly OrganizationMetadataService _service;

    public OrganizationMetadataServiceTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new OrganizationMetadataService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    // ==================== DECODE DATA ====================

    [Fact]
    public void DecodeData_WithValidBase64_ShouldDecode()
    {
        var original = new { id = "12345" };
        var json = JsonSerializer.Serialize(original);
        var encoded = Convert.ToBase64String(Encoding.UTF8.GetBytes(json));

        var result = OrganizationMetadataService.DecodeData(encoded);
        result.Should().NotBeNull();
    }

    [Fact]
    public void DecodeData_WithInvalidBase64_ShouldReturnNull()
    {
        var result = OrganizationMetadataService.DecodeData("not-valid-base64!!!");
        result.Should().BeNull();
    }

    [Fact]
    public void DecodeData_WithEmptyString_ShouldReturnNull()
    {
        var result = OrganizationMetadataService.DecodeData("");
        result.Should().BeNull();
    }

    // ==================== GET METADATA ====================

    [Fact]
    public async Task GetOrganizationMetadataAsync_WithValidData_ShouldSucceed()
    {
        var mosadId = Convert.ToBase64String(Encoding.UTF8.GetBytes("\"12345\""));
        var apiValid = Convert.ToBase64String(Encoding.UTF8.GetBytes("\"valid-key\""));

        _handler.When("metadata.json", new
        {
            name = "Test Org",
            nedarim_mosad_id = mosadId,
            nedarim_api_valid = apiValid,
            created_at = "2026-01-01",
            status = "active",
        });

        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetOrganizationMetadataAsync_WithMissingCredentials_ShouldFail()
    {
        _handler.When("metadata.json", new
        {
            name = "Test Org",
            nedarim_mosad_id = "",
            nedarim_api_valid = "",
        });

        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("NEDARIM");
    }

    [Fact]
    public async Task GetOrganizationMetadataAsync_WhenFetchFails_ShouldReturnError()
    {
        _handler.WhenError("metadata.json");

        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetOrganizationMetadataAsync_WhenNullData_ShouldReturnError()
    {
        _handler.WhenRaw("metadata.json", "null");

        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== PRINT PRICING ====================

    [Fact]
    public async Task GetPrintPricingAsync_WithData_ShouldReturnPricing()
    {
        _handler.When("metadata.json", new
        {
            blackAndWhitePrice = 1.5,
            colorPrice = 3.5,
        });

        var result = await _service.GetPrintPricingAsync("test-org");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetPrintPricingAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("metadata.json");

        var result = await _service.GetPrintPricingAsync("test-org");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task SetPrintPricingAsync_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();

        var result = await _service.SetPrintPricingAsync("test-org", 1.5, 3.5);
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== OPERATING HOURS ====================

    [Fact]
    public async Task GetOperatingHoursAsync_WithData_ShouldReturnSettings()
    {
        _handler.When("operatingHours.json", new
        {
            enabled = true,
            startTime = "08:00",
            endTime = "22:00",
            gracePeriodMinutes = 10,
            graceBehavior = "force",
        });

        var result = await _service.GetOperatingHoursAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetOperatingHoursAsync_WhenFails_ShouldReturnDefaults()
    {
        _handler.WhenRaw("operatingHours.json", "null");

        var result = await _service.GetOperatingHoursAsync();
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== ADMIN CONTACT ====================

    [Fact]
    public async Task GetAdminContactAsync_WithData_ShouldSucceed()
    {
        _handler.When("metadata.json", new
        {
            admin_phone = "0501234567",
            admin_email = "admin@test.com",
            name = "Test Org",
        });

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetAdminContactAsync_WithNoContact_ShouldFail()
    {
        _handler.When("metadata.json", new
        {
            name = "Test Org",
        });

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("contact");
    }

    [Fact]
    public async Task GetAdminContactAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("metadata.json");

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeFalse();
    }
}
