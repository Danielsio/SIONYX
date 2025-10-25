"""
Tests for time_formatter utility
"""

from src.utils.time_formatter import format_duration, format_time, parse_time_input


class TestTimeFormatter:
    """Test cases for time formatting utilities"""

    def test_format_time_seconds(self):
        """Test formatting time in seconds"""
        assert format_time(30) == "00:00:30"
        assert format_time(0) == "00:00:00"
        assert format_time(59) == "00:00:59"

    def test_format_time_minutes(self):
        """Test formatting time in minutes"""
        assert format_time(60) == "00:01:00"
        assert format_time(90) == "00:01:30"
        assert format_time(125) == "00:02:05"
        assert format_time(3599) == "00:59:59"

    def test_format_time_hours(self):
        """Test formatting time in hours"""
        assert format_time(3600) == "01:00:00"
        assert format_time(3661) == "01:01:01"
        assert format_time(7200) == "02:00:00"
        assert format_time(7325) == "02:02:05"

    def test_format_time_large_values(self):
        """Test formatting time with large values"""
        assert format_time(86400) == "24:00:00"  # 24 hours
        assert format_time(90061) == "25:01:01"  # 25 hours, 1 minute, 1 second
        assert format_time(3661) == "01:01:01"  # 1 hour, 1 minute, 1 second

    def test_format_time_negative_values(self):
        """Test formatting time with negative values"""
        assert format_time(-30) == "00:00:00"  # Should clamp to 0
        assert format_time(-1) == "00:00:00"

    def test_format_time_float_values(self):
        """Test formatting time with float values"""
        assert format_time(30.5) == "00:00:30"
        assert format_time(60.7) == "00:01:00"
        assert format_time(90.9) == "00:01:30"

    def test_format_duration_seconds(self):
        """Test formatting duration in seconds"""
        assert format_duration(30) == "30 seconds"
        assert format_duration(1) == "1 second"
        assert format_duration(0) == "0 seconds"

    def test_format_duration_minutes(self):
        """Test formatting duration in minutes"""
        assert format_duration(60) == "1 minute"
        assert format_duration(120) == "2 minutes"
        assert format_duration(90) == "1 minute 30 seconds"
        assert format_duration(125) == "2 minutes 5 seconds"

    def test_format_duration_hours(self):
        """Test formatting duration in hours"""
        assert format_duration(3600) == "1 hour"
        assert format_duration(7200) == "2 hours"
        assert format_duration(3661) == "1 hour 1 minute 1 second"
        assert format_duration(7325) == "2 hours 2 minutes 5 seconds"

    def test_format_duration_days(self):
        """Test formatting duration in days"""
        assert format_duration(86400) == "1 day"
        assert format_duration(172800) == "2 days"
        assert format_duration(90061) == "1 day 1 hour 1 minute 1 second"

    def test_format_duration_negative_values(self):
        """Test formatting duration with negative values"""
        assert format_duration(-30) == "0 seconds"
        assert format_duration(-1) == "0 seconds"

    def test_format_duration_float_values(self):
        """Test formatting duration with float values"""
        assert format_duration(30.5) == "30 seconds"
        assert format_duration(60.7) == "1 minute"
        assert format_duration(90.9) == "1 minute 30 seconds"

    def test_parse_time_input_valid_formats(self):
        """Test parsing valid time input formats"""
        # HH:MM:SS format
        assert parse_time_input("01:30:45") == 5445  # 1 hour, 30 minutes, 45 seconds
        assert parse_time_input("00:05:30") == 330  # 5 minutes, 30 seconds
        assert parse_time_input("00:00:45") == 45  # 45 seconds
        assert parse_time_input("02:00:00") == 7200  # 2 hours

    def test_parse_time_input_invalid_formats(self):
        """Test parsing invalid time input formats"""
        invalid_inputs = [
            "invalid",
            "25:00:00",  # Invalid hour
            "12:60:00",  # Invalid minute
            "12:30:60",  # Invalid second
            "12:30",  # Missing seconds
            "12",  # Missing minutes and seconds
            "",  # Empty string
            "12:30:45:67",  # Too many parts
        ]

        for invalid_input in invalid_inputs:
            result = parse_time_input(invalid_input)
            assert result == 0, f"Expected 0 for invalid input: {invalid_input}"

    def test_parse_time_input_edge_cases(self):
        """Test parsing time input edge cases"""
        # Leading zeros
        assert parse_time_input("01:05:30") == 3930
        assert parse_time_input("00:00:01") == 1

        # Maximum valid values
        assert parse_time_input("23:59:59") == 86399

        # Zero time
        assert parse_time_input("00:00:00") == 0

    def test_parse_time_input_whitespace(self):
        """Test parsing time input with whitespace"""
        assert parse_time_input(" 01:30:45 ") == 5445
        assert parse_time_input("\t02:00:00\n") == 7200

    def test_parse_time_input_none_and_empty(self):
        """Test parsing time input with None and empty values"""
        assert parse_time_input(None) == 0
        assert parse_time_input("") == 0
        assert parse_time_input("   ") == 0

    def test_format_time_consistency(self):
        """Test that format_time and parse_time_input are consistent"""
        test_cases = [0, 30, 60, 90, 3600, 3661, 7200, 86400]

        for seconds in test_cases:
            formatted = format_time(seconds)
            parsed = parse_time_input(formatted)
            assert (
                parsed == seconds
            ), f"Failed for {seconds} seconds: {formatted} -> {parsed}"

    def test_format_duration_consistency(self):
        """Test that format_duration handles edge cases consistently"""
        # Test singular vs plural forms
        assert "1 second" in format_duration(1)
        assert "2 seconds" in format_duration(2)
        assert "1 minute" in format_duration(60)
        assert "2 minutes" in format_duration(120)
        assert "1 hour" in format_duration(3600)
        assert "2 hours" in format_duration(7200)

    def test_format_time_large_numbers(self):
        """Test formatting very large time values"""
        # Test with very large numbers
        large_seconds = 999999
        formatted = format_time(large_seconds)
        assert ":" in formatted  # Should contain time separators
        assert len(formatted.split(":")) == 3  # Should have 3 parts

    def test_format_duration_large_numbers(self):
        """Test formatting very large duration values"""
        # Test with very large numbers
        large_seconds = 999999
        formatted = format_duration(large_seconds)
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_time_formatter_integration(self):
        """Test integration between different time formatter functions"""
        # Test round-trip conversion
        original_seconds = 3661  # 1 hour, 1 minute, 1 second

        # Format to time string
        time_string = format_time(original_seconds)
        assert time_string == "01:01:01"

        # Parse back to seconds
        parsed_seconds = parse_time_input(time_string)
        assert parsed_seconds == original_seconds

        # Format to duration string
        duration_string = format_duration(original_seconds)
        assert "1 hour" in duration_string
        assert "1 minute" in duration_string
        assert "1 second" in duration_string
