from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_POSTGRES_CONNECTION_URL = "postgresql://habits_admin:secure_password_123@localhost:5432/habits_tracking_db"

database_engine_instance = create_engine(
    DATABASE_POSTGRES_CONNECTION_URL,
    echo=True
)

DatabaseSessionLocalFactory = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=database_engine_instance
)

def yield_database_session_instance():
    database_session_instance = DatabaseSessionLocalFactory()
    try:
        yield database_session_instance
    finally:
        database_session_instance.close()
