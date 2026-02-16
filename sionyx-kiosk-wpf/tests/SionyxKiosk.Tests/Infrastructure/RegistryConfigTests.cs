using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class RegistryConfigTests
{
    [Fact]
    public void ReadValue_NonExistentKey_ShouldReturnDefault()
    {
        var result = RegistryConfig.ReadValue("NonExistentKey12345", "default_value");
        result.Should().Be("default_value");
    }

    [Fact]
    public void ReadValue_WithNullDefault_ShouldReturnNull()
    {
        var result = RegistryConfig.ReadValue("NonExistentKey12345");
        result.Should().BeNull();
    }

    [Fact]
    public void GetAllConfig_ShouldReturnAllExpectedKeys()
    {
        var config = RegistryConfig.GetAllConfig();

        config.Should().ContainKey("OrgId");
        config.Should().ContainKey("ApiKey");
        config.Should().ContainKey("AuthDomain");
        config.Should().ContainKey("ProjectId");
        config.Should().ContainKey("DatabaseUrl");
        config.Should().ContainKey("StorageBucket");
        config.Should().ContainKey("MessagingSenderId");
        config.Should().ContainKey("AppId");
        config.Should().ContainKey("MeasurementId");
    }

    [Fact]
    public void RegistryConfigExists_ShouldNotThrow()
    {
        var act = () => RegistryConfig.RegistryConfigExists();
        act.Should().NotThrow();
    }

    [Fact]
    public void IsProduction_ShouldReturnBoolean()
    {
        // Just verify it doesn't throw and returns a boolean
        var act = () => RegistryConfig.IsProduction();
        act.Should().NotThrow();
    }
}
