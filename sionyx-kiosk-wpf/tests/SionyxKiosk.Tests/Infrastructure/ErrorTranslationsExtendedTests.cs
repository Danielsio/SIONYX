using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class ErrorTranslationsExtendedTests
{
    [Fact]
    public void Translate_Null_ShouldReturnDefaultHebrew()
    {
        ErrorTranslations.Translate(null).Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void Translate_Empty_ShouldReturnDefaultHebrew()
    {
        ErrorTranslations.Translate("").Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void Translate_Whitespace_ShouldReturnDefaultHebrew()
    {
        ErrorTranslations.Translate("   ").Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void Translate_InvalidCredentials_ShouldReturnHebrew()
    {
        ErrorTranslations.Translate("invalid credentials").Should().Contain("שגויים");
    }

    [Fact]
    public void Translate_NetworkError_ShouldReturnHebrew()
    {
        ErrorTranslations.Translate("network error").Should().Contain("רשת");
    }

    [Fact]
    public void Translate_UnknownMessage_ShouldPrefix()
    {
        var result = ErrorTranslations.Translate("some random error message");
        result.Should().Contain("שגיאה:");
    }

    [Fact]
    public void Translate_PartialMatch_ShouldTranslate()
    {
        var result = ErrorTranslations.Translate("There was a network error in the system");
        result.Should().Contain("רשת");
    }

    [Fact]
    public void Translate_CaseInsensitive_ShouldMatch()
    {
        ErrorTranslations.Translate("INVALID CREDENTIALS").Should().Contain("שגויים");
    }

    [Theory]
    [InlineData("user not found")]
    [InlineData("wrong password")]
    [InlineData("account disabled")]
    [InlineData("too many attempts")]
    [InlineData("database error")]
    [InlineData("access denied")]
    [InlineData("session expired")]
    [InlineData("password must be at least 6 characters")]
    [InlineData("email already exists")]
    [InlineData("password too weak")]
    public void Translate_KnownErrors_ShouldReturnHebrew(string error)
    {
        var result = ErrorTranslations.Translate(error);
        result.Should().NotStartWith("שגיאה:"); // Should be a direct translation, not prefixed
    }

    [Theory]
    [InlineData("user-not-found")]
    [InlineData("wrong-password")]
    [InlineData("account-disabled")]
    [InlineData("too-many-attempts")]
    [InlineData("network-error")]
    [InlineData("server-error")]
    [InlineData("database-error")]
    [InlineData("invalid-input")]
    [InlineData("required-field")]
    public void Translate_DashedErrors_ShouldReturnHebrew(string error)
    {
        var result = ErrorTranslations.Translate(error);
        result.Should().NotStartWith("שגיאה:");
    }
}
