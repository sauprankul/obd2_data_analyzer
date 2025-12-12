"""
Database Connection Tests

Tests for the database connection layer.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

import pytest
import pandas as pd
from uuid import uuid4

from obd2_viewer.database import (
    DatabaseManager,
    ImportRepository,
    SnapshotRepository,
    ImportObject,
    ChannelData,
)


class TestDatabaseConnection:
    """Test database connectivity."""
    
    def test_connection(self):
        """Test basic database connection."""
        db = DatabaseManager()
        assert db.test_connection() is True
    
    def test_session_context_manager(self):
        """Test session context manager works."""
        from sqlalchemy import text
        db = DatabaseManager()
        with db.session() as session:
            # Simple query to verify session works
            result = session.execute(text("SELECT 1")).fetchone()
            assert result[0] == 1


class TestImportRepository:
    """Test import repository operations."""
    
    @pytest.fixture
    def repo(self):
        """Get import repository."""
        return ImportRepository()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample channel data."""
        channels_data = {
            "test_channel_1": pd.DataFrame({
                "SECONDS": [0.0, 1.0, 2.0, 3.0, 4.0],
                "VALUE": [10.0, 20.0, 30.0, 40.0, 50.0],
            }),
            "test_channel_2": pd.DataFrame({
                "SECONDS": [0.0, 1.0, 2.0, 3.0, 4.0],
                "VALUE": [100.0, 200.0, 300.0, 400.0, 500.0],
            }),
        }
        units_mapping = {
            "test_channel_1": "km/h",
            "test_channel_2": "rpm",
        }
        return channels_data, units_mapping
    
    def test_create_and_get_import(self, repo, sample_data):
        """Test creating and retrieving an import."""
        channels_data, units_mapping = sample_data
        
        # Create import
        import_obj = repo.create_import(
            name="Test Import",
            channels_data=channels_data,
            units_mapping=units_mapping,
            original_filename="test.csv",
            file_size_bytes=1024,
        )
        
        assert import_obj is not None
        assert import_obj.name == "Test Import"
        assert import_obj.channel_count == 2
        assert import_obj.processing_status == "completed"
        
        # Retrieve import
        retrieved = repo.get_import(import_obj.id)
        assert retrieved is not None
        assert retrieved.name == "Test Import"
        
        # Get channels
        retrieved_channels, retrieved_units = repo.get_import_channels(import_obj.id)
        assert len(retrieved_channels) == 2
        assert "test_channel_1" in retrieved_channels
        assert retrieved_units["test_channel_1"] == "km/h"
        
        # Verify data
        df = retrieved_channels["test_channel_1"]
        assert len(df) == 5
        assert df["VALUE"].iloc[0] == 10.0
        
        # Cleanup
        repo.delete_import(import_obj.id)
    
    def test_get_all_imports(self, repo, sample_data):
        """Test listing all imports."""
        channels_data, units_mapping = sample_data
        
        # Create a couple imports
        import1 = repo.create_import(
            name="Import 1",
            channels_data=channels_data,
            units_mapping=units_mapping,
        )
        import2 = repo.create_import(
            name="Import 2",
            channels_data=channels_data,
            units_mapping=units_mapping,
        )
        
        # Get all
        all_imports = repo.get_all_imports()
        import_names = [i.name for i in all_imports]
        
        assert "Import 1" in import_names
        assert "Import 2" in import_names
        
        # Cleanup
        repo.delete_import(import1.id)
        repo.delete_import(import2.id)
    
    def test_delete_import(self, repo, sample_data):
        """Test deleting an import."""
        channels_data, units_mapping = sample_data
        
        import_obj = repo.create_import(
            name="To Delete",
            channels_data=channels_data,
            units_mapping=units_mapping,
        )
        
        # Delete
        result = repo.delete_import(import_obj.id)
        assert result is True
        
        # Verify deleted
        retrieved = repo.get_import(import_obj.id)
        assert retrieved is None


class TestSnapshotRepository:
    """Test snapshot repository operations."""
    
    @pytest.fixture
    def repo(self):
        """Get snapshot repository."""
        return SnapshotRepository()
    
    def test_create_and_get_snapshot(self, repo):
        """Test creating and retrieving a snapshot."""
        import_id = uuid4()
        
        snapshot = repo.create_snapshot(
            name="Test Snapshot",
            import_ids=[import_id],
            time_settings={str(import_id): {"start": 0, "end": 100}},
            channel_visibility={str(import_id): {"channel1": True}},
            import_colors={str(import_id): "#FF5733"},
        )
        
        assert snapshot is not None
        assert snapshot.name == "Test Snapshot"
        
        # Retrieve
        retrieved = repo.get_snapshot(snapshot.id)
        assert retrieved is not None
        assert retrieved.name == "Test Snapshot"
        
        # Cleanup
        repo.delete_snapshot(snapshot.id)


if __name__ == "__main__":
    # Quick connection test
    print("Testing database connection...")
    db = DatabaseManager()
    if db.test_connection():
        print("✅ Database connection successful!")
        
        # Test import repository
        print("\nTesting import repository...")
        repo = ImportRepository()
        
        channels_data = {
            "speed": pd.DataFrame({
                "SECONDS": [0.0, 1.0, 2.0],
                "VALUE": [50.0, 55.0, 60.0],
            }),
        }
        units = {"speed": "km/h"}
        
        import_obj = repo.create_import(
            name="Quick Test",
            channels_data=channels_data,
            units_mapping=units,
        )
        print(f"✅ Created import: {import_obj.id}")
        
        # Retrieve
        retrieved_channels, _ = repo.get_import_channels(import_obj.id)
        print(f"✅ Retrieved {len(retrieved_channels)} channels")
        
        # Cleanup
        repo.delete_import(import_obj.id)
        print("✅ Deleted test import")
        
        print("\n🎉 All database tests passed!")
    else:
        print("❌ Database connection failed!")
