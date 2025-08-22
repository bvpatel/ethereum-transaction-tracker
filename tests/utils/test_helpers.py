import pytest
import os
import tempfile
from datetime import datetime
from unittest.mock import patch
from src.utils.helpers import ensure_directory_exists, format_timestamp

class TestEnsureDirectoryExists:
    """Test directory creation functionality"""
    
    def test_create_single_directory(self):
        """Test creating a single directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test_directory")
            
            # Directory should not exist initially
            assert not os.path.exists(test_dir)
            
            # Create directory
            ensure_directory_exists(test_dir)
            
            # Directory should now exist
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)
    
    def test_create_nested_directories(self):
        """Test creating nested directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "level1", "level2", "level3")
            
            # Path should not exist initially
            assert not os.path.exists(nested_path)
            
            # Create nested directories
            ensure_directory_exists(nested_path)
            
            # All levels should now exist
            assert os.path.exists(nested_path)
            assert os.path.isdir(nested_path)
            assert os.path.exists(os.path.join(temp_dir, "level1"))
            assert os.path.exists(os.path.join(temp_dir, "level1", "level2"))
    
    def test_directory_already_exists(self):
        """Test when directory already exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # temp_dir already exists
            
            # Should not raise any exception
            ensure_directory_exists(temp_dir)
            
            # Directory should still exist
            assert os.path.exists(temp_dir)
            assert os.path.isdir(temp_dir)
    
    def test_empty_string_directory(self):
        """Test with empty string directory"""
        # Empty string causes FileNotFoundError in os.makedirs
        with pytest.raises(FileNotFoundError):
            ensure_directory_exists("")
    
    def test_current_directory_dot(self):
        """Test with current directory '.'"""
        ensure_directory_exists(".")
        assert os.path.exists(".")
    
    def test_empty_string_behavior(self):
        """Test actual behavior with empty string"""
        # Document the actual behavior - empty string raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            ensure_directory_exists("")
    
    def test_relative_path(self):
        """Test with relative path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                rel_path = "relative/test/path"
                
                ensure_directory_exists(rel_path)
                
                assert os.path.exists(rel_path)
                assert os.path.isdir(rel_path)
            finally:
                os.chdir(original_cwd)
    
    def test_absolute_path(self):
        """Test with absolute path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            abs_path = os.path.join(temp_dir, "absolute", "test", "path")
            
            ensure_directory_exists(abs_path)
            
            assert os.path.exists(abs_path)
            assert os.path.isdir(abs_path)
    
    def test_path_with_spaces(self):
        """Test with path containing spaces"""
        with tempfile.TemporaryDirectory() as temp_dir:
            spaced_path = os.path.join(temp_dir, "directory with spaces", "sub dir")
            
            ensure_directory_exists(spaced_path)
            
            assert os.path.exists(spaced_path)
            assert os.path.isdir(spaced_path)
    
    def test_path_with_special_characters(self):
        """Test with path containing special characters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            special_path = os.path.join(temp_dir, "dir-with_special.chars", "sub@dir")
            
            ensure_directory_exists(special_path)
            
            assert os.path.exists(special_path)
            assert os.path.isdir(special_path)
    
    @patch('os.makedirs')
    def test_makedirs_called_with_correct_params(self, mock_makedirs):
        """Test that os.makedirs is called with correct parameters"""
        test_dir = "/test/directory"
        
        ensure_directory_exists(test_dir)
        
        mock_makedirs.assert_called_once_with(test_dir, exist_ok=True)
    
    @patch('os.makedirs')
    def test_makedirs_exception_handling(self, mock_makedirs):
        """Test handling of os.makedirs exceptions"""
        mock_makedirs.side_effect = PermissionError("Permission denied")
        
        with pytest.raises(PermissionError):
            ensure_directory_exists("/root/test")
    
    def test_very_long_path(self):
        """Test with very long path name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a reasonably long path (but within filesystem limits)
            long_name = "a" * 50
            long_path = os.path.join(temp_dir, long_name, long_name)
            
            ensure_directory_exists(long_path)
            
            assert os.path.exists(long_path)
            assert os.path.isdir(long_path)


class TestFormatTimestamp:
    """Test timestamp formatting functionality"""
    
    def test_default_format(self):
        """Test default timestamp format"""
        dt = datetime(2023, 12, 25, 14, 30, 45)
        result = format_timestamp(dt)
        assert result == "20231225_143045"
    
    def test_custom_format_date_only(self):
        """Test custom format with date only"""
        dt = datetime(2023, 12, 25, 14, 30, 45)
        result = format_timestamp(dt, "%Y-%m-%d")
        assert result == "2023-12-25"
    
    def test_custom_format_time_only(self):
        """Test custom format with time only"""
        dt = datetime(2023, 12, 25, 14, 30, 45)
        result = format_timestamp(dt, "%H:%M:%S")
        assert result == "14:30:45"
    
    def test_custom_format_with_microseconds(self):
        """Test custom format including microseconds"""
        dt = datetime(2023, 12, 25, 14, 30, 45, 123456)
        result = format_timestamp(dt, "%Y%m%d_%H%M%S_%f")
        assert result == "20231225_143045_123456"
    
    def test_custom_format_verbose(self):
        """Test verbose custom format"""
        dt = datetime(2023, 12, 25, 14, 30, 45)
        result = format_timestamp(dt, "%B %d, %Y at %I:%M %p")
        assert result == "December 25, 2023 at 02:30 PM"
    
    def test_iso_format(self):
        """Test ISO format"""
        dt = datetime(2023, 12, 25, 14, 30, 45)
        result = format_timestamp(dt, "%Y-%m-%dT%H:%M:%S")
        assert result == "2023-12-25T14:30:45"
    
    def test_minimal_format(self):
        """Test minimal format"""
        dt = datetime(2023, 12, 25, 14, 30, 45)
        result = format_timestamp(dt, "%y%m%d")
        assert result == "231225"
    
    def test_format_with_weekday(self):
        """Test format including weekday"""
        dt = datetime(2023, 12, 25, 14, 30, 45)  # Monday
        result = format_timestamp(dt, "%A, %B %d, %Y")
        assert result == "Monday, December 25, 2023"
    
    def test_format_midnight(self):
        """Test formatting at midnight"""
        dt = datetime(2023, 12, 25, 0, 0, 0)
        result = format_timestamp(dt)
        assert result == "20231225_000000"
    
    def test_format_end_of_day(self):
        """Test formatting at end of day"""
        dt = datetime(2023, 12, 25, 23, 59, 59)
        result = format_timestamp(dt)
        assert result == "20231225_235959"
    
    def test_format_new_years_eve(self):
        """Test formatting on New Year's Eve"""
        dt = datetime(2023, 12, 31, 23, 59, 59)
        result = format_timestamp(dt)
        assert result == "20231231_235959"
    
    def test_format_new_years_day(self):
        """Test formatting on New Year's Day"""
        dt = datetime(2024, 1, 1, 0, 0, 0)
        result = format_timestamp(dt)
        assert result == "20240101_000000"
    
    def test_format_leap_year(self):
        """Test formatting on leap year date"""
        dt = datetime(2024, 2, 29, 12, 0, 0)  # 2024 is a leap year
        result = format_timestamp(dt)
        assert result == "20240229_120000"
    
    def test_format_single_digits(self):
        """Test formatting with single digit values"""
        dt = datetime(2023, 1, 1, 1, 1, 1)
        result = format_timestamp(dt)
        assert result == "20230101_010101"
    
    def test_format_with_timezone_info(self):
        """Test formatting with timezone format (note: datetime object should have tzinfo)"""
        dt = datetime(2023, 12, 25, 14, 30, 45)
        result = format_timestamp(dt, "%Y-%m-%d %H:%M:%S %Z")
        # Without actual timezone info, %Z will be empty
        assert result == "2023-12-25 14:30:45 "
    
    def test_empty_format_string(self):
        """Test with empty format string"""
        dt = datetime(2023, 12, 25, 14, 30, 45)
        result = format_timestamp(dt, "")
        assert result == ""
    
    def test_format_string_with_literals(self):
        """Test format string with literal text"""
        dt = datetime(2023, 12, 25, 14, 30, 45)
        result = format_timestamp(dt, "backup_%Y%m%d_%H%M%S.log")
        assert result == "backup_20231225_143045.log"
    
    @pytest.mark.parametrize("dt,format_str,expected", [
        (datetime(2023, 1, 1, 0, 0, 0), "%Y%m%d", "20230101"),
        (datetime(2023, 12, 31, 23, 59, 59), "%H%M%S", "235959"),
        (datetime(2023, 6, 15, 12, 30, 0), "%B", "June"),
        (datetime(2023, 6, 15, 12, 30, 0), "%b", "Jun"),
        (datetime(2023, 6, 15, 12, 30, 0), "%A", "Thursday"),
        (datetime(2023, 6, 15, 12, 30, 0), "%a", "Thu"),
    ])
    def test_various_format_combinations(self, dt, format_str, expected):
        """Test various datetime format combinations"""
        result = format_timestamp(dt, format_str)
        assert result == expected


class TestFileUtilsIntegration:
    """Integration tests combining both functions"""
    
    def test_create_timestamped_directory(self):
        """Test creating a directory with timestamp in name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            dt = datetime(2023, 12, 25, 14, 30, 45)
            timestamp = format_timestamp(dt)
            timestamped_dir = os.path.join(temp_dir, f"backup_{timestamp}")
            
            ensure_directory_exists(timestamped_dir)
            
            assert os.path.exists(timestamped_dir)
            assert os.path.isdir(timestamped_dir)
            assert "backup_20231225_143045" in timestamped_dir
    
    def test_create_nested_timestamped_structure(self):
        """Test creating nested directory structure with timestamps"""
        with tempfile.TemporaryDirectory() as temp_dir:
            dt = datetime(2023, 12, 25, 14, 30, 45)
            date_part = format_timestamp(dt, "%Y/%m/%d")
            time_part = format_timestamp(dt, "%H%M%S")
            
            full_path = os.path.join(temp_dir, "logs", date_part, time_part)
            
            ensure_directory_exists(full_path)
            
            assert os.path.exists(full_path)
            assert os.path.isdir(full_path)
            assert "2023/12/25" in full_path
            assert "143045" in full_path


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_none_datetime(self):
        """Test format_timestamp with None datetime"""
        with pytest.raises(AttributeError):
            format_timestamp(None, "%Y%m%d")
    
    def test_string_instead_of_datetime(self):
        """Test format_timestamp with string instead of datetime"""
        with pytest.raises(AttributeError):
            format_timestamp("2023-12-25", "%Y%m%d")
    
    @patch('os.makedirs')
    def test_ensure_directory_with_none(self, mock_makedirs):
        """Test ensure_directory_exists with None"""
        # None will be passed to os.makedirs which expects a string
        mock_makedirs.side_effect = TypeError("expected str, not NoneType")
        
        with pytest.raises(TypeError):
            ensure_directory_exists(None)