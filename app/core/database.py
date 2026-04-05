"""SQLAlchemy engine and session management."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base


@dataclass(slots=True)
class DatabaseManager:
    """Manage SQLAlchemy engine and sessions for the application.

    Attributes:
        database_url: Database connection string.
        engine: SQLAlchemy engine instance.
        session_factory: Session factory bound to the engine.
    """

    database_url: str
    engine: Engine
    session_factory: sessionmaker[Session]

    @classmethod
    def create(cls, database_url: str) -> "DatabaseManager":
        """Create a database manager for the given connection string.

        Args:
            database_url: SQLAlchemy database URL.

        Returns:
            Initialized database manager.
        """
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        engine = create_engine(
            database_url,
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        session_factory = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )
        return cls(
            database_url=database_url,
            engine=engine,
            session_factory=session_factory,
        )

    def create_schema(self) -> None:
        """Create database schema for all ORM models.

        Args:
            None.

        Returns:
            None.
        """
        # 确保所有 ORM 模型在建表前已注册到 Base.metadata。
        import app.models  # noqa: F401

        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Create a new SQLAlchemy session.

        Args:
            None.

        Returns:
            New ORM session.
        """
        return self.session_factory()

    def dispose(self) -> None:
        """Dispose the underlying SQLAlchemy engine.

        Args:
            None.

        Returns:
            None.
        """
        self.engine.dispose()
