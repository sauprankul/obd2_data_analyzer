"""
Database Configuration

Environment-based configuration for database connections.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    
    host: str = "localhost"
    port: int = 5432
    database: str = "obd2_data"
    user: str = "obd2_user"
    password: str = "obd2_password"
    
    # Connection pool settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create config from environment variables."""
        return cls(
            host=os.getenv("OBD2_DB_HOST", "localhost"),
            port=int(os.getenv("OBD2_DB_PORT", "5432")),
            database=os.getenv("OBD2_DB_NAME", "obd2_data"),
            user=os.getenv("OBD2_DB_USER", "obd2_user"),
            password=os.getenv("OBD2_DB_PASSWORD", "obd2_password"),
            pool_size=int(os.getenv("OBD2_DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("OBD2_DB_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("OBD2_DB_POOL_TIMEOUT", "30")),
        )
    
    @property
    def connection_url(self) -> str:
        """Get SQLAlchemy connection URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_connection_url(self) -> str:
        """Get async SQLAlchemy connection URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


# Default configuration instance
default_config = DatabaseConfig.from_env()
