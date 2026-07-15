using FluentAssertions;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

/// <summary>
/// The org's display name (set in the web console) is used as the message
/// sender when the message itself carries no name — otherwise "מנהל".
/// </summary>
public class MessageSenderNameTests
{
    private static Dictionary<string, object?> Msg(string? fromName = null) =>
        new()
        {
            ["id"] = "m1",
            ["body"] = "שלום",
            ["timestamp"] = 0d,
            ["fromName"] = fromName,
        };

    [Fact]
    public void UsesTheOrgDisplayNameWhenTheMessageHasNoSender()
    {
        var item = MessageItem.FromDictionary(Msg(), "הדפסות המרכז");
        item.DisplaySender.Should().Be("הדפסות המרכז");
    }

    [Fact]
    public void MessageSenderWinsOverTheOrgDisplayName()
    {
        var item = MessageItem.FromDictionary(Msg("יוסי"), "הדפסות המרכז");
        item.DisplaySender.Should().Be("יוסי");
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void FallsBackToTheGenericSenderWhenNoDisplayNameIsSet(string? displayName)
    {
        var item = MessageItem.FromDictionary(Msg(), displayName);
        item.DisplaySender.Should().Be(MessageItem.DefaultSender);
    }

    [Fact]
    public void UnchangedBehaviourWhenNoFallbackIsSupplied()
    {
        var item = MessageItem.FromDictionary(Msg());
        item.DisplaySender.Should().Be("מנהל");
    }
}
