"""
SQLAlchemy ORM Models

Models matching the PostgreSQL schema in database/init.sql
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, 
    DateTime, ForeignKey, ARRAY, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class ImportObject(Base):
    """
    Represents an imported OBD2 data file.
    
    Each import contains multiple channels parsed from a CSV file.
    """
    __tablename__ = "import_objects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    file_size_bytes = Column(Integer, nullable=False)
    channel_count = Column(Integer, nullable=False)
    total_data_points = Column(Integer, nullable=False)
    time_range_start = Column(Float, nullable=True)
    time_range_end = Column(Float, nullable=True)
    original_filename = Column(String(500), nullable=True)
    processing_status = Column(String(50), default="processing")  # processing, completed, failed
    
    # Relationships
    channels = relationship("ChannelData", back_populates="import_obj", cascade="all, delete-orphan")
    logs = relationship("ProcessingLog", back_populates="import_obj", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "file_size_bytes": self.file_size_bytes,
            "channel_count": self.channel_count,
            "total_data_points": self.total_data_points,
            "time_range_start": self.time_range_start,
            "time_range_end": self.time_range_end,
            "original_filename": self.original_filename,
            "processing_status": self.processing_status,
        }


class ChannelData(Base):
    """
    Stores time-series data for a single channel within an import.
    
    Data points are stored as JSONB array of [timestamp, value] pairs.
    """
    __tablename__ = "channel_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id = Column(UUID(as_uuid=True), ForeignKey("import_objects.id", ondelete="CASCADE"), nullable=False)
    channel_name = Column(String(255), nullable=False)
    units = Column(String(100), nullable=True)
    data_points = Column(JSONB, nullable=False)  # Array of [timestamp, value] pairs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    import_obj = relationship("ImportObject", back_populates="channels")
    
    # Unique constraint
    __table_args__ = (
        Index("idx_channel_data_import_id", "import_id"),
        Index("idx_channel_data_channel_name", "channel_name"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "import_id": str(self.import_id),
            "channel_name": self.channel_name,
            "units": self.units,
            "data_point_count": len(self.data_points) if self.data_points else 0,
        }


class VizSnapshot(Base):
    """
    Stores a complete visualization state for later restoration.
    
    Includes layout settings, time ranges, channel visibility, and math channels.
    """
    __tablename__ = "viz_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Layout settings
    sidebar_ratio = Column(Float, default=0.20)
    sidebar_position = Column(String(20), default="left")
    
    # Import references (array of UUIDs)
    import_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    
    # Settings stored as JSONB
    time_settings = Column(JSONB, nullable=False)  # {"import_id": {"start": 0, "end": 100}}
    channel_visibility = Column(JSONB, nullable=False)  # {"import_id": {"channel": true/false}}
    math_channels = Column(JSONB, nullable=False, default=list)
    import_colors = Column(JSONB, nullable=False)  # {"import_id": "#FF5733"}
    graph_heights = Column(JSONB, nullable=False, default=dict)
    
    # UI state
    active_channels = Column(ARRAY(Text), default=list)
    snapshot_metadata = Column("metadata", JSONB, default=dict)  # DB column is 'metadata', Python attr is 'snapshot_metadata'
    
    # Relationships
    math_channel_defs = relationship("MathChannel", back_populates="snapshot", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sidebar_ratio": self.sidebar_ratio,
            "sidebar_position": self.sidebar_position,
            "import_ids": [str(uid) for uid in self.import_ids] if self.import_ids else [],
            "import_count": len(self.import_ids) if self.import_ids else 0,
        }


class MathChannel(Base):
    """
    Defines a mathematical channel computed from other channels.
    """
    __tablename__ = "math_channels"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("viz_snapshots.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)
    expression = Column(Text, nullable=False)  # e.g., "channel_a + channel_b"
    input_channels = Column(ARRAY(Text), nullable=False)
    units = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    snapshot = relationship("VizSnapshot", back_populates="math_channel_defs")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "expression": self.expression,
            "input_channels": self.input_channels,
            "units": self.units,
        }


class ProcessingLog(Base):
    """
    Stores processing logs for import operations.
    """
    __tablename__ = "processing_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id = Column(UUID(as_uuid=True), ForeignKey("import_objects.id", ondelete="CASCADE"), nullable=True)
    log_level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    import_obj = relationship("ImportObject", back_populates="logs")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "import_id": str(self.import_id) if self.import_id else None,
            "log_level": self.log_level,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
