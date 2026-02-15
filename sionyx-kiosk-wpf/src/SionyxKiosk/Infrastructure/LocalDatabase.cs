using System.IO;
using LiteDB;
using Serilog;

namespace SionyxKiosk.Infrastructure;

/// <summary>
/// Local embedded database for offline caching (auth tokens, session state, etc.).
/// Uses LiteDB — a lightweight NoSQL embedded database for .NET.
/// Replaces the Python SQLite-based LocalDatabase.
/// </summary>
public sealed class LocalDatabase : IDisposable
{
    private static readonly ILogger Logger = Log.ForContext<LocalDatabase>();
    private readonly LiteDatabase _db;

    public LocalDatabase(string? dbPath = null)
    {
        var path = dbPath ?? GetDefaultPath();
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        _db = new LiteDatabase(path);
        Logger.Debug("LocalDatabase opened at {Path}", path);
    }

    /// <summary>Get a typed collection from the database.</summary>
    public ILiteCollection<T> GetCollection<T>(string name) => _db.GetCollection<T>(name);

    /// <summary>Store a key-value pair in the "settings" collection.</summary>
    public void Set(string key, string value)
    {
        var col = _db.GetCollection<KeyValueEntry>("settings");
        col.Upsert(new KeyValueEntry { Key = key, Value = value });
    }

    /// <summary>Retrieve a value by key from the "settings" collection.</summary>
    public string? Get(string key)
    {
        var col = _db.GetCollection<KeyValueEntry>("settings");
        var entry = col.FindById(key);
        return entry?.Value;
    }

    /// <summary>Delete a key from the "settings" collection.</summary>
    public bool Delete(string key)
    {
        var col = _db.GetCollection<KeyValueEntry>("settings");
        return col.Delete(key);
    }

    /// <summary>Clear all data from a collection.</summary>
    public int ClearCollection(string name) => _db.GetCollection(name).DeleteAll();

    public void Dispose()
    {
        _db.Dispose();
        Logger.Debug("LocalDatabase disposed");
    }

    private static string GetDefaultPath()
    {
        var appData = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "SIONYX");
        return Path.Combine(appData, "sionyx.db");
    }

    /// <summary>Simple key-value entry for settings storage.</summary>
    private class KeyValueEntry
    {
        [BsonId]
        public string Key { get; set; } = "";
        public string Value { get; set; } = "";
    }
}
