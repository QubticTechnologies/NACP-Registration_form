# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database URL
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://agri_user:sherline10152@localhost:5432/agri_census"

# Create engine
engine = create_engine(SQLALCHEMY_DATABASE_URI, future=True)

# Session maker for ORM queries
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Base class for models
Base = declarative_base()
