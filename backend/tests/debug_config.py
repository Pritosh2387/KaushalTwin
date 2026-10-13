"""
Debug configuration loading
"""
import os
import sys
from pathlib import Path

# Add current directory to path (we're already in backend)
sys.path.insert(0, ".")

from app.core.config import Settings

# Clear relevant environment variables
for key in list(os.environ.keys()):
    if key.startswith(('APP_', 'JWT_', 'MONGODB_', 'ML_', 'CORS_', 'SKILL_', 'EMBEDDING_', 'STT_', 'DEMO_', 'UPLOAD_', 'MAX_', 'ALLOWED_', 'LOG_')):
        del os.environ[key]

# Set test values
os.environ["APP_ENV"] = "development"
os.environ["SKILL_EXTRACTION_PROVIDER"] = "llm"
os.environ["LLM_SKILL_API_KEY"] = "test-api-key"
os.environ["EMBEDDING_PROVIDER"] = "sentence_transformer"

print("Environment variables:")
for key in sorted(os.environ.keys()):
    if key.startswith(('APP_', 'JWT_', 'MONGODB_', 'ML_', 'CORS_', 'SKILL_', 'EMBEDDING_', 'STT_', 'DEMO_', 'UPLOAD_', 'MAX_', 'ALLOWED_', 'LOG_')):
        print(f"  {key} = {os.environ[key]}")

# Create settings
settings = Settings(_env_file=None)

print("\nSettings values:")
print(f"  APP_ENV = {settings.APP_ENV}")
print(f"  SKILL_EXTRACTION_PROVIDER = {settings.SKILL_EXTRACTION_PROVIDER}")
print(f"  LLM_SKILL_API_KEY = {settings.LLM_SKILL_API_KEY}")
print(f"  uses_demo_skill_provider = {settings.uses_demo_skill_provider}")
print(f"  EMBEDDING_PROVIDER = {settings.EMBEDDING_PROVIDER}")
print(f"  uses_demo_embedding_provider = {settings.uses_demo_embedding_provider}")