"""Root Streamlit entrypoint wrapper."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from streamlit_sample.app import run_app


if __name__ == "__main__":  # pragma: no cover - executed by Streamlit runtime
    run_app()
