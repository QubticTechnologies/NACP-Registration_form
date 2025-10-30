from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import time
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def connect_with_retries(retries=5, delay=3):
    """Try connecting to the database with multiple retries."""
    for i in range(retries):
        try:
            engine = create_engine(DATABASE_URL)
            connection = engine.connect()
            print("✅ Database connection successful.")
            return engine
        except OperationalError as e:
            print(f"⚠️ Attempt {i+1}/{retries} failed: {e}")
            time.sleep(delay)
    raise Exception("❌ Could not connect to database after multiple retries.")

# Export engine so other files can import it
engine = connect_with_retries()
