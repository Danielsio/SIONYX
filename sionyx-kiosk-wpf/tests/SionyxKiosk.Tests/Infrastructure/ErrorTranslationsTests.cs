using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class ErrorTranslationsTests
{
    [Fact]
    public void Translate_KnownFirebaseError_ShouldReturnHebrew()
    {
        var result = ErrorTranslations.Translate("INVALID_PASSWORD");
        result.Should().NotBe("INVALID_PASSWORD", "known errors should be translated");
    }

    [Fact]
    public void Translate_UnknownError_ShouldReturnGenericMessage()
    {
        var result = ErrorTranslations.Translate("SOME_UNKNOWN_ERROR_CODE");
        result.Should().NotBeNullOrWhiteSpace();
    }

    [Fact]
    public void Translate_NullOrEmpty_ShouldReturnGenericMessage()
    {
        ErrorTranslations.Translate("").Should().NotBeNullOrWhiteSpace();
        ErrorTranslations.Translate(null!).Should().NotBeNullOrWhiteSpace();
    }
}
