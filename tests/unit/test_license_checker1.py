"""
Unit tests for src/license_checker.py  —  written with pytest-mock.

Advantages over the unittest.mock version (test_license_checker.py):
  - No nested `with patch()` context managers
  - `mocker` fixture auto-resets every mock after each test automatically
  - Flat, readable test bodies — mock setup reads top-to-bottom
  - Zero unittest.mock imports — mocker.mock_open / mocker.call used throughout
"""

import pytest
from datetime import datetime, timedelta

from src.license_checker import check_license


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _date_str(days_offset: int) -> str:
    """Return a YYYY-MM-DD date string relative to today."""
    return (datetime.today() + timedelta(days=days_offset)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Valid license
# ---------------------------------------------------------------------------

class TestLicenseValid:
    """License installed recently -> should be valid."""

    def test_returns_true_when_not_expired(self, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data=_date_str(-10)))
        mock_sound = mocker.patch("src.license_checker.playsound")

        result = check_license()

        assert result is True
        mock_sound.assert_not_called()

    def test_prints_days_remaining(self, mocker, capsys):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data=_date_str(-10)))
        mocker.patch("src.license_checker.playsound")

        check_license()

        captured = capsys.readouterr()
        assert "License is valid" in captured.out
        assert "remaining" in captured.out

    def test_valid_one_day_before_expiry(self, mocker):
        """364 days old -> 1 day remaining -> still valid."""
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data=_date_str(-364)))
        mock_sound = mocker.patch("src.license_checker.playsound")

        result = check_license()

        assert result is True
        mock_sound.assert_not_called()


# ---------------------------------------------------------------------------
# Expired license
# ---------------------------------------------------------------------------

class TestLicenseExpired:
    """License installed more than `duration` days ago -> expired."""

    def test_returns_false_when_expired(self, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data=_date_str(-400)))
        mocker.patch("src.license_checker.playsound")

        assert check_license() is False

    def test_prints_expiry_message(self, mocker, capsys):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data=_date_str(-400)))
        mocker.patch("src.license_checker.playsound")

        check_license()

        assert "License expired" in capsys.readouterr().out

    def test_playsound_called_exactly_twice(self, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data=_date_str(-400)))
        mock_sound = mocker.patch("src.license_checker.playsound")

        check_license()

        assert mock_sound.call_count == 2

    def test_playsound_called_with_correct_file(self, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data=_date_str(-400)))
        mock_sound = mocker.patch("src.license_checker.playsound")

        check_license()

        mock_sound.assert_has_calls([mocker.call("alert.wav"), mocker.call("alert.wav")])

    def test_custom_duration_expired(self, mocker):
        """Custom shorter license (30 days) -> 31 days old -> expired."""
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data=_date_str(-31)))
        mock_sound = mocker.patch("src.license_checker.playsound")

        result = check_license(license_duration_days=30)

        assert result is False
        assert mock_sound.call_count == 2

    def test_custom_duration_valid(self, mocker):
        """Custom longer license (730 days) -> 400 days old -> still valid."""
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data=_date_str(-400)))
        mock_sound = mocker.patch("src.license_checker.playsound")

        result = check_license(license_duration_days=730)

        assert result is True
        mock_sound.assert_not_called()


# ---------------------------------------------------------------------------
# File not found
# ---------------------------------------------------------------------------

class TestLicenseFileNotFound:
    """License file is missing -> FileNotFoundError must be raised."""

    def test_raises_file_not_found(self, mocker):
        mocker.patch("os.path.exists", return_value=False)

        with pytest.raises(FileNotFoundError):
            check_license()

    def test_error_message_contains_filename(self, mocker):
        mocker.patch("os.path.exists", return_value=False)

        with pytest.raises(FileNotFoundError, match="custom/path/license.txt"):
            check_license(license_file="custom/path/license.txt")

    def test_playsound_not_called_when_file_missing(self, mocker):
        mocker.patch("os.path.exists", return_value=False)
        mock_sound = mocker.patch("src.license_checker.playsound")

        with pytest.raises(FileNotFoundError):
            check_license()

        mock_sound.assert_not_called()


# ---------------------------------------------------------------------------
# Bad date format inside the file
# ---------------------------------------------------------------------------

class TestLicenseBadDateFormat:
    """License file contains an un-parseable date -> ValueError must be raised."""

    def test_raises_value_error_on_bad_date(self, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data="not-a-date"))

        with pytest.raises(ValueError, match="Invalid date format"):
            check_license()

    def test_raises_value_error_on_wrong_format(self, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open(read_data="17/03/2026"))

        with pytest.raises(ValueError):
            check_license()

