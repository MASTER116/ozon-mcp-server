-- PostgreSQL initialization script for Ozon MCP Server
-- Runs once on first container start (when data volume is empty)

-- Create audit table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tool_name TEXT NOT NULL,
    parameters JSONB,
    result_status TEXT NOT NULL CHECK (result_status IN (
        'success', 'error', 'rate_limited', 'unauthorized', 'validation_error'
    )),
    response_time_ms DOUBLE PRECISION,
    error_message TEXT,
    ozon_trace_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_tool ON audit_log (tool_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_status ON audit_log (result_status);
CREATE INDEX IF NOT EXISTS idx_audit_log_trace ON audit_log (ozon_trace_id) WHERE ozon_trace_id IS NOT NULL;

-- Auto-cleanup: partition-friendly index for date range deletions
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log (created_at);
