using System.Globalization;
using System.Windows;
using FluentAssertions;
using SionyxKiosk.Views.Controls;
using SionyxKiosk.Views.Windows;

namespace SionyxKiosk.Tests.Views;

public class StringToVisibilityConverterTests
{
    private readonly StringToVisibilityConverter _converter = StringToVisibilityConverter.Instance;

    [Fact]
    public void Convert_NonEmptyString_ReturnsVisible()
    {
        var result = _converter.Convert("hello", typeof(Visibility), null!, CultureInfo.InvariantCulture);
        result.Should().Be(Visibility.Visible);
    }

    [Fact]
    public void Convert_EmptyString_ReturnsCollapsed()
    {
        var result = _converter.Convert("", typeof(Visibility), null!, CultureInfo.InvariantCulture);
        result.Should().Be(Visibility.Collapsed);
    }

    [Fact]
    public void Convert_NullValue_ReturnsCollapsed()
    {
        var result = _converter.Convert(null!, typeof(Visibility), null!, CultureInfo.InvariantCulture);
        result.Should().Be(Visibility.Collapsed);
    }

    [Fact]
    public void Convert_NonStringValue_ReturnsCollapsed()
    {
        var result = _converter.Convert(42, typeof(Visibility), null!, CultureInfo.InvariantCulture);
        result.Should().Be(Visibility.Collapsed);
    }

    [Fact]
    public void Convert_WhitespaceString_ReturnsVisible()
    {
        var result = _converter.Convert("  ", typeof(Visibility), null!, CultureInfo.InvariantCulture);
        result.Should().Be(Visibility.Visible);
    }

    [Fact]
    public void ConvertBack_ShouldThrowNotSupportedException()
    {
        var act = () => _converter.ConvertBack(Visibility.Visible, typeof(string), null!, CultureInfo.InvariantCulture);
        act.Should().Throw<NotSupportedException>();
    }

    [Fact]
    public void Instance_ShouldBeSingleton()
    {
        var instance1 = StringToVisibilityConverter.Instance;
        var instance2 = StringToVisibilityConverter.Instance;
        instance1.Should().BeSameAs(instance2);
    }
}

public class InverseBoolConverterTests
{
    private readonly InverseBoolConverter _converter = new();

    [Fact]
    public void Convert_True_ReturnsFalse()
    {
        var result = _converter.Convert(true, typeof(bool), null!, CultureInfo.InvariantCulture);
        result.Should().Be(false);
    }

    [Fact]
    public void Convert_False_ReturnsTrue()
    {
        var result = _converter.Convert(false, typeof(bool), null!, CultureInfo.InvariantCulture);
        result.Should().Be(true);
    }

    [Fact]
    public void Convert_NonBool_ReturnsValueUnchanged()
    {
        var result = _converter.Convert("not a bool", typeof(bool), null!, CultureInfo.InvariantCulture);
        result.Should().Be("not a bool");
    }

    [Fact]
    public void Convert_NullValue_ReturnsNull()
    {
        var result = _converter.Convert(null!, typeof(bool), null!, CultureInfo.InvariantCulture);
        result.Should().BeNull();
    }

    [Fact]
    public void ConvertBack_True_ReturnsFalse()
    {
        var result = _converter.ConvertBack(true, typeof(bool), null!, CultureInfo.InvariantCulture);
        result.Should().Be(false);
    }

    [Fact]
    public void ConvertBack_False_ReturnsTrue()
    {
        var result = _converter.ConvertBack(false, typeof(bool), null!, CultureInfo.InvariantCulture);
        result.Should().Be(true);
    }

    [Fact]
    public void ConvertBack_NonBool_ReturnsValueUnchanged()
    {
        var result = _converter.ConvertBack(42, typeof(bool), null!, CultureInfo.InvariantCulture);
        result.Should().Be(42);
    }

    [Fact]
    public void RoundTrip_ShouldReturnOriginal()
    {
        var original = true;
        var converted = _converter.Convert(original, typeof(bool), null!, CultureInfo.InvariantCulture);
        var backAgain = _converter.ConvertBack(converted, typeof(bool), null!, CultureInfo.InvariantCulture);
        backAgain.Should().Be(original);
    }
}
