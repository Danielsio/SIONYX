using System.IO;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class LocalDatabaseTests : IDisposable
{
    private readonly string _dbPath;
    private readonly LocalDatabase _db;

    public LocalDatabaseTests()
    {
        _dbPath = Path.Combine(Path.GetTempPath(), $"sionyx_test_{Guid.NewGuid():N}.db");
        _db = new LocalDatabase(_dbPath);
    }

    public void Dispose()
    {
        _db.Dispose();
        try { File.Delete(_dbPath); } catch { }
    }

    [Fact]
    public void Set_And_Get_ShouldRoundtrip()
    {
        _db.Set("test_key", "test_value");
        _db.Get("test_key").Should().Be("test_value");
    }

    [Fact]
    public void Get_NonExistentKey_ShouldReturnNull()
    {
        _db.Get("nonexistent").Should().BeNull();
    }

    [Fact]
    public void Set_ShouldOverwriteExisting()
    {
        _db.Set("key", "value1");
        _db.Set("key", "value2");
        _db.Get("key").Should().Be("value2");
    }

    [Fact]
    public void Delete_ExistingKey_ShouldReturnTrue()
    {
        _db.Set("key", "value");
        _db.Delete("key").Should().BeTrue();
        _db.Get("key").Should().BeNull();
    }

    [Fact]
    public void Delete_NonExistentKey_ShouldReturnFalse()
    {
        _db.Delete("nonexistent").Should().BeFalse();
    }

    [Fact]
    public void ClearCollection_ShouldRemoveAll()
    {
        _db.Set("key1", "value1");
        _db.Set("key2", "value2");
        _db.ClearCollection("settings");
        _db.Get("key1").Should().BeNull();
        _db.Get("key2").Should().BeNull();
    }

    [Fact]
    public void Set_MultipleKeys_ShouldAllBeRetrievable()
    {
        _db.Set("a", "1");
        _db.Set("b", "2");
        _db.Set("c", "3");

        _db.Get("a").Should().Be("1");
        _db.Get("b").Should().Be("2");
        _db.Get("c").Should().Be("3");
    }

    [Fact]
    public void GetCollection_ShouldReturnCollection()
    {
        var col = _db.GetCollection<dynamic>("test_collection");
        col.Should().NotBeNull();
    }

    [Fact]
    public void Set_EmptyValue_ShouldStoreOrReturnNull()
    {
        // LiteDB may store empty strings as null
        _db.Set("key", "");
        var result = _db.Get("key");
        (result == null || result == "").Should().BeTrue();
    }

    [Fact]
    public void Set_SpecialCharacters_ShouldStore()
    {
        _db.Set("key", "שלום עולם 🌍");
        _db.Get("key").Should().Be("שלום עולם 🌍");
    }
}
