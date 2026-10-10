"""
pytest configuration for the KaushalTwin Backend + ML Service.
Sets sys.path so tests can import from app/ and ml/ without installing the package.
"""

import sys
from pathlib import Path

# Add backend root to path so `from app.xxx import ...` and `from ml.xxx import ...` work everywhere
sys.path.insert(0, str(Path(__file__).parent))
