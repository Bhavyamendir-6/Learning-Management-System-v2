import sys
from pathlib import Path

# Ensure the project root is on sys.path so that absolute imports
# (e.g. from Tools..., from Models..., from database..., from config...)
# resolve correctly when the package is loaded by `adk web`.
_project_root = str(Path(__file__).resolve().parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from .agent import root_agent

__all__ = ["root_agent"]
