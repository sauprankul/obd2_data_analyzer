"""
Repository Layer

Provides high-level data access methods for imports and snapshots.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from .models import ImportObject, ChannelData, VizSnapshot, MathChannel, ProcessingLog
from .connection import DatabaseManager

logger = logging.getLogger(__name__)


class ImportRepository:
    """
    Repository for managing import objects and their channel data.
    """
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        """Initialize repository with database manager."""
        self.db = db or DatabaseManager.get_instance()
    
    def create_import(
        self,
        name: str,
        channels_data: Dict[str, pd.DataFrame],
        units_mapping: Dict[str, str],
        original_filename: Optional[str] = None,
        file_size_bytes: int = 0,
        description: Optional[str] = None,
    ) -> ImportObject:
        """
        Create a new import with all its channel data.
        
        Args:
            name: Display name for the import
            channels_data: Dict of channel_name -> DataFrame with SECONDS, VALUE columns
            units_mapping: Dict of channel_name -> unit string
            original_filename: Original CSV filename
            file_size_bytes: Size of original file
            description: Optional description
            
        Returns:
            Created ImportObject
        """
        with self.db.session() as session:
            # Calculate metadata
            total_points = sum(len(df) for df in channels_data.values())
            
            # Get time range
            all_times = []
            for df in channels_data.values():
                if 'SECONDS' in df.columns:
                    all_times.extend(df['SECONDS'].dropna().tolist())
            
            time_start = min(all_times) if all_times else None
            time_end = max(all_times) if all_times else None
            
            # Create import object
            import_obj = ImportObject(
                name=name,
                description=description,
                file_size_bytes=file_size_bytes,
                channel_count=len(channels_data),
                total_data_points=total_points,
                time_range_start=time_start,
                time_range_end=time_end,
                original_filename=original_filename,
                processing_status="processing",
            )
            session.add(import_obj)
            session.flush()  # Get the ID
            
            # Create channel data entries
            for channel_name, df in channels_data.items():
                # Convert DataFrame to list of [timestamp, value] pairs
                data_points = []
                if 'SECONDS' in df.columns and 'VALUE' in df.columns:
                    for _, row in df.iterrows():
                        if pd.notna(row['SECONDS']) and pd.notna(row['VALUE']):
                            data_points.append([float(row['SECONDS']), float(row['VALUE'])])
                
                channel = ChannelData(
                    import_id=import_obj.id,
                    channel_name=channel_name,
                    units=units_mapping.get(channel_name, "unknown"),
                    data_points=data_points,
                )
                session.add(channel)
            
            # Mark as completed
            import_obj.processing_status = "completed"
            
            # Log success
            log_entry = ProcessingLog(
                import_id=import_obj.id,
                log_level="INFO",
                message=f"Successfully imported {len(channels_data)} channels with {total_points} data points",
            )
            session.add(log_entry)
            
            logger.info(f"Created import '{name}' with {len(channels_data)} channels")
            
            # Need to expunge to use outside session
            session.expunge(import_obj)
            return import_obj
    
    def get_import(self, import_id: uuid.UUID) -> Optional[ImportObject]:
        """Get an import by ID."""
        with self.db.session() as session:
            import_obj = session.get(ImportObject, import_id)
            if import_obj:
                session.expunge(import_obj)
            return import_obj
    
    def get_all_imports(self) -> List[ImportObject]:
        """Get all imports ordered by creation date."""
        with self.db.session() as session:
            stmt = select(ImportObject).order_by(ImportObject.created_at.desc())
            imports = session.execute(stmt).scalars().all()
            for imp in imports:
                session.expunge(imp)
            return list(imports)
    
    def get_import_channels(
        self, 
        import_id: uuid.UUID
    ) -> Tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
        """
        Get channel data for an import as DataFrames.
        
        Args:
            import_id: UUID of the import
            
        Returns:
            Tuple of (channels_data dict, units_mapping dict)
        """
        with self.db.session() as session:
            stmt = select(ChannelData).where(ChannelData.import_id == import_id)
            channels = session.execute(stmt).scalars().all()
            
            channels_data = {}
            units_mapping = {}
            
            for channel in channels:
                # Convert JSONB data points back to DataFrame
                data_points = channel.data_points or []
                if data_points:
                    df = pd.DataFrame(data_points, columns=['SECONDS', 'VALUE'])
                else:
                    df = pd.DataFrame(columns=['SECONDS', 'VALUE'])
                
                channels_data[channel.channel_name] = df
                units_mapping[channel.channel_name] = channel.units or "unknown"
            
            return channels_data, units_mapping
    
    def delete_import(self, import_id: uuid.UUID) -> bool:
        """Delete an import and all its channel data."""
        with self.db.session() as session:
            import_obj = session.get(ImportObject, import_id)
            if import_obj:
                session.delete(import_obj)
                logger.info(f"Deleted import {import_id}")
                return True
            return False
    
    def update_import_name(self, import_id: uuid.UUID, new_name: str) -> bool:
        """Update an import's name."""
        with self.db.session() as session:
            import_obj = session.get(ImportObject, import_id)
            if import_obj:
                import_obj.name = new_name
                logger.info(f"Updated import {import_id} name to '{new_name}'")
                return True
            return False


class SnapshotRepository:
    """
    Repository for managing visualization snapshots.
    """
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        """Initialize repository with database manager."""
        self.db = db or DatabaseManager.get_instance()
    
    def create_snapshot(
        self,
        name: str,
        import_ids: List[uuid.UUID],
        time_settings: Dict[str, Dict[str, float]],
        channel_visibility: Dict[str, Dict[str, bool]],
        import_colors: Dict[str, str],
        sidebar_ratio: float = 0.20,
        sidebar_position: str = "left",
        graph_heights: Optional[Dict[str, Dict[str, int]]] = None,
        math_channels: Optional[List[Dict]] = None,
        description: Optional[str] = None,
    ) -> VizSnapshot:
        """
        Create a new visualization snapshot.
        
        Args:
            name: Snapshot name
            import_ids: List of import UUIDs included in this snapshot
            time_settings: Time range per import {"import_id": {"start": 0, "end": 100}}
            channel_visibility: Visibility per import {"import_id": {"channel": true}}
            import_colors: Color per import {"import_id": "#FF5733"}
            sidebar_ratio: Sidebar width ratio (0-1)
            sidebar_position: "left" or "top"
            graph_heights: Height per channel
            math_channels: List of math channel definitions
            description: Optional description
            
        Returns:
            Created VizSnapshot
        """
        with self.db.session() as session:
            snapshot = VizSnapshot(
                name=name,
                description=description,
                sidebar_ratio=sidebar_ratio,
                sidebar_position=sidebar_position,
                import_ids=import_ids,
                time_settings=time_settings,
                channel_visibility=channel_visibility,
                import_colors=import_colors,
                graph_heights=graph_heights or {},
                math_channels=math_channels or [],
            )
            session.add(snapshot)
            session.flush()
            
            logger.info(f"Created snapshot '{name}' with {len(import_ids)} imports")
            
            session.expunge(snapshot)
            return snapshot
    
    def get_snapshot(self, snapshot_id: uuid.UUID) -> Optional[VizSnapshot]:
        """Get a snapshot by ID."""
        with self.db.session() as session:
            snapshot = session.get(VizSnapshot, snapshot_id)
            if snapshot:
                session.expunge(snapshot)
            return snapshot
    
    def get_all_snapshots(self) -> List[VizSnapshot]:
        """Get all snapshots ordered by creation date."""
        with self.db.session() as session:
            stmt = select(VizSnapshot).order_by(VizSnapshot.created_at.desc())
            snapshots = session.execute(stmt).scalars().all()
            for snap in snapshots:
                session.expunge(snap)
            return list(snapshots)
    
    def delete_snapshot(self, snapshot_id: uuid.UUID) -> bool:
        """Delete a snapshot."""
        with self.db.session() as session:
            snapshot = session.get(VizSnapshot, snapshot_id)
            if snapshot:
                session.delete(snapshot)
                logger.info(f"Deleted snapshot {snapshot_id}")
                return True
            return False
    
    def update_snapshot(
        self,
        snapshot_id: uuid.UUID,
        **kwargs
    ) -> bool:
        """
        Update snapshot fields.
        
        Args:
            snapshot_id: UUID of snapshot to update
            **kwargs: Fields to update (name, time_settings, channel_visibility, etc.)
            
        Returns:
            True if updated, False if not found
        """
        with self.db.session() as session:
            snapshot = session.get(VizSnapshot, snapshot_id)
            if snapshot:
                for key, value in kwargs.items():
                    if hasattr(snapshot, key):
                        setattr(snapshot, key, value)
                logger.info(f"Updated snapshot {snapshot_id}")
                return True
            return False
