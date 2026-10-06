"""
pytest configuration for the KaushalTwin ML Service.
Sets sys.path so tests can import from app/ without installing the package.
"""

import sys
from pathlib import Path

# Add ml_service root to path so `from app.xxx import ...` works in tests
sys.path.insert(0, str(Path(__file__).parent))
