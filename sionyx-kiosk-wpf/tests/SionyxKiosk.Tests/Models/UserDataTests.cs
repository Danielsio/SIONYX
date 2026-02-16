using FluentAssertions;
using SionyxKiosk.Models;

namespace SionyxKiosk.Tests.Models;

/// <summary>
/// Tests for UserData model covering all properties and computed values.
/// </summary>
public class UserDataTests
{
    [Fact]
    public void FullName_ShouldCombineFirstAndLastName()
    {
        var user = new UserData { FirstName = "David", LastName = "Cohen" };
        user.FullName.Should().Be("David Cohen");
    }

    [Fact]
    public void FullName_WithOnlyFirstName_ShouldReturnFirstName()
    {
        var user = new UserData { FirstName = "David", LastName = "" };
        user.FullName.Should().Contain("David");
    }

    [Fact]
    public void DefaultValues_ShouldBeCorrect()
    {
        var user = new UserData();
        user.Uid.Should().BeEmpty();
        user.FirstName.Should().BeEmpty();
        user.LastName.Should().BeEmpty();
        user.PhoneNumber.Should().BeEmpty();
        user.Email.Should().BeEmpty();
        user.RemainingTime.Should().Be(0);
        user.PrintBalance.Should().Be(0);
        user.IsLoggedIn.Should().BeFalse();
        user.IsAdmin.Should().BeFalse();
        user.IsSessionActive.Should().BeFalse();
        user.SessionStartTime.Should().BeNull();
        user.CurrentComputerId.Should().BeNull();
        user.TimeExpiresAt.Should().BeNull();
    }

    [Fact]
    public void AllProperties_ShouldBeSettable()
    {
        var now = DateTime.Now.ToString("o");
        var user = new UserData
        {
            Uid = "uid-123",
            FirstName = "Jane",
            LastName = "Doe",
            PhoneNumber = "0501234567",
            Email = "jane@test.com",
            RemainingTime = 7200,
            PrintBalance = 50.5,
            IsLoggedIn = true,
            IsAdmin = true,
            IsSessionActive = true,
            SessionStartTime = now,
            CurrentComputerId = "comp-1",
            TimeExpiresAt = now,
            CreatedAt = now,
            UpdatedAt = now,
        };

        user.Uid.Should().Be("uid-123");
        user.FirstName.Should().Be("Jane");
        user.LastName.Should().Be("Doe");
        user.PhoneNumber.Should().Be("0501234567");
        user.Email.Should().Be("jane@test.com");
        user.RemainingTime.Should().Be(7200);
        user.PrintBalance.Should().Be(50.5);
        user.IsLoggedIn.Should().BeTrue();
        user.IsAdmin.Should().BeTrue();
        user.IsSessionActive.Should().BeTrue();
        user.SessionStartTime.Should().Be(now);
        user.CurrentComputerId.Should().Be("comp-1");
        user.TimeExpiresAt.Should().Be(now);
    }
}
