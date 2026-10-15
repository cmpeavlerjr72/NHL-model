"""Forward logger (read-only): Daily Faceoff starting goalies. See docs/ops/live_loggers.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.live import common, goalies  # noqa: E402

if __name__ == "__main__":
    sys.exit(common.run_logger("goalies", goalies.fetch, goalies.normalise))
