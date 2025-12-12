"""
OBD2 Database Module

Provides database connectivity, ORM models, and repository pattern
for persistent storage of imports, channels, and visualization snapshots.
"""

from .connection import DatabaseManager, get_db_session
from .models import Base, ImportObject, ChannelData, VizSnapshot, MathChannel, ProcessingLog
from .repository import ImportRepository, SnapshotRepository

__all__ = [
    'DatabaseManager',
    'get_db_session',
    'Base',
    'ImportObject',
    'ChannelData',
    'VizSnapshot',
    'MathChannel',
    'ProcessingLog',
    'ImportRepository',
    'SnapshotRepository',
]
