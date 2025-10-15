# db.py
import os
os.environ["LOCAL_DEV"] = "1"  # must be set before loading any other env/config

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()  # optional, for .env

LOCAL_DEV = os.environ.get("LOCAL_DEV", "0") == "1"

if LOCAL_DEV:
    DB_USER = os.getenv("LOCAL_DB_USER", "agri_user")
    DB_PASSWORD = os.getenv("LOCAL_DB_PASSWORD", "sherline10152")
    DB_HOST = os.getenv("LOCAL_DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("LOCAL_DB_PORT", 5432))
    DB_NAME = os.getenv("LOCAL_DB_NAME", "agri_census")
    DB_SSLMODE = "disable"
else:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME")
    DB_SSLMODE = "require"

SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSLMODE}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# Optional connection test
def test_connection():
    try:
        with engine.connect() as conn:
            print("✅ Connected to PostgreSQL:", conn.execute(text("SELECT version();")).fetchone()[0])
    except Exception as e:
        print("❌ Connection failed:", e)

if __name__ == "__main__":
    test_connection()
