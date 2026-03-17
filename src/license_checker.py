import os
from datetime import datetime, timedelta

from playsound import playsound

LICENSE_FILE = "license.txt"
LICENSE_DURATION_DAYS = 365  # 1 year


def check_license(
    license_file: str = LICENSE_FILE,
    license_duration_days: int = LICENSE_DURATION_DAYS,
) -> bool:
    """
    Check whether the current license is expired.

    Reads the installation date (YYYY-MM-DD) from *license_file* and compares
    it against today's date.  When the license has expired the function:
      1. Prints an expiry message to stdout.
      2. Plays an alert sound **twice** via playsound.
      3. Returns False.

    :param license_file: Path to the file that stores the installation date.
    :param license_duration_days: Number of days the license remains valid
                                  (default: 365).
    :return: True if the license is still valid, False if it has expired.
    :raises FileNotFoundError: When *license_file* does not exist.
    :raises ValueError: When the date stored in the file cannot be parsed.
    """
    if not os.path.exists(license_file):
        raise FileNotFoundError(
            f"License file '{license_file}' not found. "
            "Please reinstall the application."
        )

    with open(license_file, "r") as fh:
        raw = fh.read().strip()

    try:
        installed_date = datetime.strptime(raw, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            f"Invalid date format in license file (expected YYYY-MM-DD): '{raw}'"
        ) from exc

    expiry_date = installed_date + timedelta(days=license_duration_days)
    today = datetime.today()

    if today > expiry_date:
        print(
            f"⚠  License expired on {expiry_date.strftime('%Y-%m-%d')}. "
            "Please renew your license."
        )
        playsound("alert.wav")
        playsound("alert.wav")
        return False

    days_left = (expiry_date - today).days
    print(f"✔  License is valid. Expires on {expiry_date.strftime('%Y-%m-%d')} "
          f"({days_left} day(s) remaining).")
    return True

