import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# --------------------------------------------------------
# Load environment variables
# --------------------------------------------------------
load_dotenv()

# Toggle: Set to False when deploying live
LOCAL_DEV = False

# --------------------------------------------------------
# Database Configuration
# --------------------------------------------------------
if LOCAL_DEV:
    # 🔹 Local PostgreSQL
    DB_USER = os.getenv("LOCAL_DB_USER", "postgres")
    DB_PASSWORD = os.getenv("LOCAL_DB_PASSWORD", "sherline10152")
    DB_HOST = os.getenv("LOCAL_DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("LOCAL_DB_PORT", 5432))
    DB_NAME = os.getenv("LOCAL_DB_NAME", "agri_census")
    DB_SSLMODE = "disable"
    DATABASE_URL = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSLMODE}"
    )
else:
    # 🔹 Production: Render PostgreSQL (Live)
    DATABASE_URL = (
        "postgresql+psycopg2://servey_census_user:"
        "pA16sWRzYkKqhOLJoLiiHcHnaRu7q3oJ@"
        "dpg-d3msd5s9c44c73ccd240-a/servey_census"
    )

# --------------------------------------------------------
# SQLAlchemy Engine & Session
# --------------------------------------------------------
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

# --------------------------------------------------------
# Test Connection (safe to keep)
# --------------------------------------------------------
def test_connection():
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version();")).fetchone()
            print(f"✅ [DB] Connected successfully → {version[0]}")
    except Exception as e:
        print(f"❌ [DB] Connection failed: {e}")

# Run connection test only when running locally
if __name__ == "__main__":
    test_connection()

# --------------------------------------------------------
# Table Constants
# --------------------------------------------------------
USERS_TABLE = "users"
HOLDERS_TABLE = "holders"
HOUSEHOLD_MEMBERS_TABLE = "household_members"
HOLDING_LABOUR_TABLE = "holding_labour"
HOLDING_LABOUR_PERM_TABLE = "holding_labour_permanent"
HOLDER_SURVEY_PROGRESS_TABLE = "holder_survey_progress"

# --------------------------------------------------------
# Roles
# --------------------------------------------------------
ROLE_HOLDER = "Holder"
ROLE_AGENT = "Agent"
ROLE_ADMIN = "Admin"

# --------------------------------------------------------
# Status
# --------------------------------------------------------
STATUS_PENDING = "pending"
STATUS_ACTIVE = "active"
STATUS_APPROVED = "approved"

# --------------------------------------------------------
# Survey Config
# --------------------------------------------------------
TOTAL_SURVEY_SECTIONS = 5

# --------------------------------------------------------
# Email Settings
# --------------------------------------------------------
EMAIL_USER = os.getenv("EMAIL_USER", "your_email@example.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")

# --------------------------------------------------------
# Enumerations & Constants
# --------------------------------------------------------
SEX_OPTIONS = ["Male", "Female", "Other"]

MARITAL_STATUS_OPTIONS = [
    "Single", "Married", "Divorced", "Separated", "Widowed",
    "Common-Law", "Prefer not to disclose"
]

NATIONALITY_OPTIONS = ["Bahamian", "Other"]

EDUCATION_OPTIONS = [
    "No Schooling", "Primary", "Junior Secondary", "Senior Secondary",
    "Undergraduate", "Masters", "Doctorate", "Vocational", "Professional Designation"
]

AG_TRAINING_OPTIONS = ["Yes", "No"]

PRIMARY_OCC_OPTIONS = ["Agriculture", "Other"]

OCCUPATION_OPTIONS = [
    "Agriculture", "Fishing", "Professional/ Technical", "Administrative/ Manager",
    "Sales", "Customer Service", "Tourism", "Not Economically Active", "Other"
]

RELATIONSHIP_OPTIONS = [
    "Spouse/ Partner", "Son", "Daughter", "In-Laws", "Grandchild",
    "Parent/ Parent-in-law", "Other Relative", "Non-Relative"
]

WORKING_TIME_OPTIONS = ["N", "F", "P", "P3", "P6", "P7"]
