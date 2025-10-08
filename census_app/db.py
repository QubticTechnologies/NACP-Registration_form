# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# ------------------- Load Environment Variables -------------------
load_dotenv()

# ------------------- Environment Switch -------------------
LOCAL_DEV = os.getenv("LOCAL_DEV", "0") == "1"

# ------------------- Database Configuration -------------------
if LOCAL_DEV:
    DB_USER = os.getenv("LOCAL_DB_USER", "agri_user")
    DB_PASSWORD = os.getenv("LOCAL_DB_PASSWORD", "sherline10152")
    DB_HOST = os.getenv("LOCAL_DB_HOST", "127.0.0.1")  # force IPv4
    DB_PORT = int(os.getenv("LOCAL_DB_PORT", 5432))
    DB_NAME = os.getenv("LOCAL_DB_NAME", "agri_census")
    DB_SSLMODE = "disable"  # explicitly disable SSL locally
else:
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "YourCloudPassword")
    DB_HOST = os.getenv("DB_HOST", "db.xytwuvfjsujlfxtwniem.supabase.co")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_SSLMODE = "require"  # SSL required for Supabase

# ------------------- Construct SQLAlchemy Database URL -------------------
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSLMODE}"
)

# ------------------- SQLAlchemy Engine & Session -------------------
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# ------------------- Streamlit-friendly Connection Test -------------------
def test_connection():
    try:
        with engine.connect() as conn:
            version = conn.execute("SELECT version();").fetchone()
            print(f"✅ [DB] Connected to PostgreSQL ({'Local' if LOCAL_DEV else 'Cloud'}). Version: {version[0]}")
    except Exception as e:
        print(f"❌ [DB] Connection failed: {e}")

# Run test automatically when imported in Streamlit
print(f"🔍 LOCAL_DEV = {1 if LOCAL_DEV else 0} -> Using {'local' if LOCAL_DEV else 'cloud'} database")
test_connection()
