from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The database URL for the FastAPI application is created.
# This specifies the connection string to the PostgreSQL database.
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:your_password@localhost/your_db_name'

# The engine variable is created for the FastAPI app to connect to the database.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# A local session is created for handling database sessions.
# autocommit=False means transactions must be explicitly committed.
# autoflush=False prevents automatic flushing of changes.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is a declarative base class that defines the foundation for database models.
# It allows for creating and controlling database tables.
Base = declarative_base()
