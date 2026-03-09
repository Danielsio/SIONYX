using System.Reflection;
using System.Text.Json;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Exposes the private static ParseUserData method for unit testing
/// via reflection, avoiding the need to make it internal/public.
/// </summary>
public static class AuthServiceTestHelper
{
    private static readonly MethodInfo ParseMethod = typeof(AuthService)
        .GetMethod("ParseUserData", BindingFlags.Static | BindingFlags.NonPublic)!;

    public static UserData CallParseUserData(JsonElement data, string uid)
    {
        return (UserData)ParseMethod.Invoke(null, new object[] { data, uid })!;
    }
}
