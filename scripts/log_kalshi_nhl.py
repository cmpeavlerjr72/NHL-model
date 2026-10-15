"""Forward logger (read-only, anonymous): Kalshi NHL markets. See docs/ops/live_loggers.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.live import common, kalshi  # noqa: E402

if __name__ == "__main__":
    sys.exit(common.run_logger("kalshi", kalshi.fetch, kalshi.normalise))
