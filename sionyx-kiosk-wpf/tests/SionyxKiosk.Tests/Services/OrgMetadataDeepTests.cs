using System.Text;
using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Additional coverage for OrganizationMetadataService: edge cases in
/// contact, pricing, operating hours, organization metadata.
/// </summary>
public class OrgMetadataDeepTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly OrganizationMetadataService _service;
    private const string OrgId = "test-org";

    public OrgMetadataDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.SetDefaultSuccess();
        _service = new OrganizationMetadataService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    private static string EncodeBase64(string value) =>
        Convert.ToBase64String(Encoding.UTF8.GetBytes($"\"{value}\""));

    // ==================== GET ADMIN CONTACT ====================

    [Fact]
    public async Task GetAdminContactAsync_WithBothFields_ShouldSucceed()
    {
        _handler.When("metadata.json", new
        {
            admin_phone = "050-1234567",
            admin_email = "admin@test.com",
            name = "Test Org",
        });

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeTrue();
        result.Data.Should().NotBeNull();
    }

    [Fact]
    public async Task GetAdminContactAsync_WithOnlyPhone_ShouldSucceed()
    {
        _handler.When("metadata.json", new
        {
            admin_phone = "050-1234567",
            admin_email = "",
            name = "Test Org",
        });

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetAdminContactAsync_WithNoContactInfo_ShouldReturnError()
    {
        _handler.When("metadata.json", new
        {
            name = "Test Org",
        });

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetAdminContactAsync_WhenFetchFails_ShouldReturnError()
    {
        _handler.WhenError("metadata.json");

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetAdminContactAsync_WhenNullData_ShouldReturnError()
    {
        _handler.WhenRaw("metadata.json", "null");

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== GET PRINT PRICING ====================

    [Fact]
    public async Task GetPrintPricingAsync_WithValidData_ShouldSucceed()
    {
        _handler.When("organizations/test-org/metadata.json", new
        {
            blackAndWhitePrice = 0.10,
            colorPrice = 0.50,
        });

        var result = await _service.GetPrintPricingAsync(OrgId);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetPrintPricingAsync_WithMissingPrices_ShouldUseDefaults()
    {
        _handler.WhenRaw("organizations/test-org/metadata.json", "{}");

        var result = await _service.GetPrintPricingAsync(OrgId);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetPrintPricingAsync_WhenFetchFails_ShouldReturnError()
    {
        _handler.WhenError("organizations/test-org/metadata.json");

        var result = await _service.GetPrintPricingAsync(OrgId);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetPrintPricingAsync_WhenNull_ShouldReturnError()
    {
        _handler.WhenRaw("organizations/test-org/metadata.json", "null");

        var result = await _service.GetPrintPricingAsync(OrgId);
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== SET PRINT PRICING ====================

    [Fact]
    public async Task SetPrintPricingAsync_ShouldSucceed()
    {
        var result = await _service.SetPrintPricingAsync(OrgId, 0.15, 0.60);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task SetPrintPricingAsync_WhenUpdateFails_ShouldReturnError()
    {
        _handler.ClearHandlers();
        _handler.WhenError("organizations/test-org/metadata");

        var result = await _service.SetPrintPricingAsync(OrgId, 0.15, 0.60);
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== GET OPERATING HOURS ====================

    [Fact]
    public async Task GetOperatingHoursAsync_WithFullData_ShouldSucceed()
    {
        _handler.When("metadata/settings/operatingHours.json", new
        {
            enabled = true,
            startTime = "06:00",
            endTime = "22:00",
            gracePeriodMinutes = 10,
            graceBehavior = "force",
        });

        var result = await _service.GetOperatingHoursAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetOperatingHoursAsync_WhenFetchFails_ShouldReturnDefaults()
    {
        // GetOperatingHoursAsync returns Success(defaults) on failure
        _handler.WhenError("metadata/settings/operatingHours.json");

        var result = await _service.GetOperatingHoursAsync();
        result.IsSuccess.Should().BeTrue(); // returns defaults, not error
    }

    [Fact]
    public async Task GetOperatingHoursAsync_WhenNull_ShouldReturnDefaults()
    {
        _handler.WhenRaw("metadata/settings/operatingHours.json", "null");

        var result = await _service.GetOperatingHoursAsync();
        result.IsSuccess.Should().BeTrue(); // returns defaults
    }

    // ==================== GET ORGANIZATION METADATA ====================

    [Fact]
    public async Task GetOrganizationMetadataAsync_WithFullData_ShouldSucceed()
    {
        _handler.When("metadata.json", new
        {
            name = "Test Org",
            admin_phone = "050-1234567",
            admin_email = "admin@test.com",
            nedarim_mosad_id = EncodeBase64("12345"),
            nedarim_api_valid = EncodeBase64("api-key-123"),
            created_at = "2025-01-01T00:00:00",
            status = "active",
        });

        var result = await _service.GetOrganizationMetadataAsync(OrgId);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetOrganizationMetadataAsync_WithoutNedarimCredentials_ShouldReturnError()
    {
        _handler.When("metadata.json", new
        {
            name = "Test Org",
            admin_phone = "050-1234567",
        });

        var result = await _service.GetOrganizationMetadataAsync(OrgId);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetOrganizationMetadataAsync_WhenNull_ShouldReturnError()
    {
        _handler.WhenRaw("metadata.json", "null");

        var result = await _service.GetOrganizationMetadataAsync(OrgId);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetOrganizationMetadataAsync_WhenFetchFails_ShouldReturnError()
    {
        _handler.WhenError("metadata.json");

        var result = await _service.GetOrganizationMetadataAsync(OrgId);
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== DECODE DATA ====================

    [Fact]
    public void DecodeData_WithValidBase64_ShouldDecode()
    {
        var encoded = EncodeBase64("hello");
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
}
