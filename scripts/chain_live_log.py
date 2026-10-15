"""Run the three live loggers independently; one failing does not stop the others.
Exit code is non-zero if any logger failed. Needs only requests."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGGERS = ["log_goalies.py", "log_kalshi_nhl.py", "log_dkex_nhl.py"]

if __name__ == "__main__":
    bad = 0
    for s in LOGGERS:
        try:
            rc = subprocess.run([sys.executable, str(HERE / s)], timeout=600,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).returncode
        except Exception as e:  # noqa: BLE001
            print(f"{s} runner error {e}")
            rc = 1
        bad += rc != 0
    sys.exit(1 if bad else 0)
