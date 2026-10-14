import os
import sys
sys.path.insert(0, ".")

from app.core.config import Settings

if __name__ == "__main__":
    # Test development
    print("Testing development...")
    os.environ["APP_ENV"] = "development"
    settings = Settings(_env_file=None)
    print(f"is_development: {settings.is_development}")
    print(f"is_testing: {settings.is_testing}")
    print(f"is_production: {settings.is_production}")

    # Test testing
    print("\nTesting testing...")
    os.environ["APP_ENV"] = "testing"
    settings = Settings(_env_file=None)
    print(f"is_development: {settings.is_development}")
    print(f"is_testing: {settings.is_testing}")
    print(f"is_production: {settings.is_production}")

    # Test production
    print("\nTesting production...")
    os.environ["APP_ENV"] = "production"
    settings = Settings(_env_file=None)
    print(f"is_development: {settings.is_development}")
    print(f"is_testing: {settings.is_testing}")
    print(f"is_production: {settings.is_production}")