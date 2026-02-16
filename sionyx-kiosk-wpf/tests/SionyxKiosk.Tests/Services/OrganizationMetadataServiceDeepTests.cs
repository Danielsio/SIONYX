using System.Text;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for OrganizationMetadataService covering all methods and edge cases.
/// </summary>
public class OrganizationMetadataServiceDeepTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly OrganizationMetadataService _service;

    public OrganizationMetadataServiceDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new OrganizationMetadataService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    // ==================== DecodeData ====================

    [Fact]
    public void DecodeData_WithValidBase64_ShouldReturnParsedJson()
    {
        var json = "{\"key\":\"value\"}";
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

    [Fact]
    public void DecodeData_WithValidBase64ButInvalidJson_ShouldReturnNull()
    {
        var encoded = Convert.ToBase64String(Encoding.UTF8.GetBytes("not json {{{"));
        var result = OrganizationMetadataService.DecodeData(encoded);
        result.Should().BeNull();
    }

    // ==================== GetOrganizationMetadataAsync ====================

    [Fact]
    public async Task GetOrganizationMetadataAsync_WithValidData_ShouldReturn()
    {
        var mosadId = Convert.ToBase64String(Encoding.UTF8.GetBytes("\"12345\""));
        var apiValid = Convert.ToBase64String(Encoding.UTF8.GetBytes("\"valid-key\""));

        _handler.When("metadata.json", new
        {
            name = "Test Org",
            nedarim_mosad_id = mosadId,
            nedarim_api_valid = apiValid,
            created_at = "2024-01-01",
            status = "active",
        });

        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetOrganizationMetadataAsync_WithMissingCredentials_ShouldReturnError()
    {
        _handler.When("metadata.json", new
        {
            name = "Test Org",
            // Missing nedarim credentials
        });

        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("NEDARIM");
    }

    [Fact]
    public async Task GetOrganizationMetadataAsync_WhenFirebaseFails_ShouldReturnError()
    {
        _handler.WhenError("metadata.json");
        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetOrganizationMetadataAsync_WithNullData_ShouldReturnError()
    {
        _handler.WhenRaw("metadata.json", "null");
        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== GetPrintPricingAsync ====================

    [Fact]
    public async Task GetPrintPricingAsync_WithValidPricing_ShouldReturnPrices()
    {
        _handler.When("metadata.json", new
        {
            blackAndWhitePrice = 0.5,
            colorPrice = 2.5,
        });

        var result = await _service.GetPrintPricingAsync("test-org");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetPrintPricingAsync_WithMissingPricing_ShouldReturnDefaults()
    {
        _handler.When("metadata.json", new { name = "org" });

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
    public async Task GetPrintPricingAsync_WithNullData_ShouldReturnError()
    {
        _handler.WhenRaw("metadata.json", "null");
        var result = await _service.GetPrintPricingAsync("test-org");
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== SetPrintPricingAsync ====================

    [Fact]
    public async Task SetPrintPricingAsync_WithValidData_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        var result = await _service.SetPrintPricingAsync("test-org", 0.5, 2.5);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task SetPrintPricingAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("metadata");
        var result = await _service.SetPrintPricingAsync("test-org", 0.5, 2.5);
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== GetOperatingHoursAsync ====================

    [Fact]
    public async Task GetOperatingHoursAsync_WithValidData_ShouldReturn()
    {
        _handler.When("operatingHours.json", new
        {
            enabled = true,
            startTime = "08:00",
            endTime = "22:00",
            gracePeriodMinutes = 15,
            graceBehavior = "force",
        });

        var result = await _service.GetOperatingHoursAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetOperatingHoursAsync_WithNullData_ShouldReturnDefaults()
    {
        _handler.WhenRaw("operatingHours.json", "null");

        var result = await _service.GetOperatingHoursAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetOperatingHoursAsync_WhenFails_ShouldReturnDefaults()
    {
        _handler.WhenError("operatingHours.json");

        var result = await _service.GetOperatingHoursAsync();
        result.IsSuccess.Should().BeTrue(); // Returns defaults, not error
    }

    // ==================== GetAdminContactAsync ====================

    [Fact]
    public async Task GetAdminContactAsync_WithValidContact_ShouldReturn()
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
    public async Task GetAdminContactAsync_WithOnlyPhone_ShouldReturn()
    {
        _handler.When("metadata.json", new
        {
            admin_phone = "0501234567",
            name = "Test Org",
        });

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetAdminContactAsync_WithOnlyEmail_ShouldReturn()
    {
        _handler.When("metadata.json", new
        {
            admin_email = "admin@test.com",
            name = "Test Org",
        });

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetAdminContactAsync_WithNoContact_ShouldReturnError()
    {
        _handler.When("metadata.json", new
        {
            name = "Test Org",
        });

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("Admin contact");
    }

    [Fact]
    public async Task GetAdminContactAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("metadata.json");
        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetAdminContactAsync_WithNullData_ShouldReturnError()
    {
        _handler.WhenRaw("metadata.json", "null");
        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeFalse();
    }
}
