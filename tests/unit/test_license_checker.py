"""
Unit tests for src/license_checker.py
Covers:
  - Valid (non-expired) license
  - Expired license  -> print + playsound called twice
  - License file does not exist -> FileNotFoundError
  - License file contains an invalid date -> ValueError
  - playsound is always mocked so no audio device is needed
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open, call

from src.license_checker import check_license


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _date_str(days_offset: int) -> str:
    """Return a YYYY-MM-DD string relative to today."""
    return (datetime.today() + timedelta(days=days_offset)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Valid license
# ---------------------------------------------------------------------------

class TestLicenseValid:
    """License installed recently -> should be valid."""

    def test_returns_true_when_not_expired(self):
        installed = _date_str(-10)  # installed 10 days ago -> 355 days left
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=installed)), \
             patch("src.license_checker.playsound") as mock_sound:

            result = check_license()

        assert result is True
        mock_sound.assert_not_called()

    def test_prints_days_remaining(self, capsys):
        installed = _date_str(-10)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=installed)), \
             patch("src.license_checker.playsound"):

            check_license()

        captured = capsys.readouterr()
        assert "License is valid" in captured.out
        assert "remaining" in captured.out

    def test_valid_one_day_before_expiry(self):
        """Installed 364 days ago -> 1 day left -> still valid.

        Note: datetime.today() carries the current wall-clock time, so an
        install date of exactly -365 days produces expiry_date at midnight
        *today*, which is already in the past.  Using -364 guarantees there
        is always at least one day remaining regardless of time-of-day.
        """
        installed = _date_str(-364)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=installed)), \
             patch("src.license_checker.playsound") as mock_sound:

            result = check_license()

        assert result is True
        mock_sound.assert_not_called()


# ---------------------------------------------------------------------------
# Expired license
# ---------------------------------------------------------------------------

class TestLicenseExpired:
    """License installed more than `duration` days ago -> expired."""

    def test_returns_false_when_expired(self):
        installed = _date_str(-400)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=installed)), \
             patch("src.license_checker.playsound"):

            result = check_license()

        assert result is False

    def test_prints_expiry_message(self, capsys):
        installed = _date_str(-400)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=installed)), \
             patch("src.license_checker.playsound"):

            check_license()

        captured = capsys.readouterr()
        assert "License expired" in captured.out

    def test_playsound_called_exactly_twice(self):
        installed = _date_str(-400)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=installed)), \
             patch("src.license_checker.playsound") as mock_sound:

            check_license()

        assert mock_sound.call_count == 2

    def test_playsound_called_with_correct_file(self):
        installed = _date_str(-400)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=installed)), \
             patch("src.license_checker.playsound") as mock_sound:

            check_license()

        mock_sound.assert_has_calls([call("alert.wav"), call("alert.wav")])

    def test_custom_duration_expired(self):
        """Custom shorter license (30 days) -> 31 days old -> expired."""
        installed = _date_str(-31)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=installed)), \
             patch("src.license_checker.playsound") as mock_sound:

            result = check_license(license_duration_days=30)

        assert result is False
        assert mock_sound.call_count == 2

    def test_custom_duration_valid(self):
        """Custom longer license (730 days) -> 400 days old -> still valid."""
        installed = _date_str(-400)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=installed)), \
             patch("src.license_checker.playsound") as mock_sound:

            result = check_license(license_duration_days=730)

        assert result is True
        mock_sound.assert_not_called()


# ---------------------------------------------------------------------------
# File not found
# ---------------------------------------------------------------------------

class TestLicenseFileNotFound:
    """License file is missing -> FileNotFoundError must be raised."""

    def test_raises_file_not_found(self):
        with patch("os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                check_license()

    def test_error_message_contains_filename(self):
        custom_path = "custom/path/license.txt"
        with patch("os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="custom/path/license.txt"):
                check_license(license_file=custom_path)

    def test_playsound_not_called_when_file_missing(self):
        with patch("os.path.exists", return_value=False), \
             patch("src.license_checker.playsound") as mock_sound:

            with pytest.raises(FileNotFoundError):
                check_license()

        mock_sound.assert_not_called()


# ---------------------------------------------------------------------------
# Bad date format inside the file
# ---------------------------------------------------------------------------

class TestLicenseBadDateFormat:
    """License file contains an un-parseable date -> ValueError must be raised."""

    def test_raises_value_error_on_bad_date(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="not-a-date")):
            with pytest.raises(ValueError, match="Invalid date format"):
                check_license()

    def test_raises_value_error_on_wrong_format(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="17/03/2026")):
            with pytest.raises(ValueError):
                check_license()

