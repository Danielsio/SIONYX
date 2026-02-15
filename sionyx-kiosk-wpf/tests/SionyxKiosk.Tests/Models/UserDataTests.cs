using FluentAssertions;
using SionyxKiosk.Models;

namespace SionyxKiosk.Tests.Models;

public class UserDataTests
{
    [Fact]
    public void FullName_ShouldCombineFirstAndLastName()
    {
        var user = new UserData { FirstName = "David", LastName = "Cohen" };
        user.FullName.Should().Be("David Cohen");
    }

    [Fact]
    public void FullName_WithOnlyFirstName_ShouldTrim()
    {
        var user = new UserData { FirstName = "David", LastName = "" };
        user.FullName.Should().Be("David");
    }

    [Fact]
    public void FullName_WithEmptyNames_ShouldBeEmpty()
    {
        var user = new UserData();
        user.FullName.Should().BeEmpty();
    }

    [Fact]
    public void DefaultValues_ShouldBeReasonable()
    {
        var user = new UserData();

        user.Uid.Should().BeEmpty();
        user.Email.Should().BeEmpty();
        user.RemainingTime.Should().Be(0);
        user.PrintBalance.Should().Be(0);
        user.IsLoggedIn.Should().BeFalse();
        user.IsAdmin.Should().BeFalse();
        user.IsSessionActive.Should().BeFalse();
        user.SessionStartTime.Should().BeNull();
        user.CurrentComputerId.Should().BeNull();
    }

    [Fact]
    public void Properties_ShouldRoundtrip()
    {
        var user = new UserData
        {
            Uid = "abc123",
            FirstName = "Test",
            LastName = "User",
            PhoneNumber = "0501234567",
            Email = "test@example.com",
            RemainingTime = 3600,
            PrintBalance = 25.50,
            IsLoggedIn = true,
            IsAdmin = false,
            IsSessionActive = true,
            SessionStartTime = "2025-01-01T12:00:00Z",
            CurrentComputerId = "pc-001"
        };

        user.Uid.Should().Be("abc123");
        user.RemainingTime.Should().Be(3600);
        user.PrintBalance.Should().Be(25.50);
        user.IsLoggedIn.Should().BeTrue();
        user.CurrentComputerId.Should().Be("pc-001");
    }
}
