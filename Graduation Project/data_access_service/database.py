from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# MariaDB connection URL
# Format: "mysql+pymysql://username:password@host:port/database"
DATABASE_URL = 'mysql+mysqldb://analyst:pass@localhost:3306/malware_analysis'

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
