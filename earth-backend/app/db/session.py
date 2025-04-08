from collections.abc import Generator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create SQLModel engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for debugging SQL queries, but don't use in production
    pool_pre_ping=True,  # Verify connections before usage to avoid stale connections
)


def create_db_and_tables() -> None:
    """Create all SQLModel tables."""
    logger.info("Creating database tables")
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get a database session. Usage:
    ```
    with get_session() as session:
        # use session
    ```
    """
    with Session(engine) as session:
        yield session


@contextmanager
def get_session_context() -> Generator[Session, None, None]:
    """Alternative way to get a session using context manager.
    Usage:
    ```
    with get_session_context() as session:
        # use session
    ```
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
