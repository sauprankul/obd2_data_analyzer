-- OBD2 Data Visualization Tool Database Schema
-- PostgreSQL initialization script

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Import Objects Table
CREATE TABLE IF NOT EXISTS import_objects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    file_size_bytes INTEGER NOT NULL,
    channel_count INTEGER NOT NULL,
    total_data_points INTEGER NOT NULL,
    time_range_start DOUBLE PRECISION,
    time_range_end DOUBLE PRECISION,
    original_filename VARCHAR(500),
    processing_status VARCHAR(50) DEFAULT 'processing' -- processing, completed, failed
);

-- Channel Data Table
CREATE TABLE IF NOT EXISTS channel_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    import_id UUID NOT NULL REFERENCES import_objects(id) ON DELETE CASCADE,
    channel_name VARCHAR(255) NOT NULL,
    units VARCHAR(100),
    data_points JSONB NOT NULL, -- Array of [timestamp, value] pairs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(import_id, channel_name)
);

-- Visualization Snapshots Table
CREATE TABLE IF NOT EXISTS viz_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Layout settings
    sidebar_ratio DECIMAL(3,2) DEFAULT 0.20, -- 20% sidebar, 80% graphs
    sidebar_position VARCHAR(20) DEFAULT 'left', -- left, top
    
    -- Import references
    import_ids UUID[] NOT NULL, -- Array of import object IDs
    
    -- Time settings per import (JSON object keyed by import_id)
    time_settings JSONB NOT NULL, -- {"import_id": {"start": 0, "end": 100, "zoom": 1.0}}
    
    -- Channel visibility (JSON object keyed by import_id)
    channel_visibility JSONB NOT NULL, -- {"import_id": {"channel_name": true/false}}
    
    -- Math channels
    math_channels JSONB NOT NULL DEFAULT '[]', -- Array of math channel definitions
    
    -- Color settings per import
    import_colors JSONB NOT NULL, -- {"import_id": "#FF5733"}
    
    -- Graph settings
    graph_heights JSONB NOT NULL DEFAULT '{}', -- {"channel_name": {"height": 250}}
    
    -- UI state
    active_channels TEXT[] DEFAULT '{}', -- Array of currently visible channel names
    metadata JSONB DEFAULT '{}'
);

-- Math Channel Definitions Table
CREATE TABLE IF NOT EXISTS math_channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_id UUID REFERENCES viz_snapshots(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    expression TEXT NOT NULL, -- Mathematical expression
    input_channels TEXT[] NOT NULL, -- Array of input channel names
    units VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Processing Logs Table
CREATE TABLE IF NOT EXISTS processing_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    import_id UUID REFERENCES import_objects(id) ON DELETE CASCADE,
    log_level VARCHAR(20) NOT NULL, -- INFO, WARNING, ERROR
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_import_objects_created_at ON import_objects(created_at);
CREATE INDEX IF NOT EXISTS idx_import_objects_name ON import_objects(name);
CREATE INDEX IF NOT EXISTS idx_channel_data_import_id ON channel_data(import_id);
CREATE INDEX IF NOT EXISTS idx_channel_data_channel_name ON channel_data(channel_name);
CREATE INDEX IF NOT EXISTS idx_viz_snapshots_created_at ON viz_snapshots(created_at);
CREATE INDEX IF NOT EXISTS idx_viz_snapshots_name ON viz_snapshots(name);
CREATE INDEX IF NOT EXISTS idx_processing_logs_import_id ON processing_logs(import_id);

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_channel_data_points ON channel_data USING GIN(data_points);
CREATE INDEX IF NOT EXISTS idx_viz_snapshots_import_ids ON viz_snapshots USING GIN(import_ids);
CREATE INDEX IF NOT EXISTS idx_viz_snapshots_time_settings ON viz_snapshots USING GIN(time_settings);
CREATE INDEX IF NOT EXISTS idx_viz_snapshots_channel_visibility ON viz_snapshots USING GIN(channel_visibility);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_import_objects_updated_at BEFORE UPDATE ON import_objects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_viz_snapshots_updated_at BEFORE UPDATE ON viz_snapshots FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW import_summary AS
SELECT 
    io.id,
    io.name,
    io.created_at,
    io.channel_count,
    io.total_data_points,
    io.processing_status,
    COUNT(cd.id) as stored_channels
FROM import_objects io
LEFT JOIN channel_data cd ON io.id = cd.import_id
GROUP BY io.id, io.name, io.created_at, io.channel_count, io.total_data_points, io.processing_status;

CREATE OR REPLACE VIEW snapshot_details AS
SELECT 
    vs.id,
    vs.name,
    vs.created_at,
    vs.sidebar_ratio,
    array_length(vs.import_ids, 1) as import_count,
    array_length(vs.math_channels, 1) as math_channel_count,
    io.name as import_names
FROM viz_snapshots vs
LEFT JOIN import_objects io ON io.id = ANY(vs.import_ids);

-- Sample data for testing (optional)
-- INSERT INTO import_objects (name, description, file_size_bytes, channel_count, total_data_points, time_range_start, time_range_end, processing_status)
-- VALUES ('Test Import', 'Sample OBD2 data', 1024, 5, 100, 0, 10, 'completed')
-- RETURNING id;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO obd2_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO obd2_user;
