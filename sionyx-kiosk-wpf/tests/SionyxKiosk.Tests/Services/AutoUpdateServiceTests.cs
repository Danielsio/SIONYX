using System.IO;
using FluentAssertions;
using SionyxKiosk.Services;
using Xunit;

namespace SionyxKiosk.Tests.Services;

public class AutoUpdateServiceTests
{
    [Theory]
    [InlineData("3.4.1", "3.4.0", true)]
    [InlineData("3.5.0", "3.4.9", true)]
    [InlineData("3.4.10", "3.4.9", true)]   // numeric, not lexical
    [InlineData("v3.4.1", "v3.4.0", true)]  // tolerates a leading 'v'
    [InlineData("3.4.0", "3.4.0", false)]
    [InlineData("3.3.9", "3.4.0", false)]
    public void IsNewerVersion_ComparesSemantically(string latest, string current, bool expected)
    {
        AutoUpdateService.IsNewerVersion(latest, current).Should().Be(expected);
    }

    [Fact]
    public void ComputeSha256_MatchesKnownHash()
    {
        var path = Path.GetTempFileName();
        try
        {
            File.WriteAllText(path, "hello"); // UTF-8, no BOM
            AutoUpdateService.ComputeSha256(path)
                .Should().Be("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824");
        }
        finally
        {
            File.Delete(path);
        }
    }
}
