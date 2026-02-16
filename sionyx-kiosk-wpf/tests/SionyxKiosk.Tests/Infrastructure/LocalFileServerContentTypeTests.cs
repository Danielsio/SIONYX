using System.IO;
using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Tests for LocalFileServer GetContentType and additional file serving edge cases.
/// </summary>
public class LocalFileServerContentTypeTests
{
    private static string GetContentType(string path)
    {
        var method = typeof(LocalFileServer).GetMethod("GetContentType",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        return (string)method.Invoke(null, new object[] { path })!;
    }

    [Theory]
    [InlineData("test.html", "text/html")]
    [InlineData("test.htm", "text/html")]
    [InlineData("style.css", "text/css")]
    [InlineData("app.js", "application/javascript")]
    [InlineData("data.json", "application/json")]
    [InlineData("logo.png", "image/png")]
    [InlineData("photo.jpg", "image/jpeg")]
    [InlineData("photo.jpeg", "image/jpeg")]
    [InlineData("icon.svg", "image/svg+xml")]
    [InlineData("favicon.ico", "image/x-icon")]
    [InlineData("unknown.xyz", "application/octet-stream")]
    [InlineData("file.bin", "application/octet-stream")]
    [InlineData("noext", "application/octet-stream")]
    public void GetContentType_ShouldReturnCorrectType(string filename, string expectedType)
    {
        var result = GetContentType(filename);
        result.Should().Contain(expectedType);
    }

    [Fact]
    public void FindFreePort_ShouldReturnValidPort()
    {
        var method = typeof(LocalFileServer).GetMethod("FindFreePort",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        var port = (int)method.Invoke(null, null)!;
        port.Should().BeGreaterThan(0);
        port.Should().BeLessThan(65536);
    }

    [Fact]
    public void Constructor_WithZeroPort_ShouldFindFreePort()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"lfs_port_test_{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        try
        {
            var server = new LocalFileServer(tempDir, 0);
            var port = int.Parse(server.BaseUrl.Replace("http://localhost:", "").TrimEnd('/'));
            port.Should().BeGreaterThan(0);
            server.Dispose();
        }
        finally
        {
            Directory.Delete(tempDir, true);
        }
    }
}
