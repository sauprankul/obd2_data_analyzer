"""
Database Connection Manager

Provides connection pooling and session management for PostgreSQL.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .config import DatabaseConfig, default_config
from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections with connection pooling.
    
    Usage:
        db = DatabaseManager()
        with db.session() as session:
            # Use session for queries
            pass
    """
    
    _instance: Optional["DatabaseManager"] = None
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database manager.
        
        Args:
            config: Database configuration. Uses default if not provided.
        """
        self.config = config or default_config
        self._engine = None
        self._session_factory = None
        
    @classmethod
    def get_instance(cls, config: Optional[DatabaseConfig] = None) -> "DatabaseManager":
        """Get singleton instance of DatabaseManager."""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    @property
    def engine(self):
        """Get or create SQLAlchemy engine with connection pooling."""
        if self._engine is None:
            self._engine = create_engine(
                self.config.connection_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_pre_ping=True,  # Verify connections before use
                echo=False,  # Set to True for SQL debugging
            )
            logger.info(f"Created database engine for {self.config.host}:{self.config.port}/{self.config.database}")
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """Get session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory
    
    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.
        
        Automatically commits on success, rolls back on exception.
        
        Usage:
            with db.session() as session:
                session.add(obj)
                # Auto-commits when exiting context
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def create_tables(self):
        """Create all tables defined in models (for testing/development)."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")
    
    def close(self):
        """Close database connections."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")


# Convenience function for getting sessions
def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session using the default manager.
    
    Usage:
        with get_db_session() as session:
            # Use session
            pass
    """
    db = DatabaseManager.get_instance()
    with db.session() as session:
        yield session
