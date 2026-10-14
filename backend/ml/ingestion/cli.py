"""
KaushalTwin ML Service — NOS/QP Data Ingestion CLI
Command-line interface for the NOS/QP data ingestion pipeline.
"""

import argparse
import sys
import os
from pathlib import Path

# Add the backend directory to Python path so we can import ml modules
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from ml.ingestion.pipeline import main as pipeline_main


def cli_main():
    """CLI entry point for the NOS ingestion pipeline."""
    # Forward all arguments to the pipeline main function
    sys.argv = ['nos-ingest'] + sys.argv[1:]
    return pipeline_main()


if __name__ == '__main__':
    sys.exit(cli_main())