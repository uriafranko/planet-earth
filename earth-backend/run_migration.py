"""
Temporary script to run Alembic migrations with a hardcoded database URL.
This bypasses any issues with the .env file.
"""
import os
import subprocess
import sys
import time

# Set environment variables for the database connection
# These should match your Docker Compose configuration
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_PASSWORD"] = "secret"
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_PORT"] = "5433"  # Note: Using port 5433 as seen in docker ps output
os.environ["POSTGRES_DB"] = "planet_earth_db"
os.environ["DATABASE_URL"] = f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_SERVER']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"

# Unset any problematic environment variables that might be coming from .env
if "QDRANT_HTTPS" in os.environ:
    del os.environ["QDRANT_HTTPS"]

print(f"Using database URL: {os.environ['DATABASE_URL']}")

# First, apply any existing migrations
print("Applying existing migrations...")
upgrade_cmd = ["alembic", "upgrade", "head"]
print(f"Running command: {' '.join(upgrade_cmd)}")
upgrade_result = subprocess.run(upgrade_cmd, check=False)

if upgrade_result.returncode != 0:
    print("Failed to apply existing migrations. Exiting.")
    sys.exit(upgrade_result.returncode)

print("Successfully applied existing migrations.")
print("Waiting a moment before creating a new migration...")
time.sleep(2)  # Give the database a moment to settle

# Now create a new migration
print("\nCreating new migration...")
revision_cmd = ["alembic", "revision", "--autogenerate", "-m", "New migration"]
print(f"Running command: {' '.join(revision_cmd)}")
revision_result = subprocess.run(revision_cmd, check=False)
sys.exit(revision_result.returncode)
