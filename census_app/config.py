# config.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# ------------------- Load environment variables -------------------
load_dotenv()

# ------------------- Environment Switch -------------------
# Set LOCAL_DEV=1 in .env for local development
LOCAL_DEV = os.getenv("LOCAL_DEV", "0") == "1"

# ------------------- Database Settings -------------------
if LOCAL_DEV:
    DB_USER = os.getenv("LOCAL_DB_USER", "postgres")
    DB_PASSWORD = os.getenv("LOCAL_DB_PASSWORD", "sherline10152")
    DB_HOST = os.getenv("LOCAL_DB_HOST", "127.0.0.1")  # force IPv4
    DB_PORT = int(os.getenv("LOCAL_DB_PORT", 5432))
    DB_NAME = os.getenv("LOCAL_DB_NAME", "agri_census")
    DB_SSLMODE = "disable"  # explicitly disable SSL for local
else:
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "YourCloudPassword")
    DB_HOST = os.getenv("DB_HOST", "db.xytwuvfjsujlfxtwniem.supabase.co")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_SSLMODE = "require"  # SSL required for Supabase

# ------------------- Construct Database URL -------------------
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSLMODE}"
)

# ------------------- SQLAlchemy Engine & Session -------------------
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

# ------------------- Test Connection -------------------
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

# ------------------- ENUM / Constants -------------------
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
    'Spouse/ Partner', 'Son', 'Daughter', 'In-Laws', 'Grandchild',
    'Parent/ Parent-in-law', 'Other Relative', 'Non-Relative'
]
WORKING_TIME_OPTIONS = ['N', 'F', 'P', 'P3', 'P6', 'P7']

# Permanent worker constants
POSITION_OPTIONS = {
    "Manager": '1', "Farm Worker": '2', "Grower": '3',
    "Office Worker": '4', "Technician": '5'
}
SEX_OPTIONS_PERM = {"Male": 'M', "Female": 'F'}
AGE_OPTIONS = {
    "15-24": '1', "25-34": '2', "35-44": '3', "45-54": '4',
    "55-64": '5', "65+": '6'
}
NATIONALITY_OPTIONS_PERM = {"Bahamian": 'B', "Non-Bahamian": 'NB'}
EDUCATION_OPTIONS_PERM = {
    "No Schooling": '1', "Primary": '2', "Junior Secondary": '3', "Senior Secondary": '4',
    "Undergraduate": '5', "Masters": '6', "Doctorate": '7', "Vocational": '8',
    "Professional Designation": '9'
}
AG_TRAINING_OPTIONS_PERM = {"Yes": 'Y', "No": 'N'}
MAIN_DUTIES_OPTIONS = {
    "Land Preparation": '1', "Establishment": '2', "Maintenance": '3',
    "Harvesting/Slaughtering": '4', "Transportation": '5', "Marketing/Management": '6',
    "Administrative": '7'
}
WORKING_TIME_OPTIONS_PERM = {
    "None": 'N', "Full time": 'F', "Part time": 'P', "1-3 months": 'P3',
    "4-6 months": 'P6', "7+ months": 'P7'
}

# Database tables
USERS_TABLE = "users"
HOLDERS_TABLE = "holders"
HOUSEHOLD_MEMBERS_TABLE = "household_members"
HOLDING_LABOUR_TABLE = "holding_labour"
HOLDING_LABOUR_PERM_TABLE = "holding_labour_permanent"
HOLDER_SURVEY_PROGRESS_TABLE = "holder_survey_progress"

# Roles
ROLE_HOLDER = "Holder"
ROLE_AGENT = "Agent"
ROLE_ADMIN = "Admin"

# Status
STATUS_PENDING = "pending"
STATUS_ACTIVE = "active"
STATUS_APPROVED = "approved"

# Email settings
EMAIL_USER = os.getenv("EMAIL_USER", "your_email@example.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")

# Survey config
TOTAL_SURVEY_SECTIONS = 5
