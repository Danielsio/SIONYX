using System.IO;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class DotEnvLoaderTests : IDisposable
{
    private readonly string _envPath;
    private readonly List<string> _envVarsSet = new();

    public DotEnvLoaderTests()
    {
        _envPath = Path.Combine(Path.GetTempPath(), $"test_{Guid.NewGuid():N}.env");
    }

    public void Dispose()
    {
        // Clean up env vars we set
        foreach (var key in _envVarsSet)
            Environment.SetEnvironmentVariable(key, null);

        try { File.Delete(_envPath); } catch { }
    }

    private void WriteEnvFile(string content)
    {
        File.WriteAllText(_envPath, content);
    }

    private string UniqueKey()
    {
        var key = $"SIONYX_TEST_{Guid.NewGuid():N}";
        _envVarsSet.Add(key);
        return key;
    }

    [Fact]
    public void Load_ShouldSetEnvironmentVariables()
    {
        var key = UniqueKey();
        WriteEnvFile($"{key}=hello_world");

        DotEnvLoader.Load(_envPath);

        Environment.GetEnvironmentVariable(key).Should().Be("hello_world");
    }

    [Fact]
    public void Load_ShouldSkipComments()
    {
        var key = UniqueKey();
        WriteEnvFile($"# This is a comment\n{key}=value");

        DotEnvLoader.Load(_envPath);

        Environment.GetEnvironmentVariable(key).Should().Be("value");
    }

    [Fact]
    public void Load_ShouldSkipEmptyLines()
    {
        var key = UniqueKey();
        WriteEnvFile($"\n\n{key}=value\n\n");

        DotEnvLoader.Load(_envPath);

        Environment.GetEnvironmentVariable(key).Should().Be("value");
    }

    [Fact]
    public void Load_ShouldHandleDoubleQuotedValues()
    {
        var key = UniqueKey();
        WriteEnvFile($"{key}=\"hello world\"");

        DotEnvLoader.Load(_envPath);

        Environment.GetEnvironmentVariable(key).Should().Be("hello world");
    }

    [Fact]
    public void Load_ShouldHandleSingleQuotedValues()
    {
        var key = UniqueKey();
        WriteEnvFile($"{key}='hello world'");

        DotEnvLoader.Load(_envPath);

        Environment.GetEnvironmentVariable(key).Should().Be("hello world");
    }

    [Fact]
    public void Load_ShouldNotOverrideExistingValues()
    {
        var key = UniqueKey();
        Environment.SetEnvironmentVariable(key, "original");
        WriteEnvFile($"{key}=new_value");

        DotEnvLoader.Load(_envPath);

        Environment.GetEnvironmentVariable(key).Should().Be("original");
    }

    [Fact]
    public void Load_NonExistentFile_ShouldNotThrow()
    {
        var act = () => DotEnvLoader.Load("/nonexistent/path/.env");
        act.Should().NotThrow();
    }

    [Fact]
    public void Load_ShouldHandleEqualsInValue()
    {
        var key = UniqueKey();
        WriteEnvFile($"{key}=abc=def=ghi");

        DotEnvLoader.Load(_envPath);

        Environment.GetEnvironmentVariable(key).Should().Be("abc=def=ghi");
    }

    [Fact]
    public void Load_ShouldTrimKeyAndValue()
    {
        var key = UniqueKey();
        WriteEnvFile($"  {key}  =  some_value  ");

        DotEnvLoader.Load(_envPath);

        Environment.GetEnvironmentVariable(key).Should().Be("some_value");
    }

    [Fact]
    public void Load_ShouldSkipLinesWithoutEquals()
    {
        var key = UniqueKey();
        WriteEnvFile($"no_equals_here\n{key}=value");

        DotEnvLoader.Load(_envPath);

        Environment.GetEnvironmentVariable(key).Should().Be("value");
    }
}
