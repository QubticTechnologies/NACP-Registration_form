# db.py - Local Only
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# ------------------- Force Local Mode -------------------
os.environ["LOCAL_DEV"] = "1"
LOCAL_DEV = True

# ------------------- Load Environment Variables -------------------
load_dotenv()  # optional if you have a .env in project root

# ------------------- Local Database Configuration -------------------
DB_USER = os.getenv("LOCAL_DB_USER", "agri_user")
DB_PASSWORD = os.getenv("LOCAL_DB_PASSWORD", "sherline10152")
DB_HOST = os.getenv("LOCAL_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("LOCAL_DB_PORT", 5432))
DB_NAME = os.getenv("LOCAL_DB_NAME", "agri_census")
DB_SSLMODE = "disable"  # explicitly disable SSL for local

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
            version = conn.execute(text("SELECT version();")).fetchone()
            print(f"✅ [DB] Connected to PostgreSQL (Local). Version: {version[0]}")
    except Exception as e:
        print(f"❌ [DB] Connection failed: {e}")

# ------------------- Run Test Automatically -------------------
print("🔍 LOCAL_DEV = 1 -> Using local database")
test_connection()
