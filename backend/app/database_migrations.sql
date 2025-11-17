-- Database schema for feedback learning system
-- Created: 2025-11-13

-- 1. Field Definitions - שדות שנלמדו מפידבק
CREATE TABLE IF NOT EXISTS field_definitions (
    id SERIAL PRIMARY KEY,
    field_name VARCHAR(100) UNIQUE NOT NULL,
    field_type VARCHAR(50) NOT NULL,  -- 'text', 'number', 'date', 'currency'
    field_category VARCHAR(50),  -- 'employee', 'salary', 'deduction', 'addition', 'tax'
    extraction_patterns JSON,  -- List of regex patterns
    validation_rules JSON,
    learned_from_feedback BOOLEAN DEFAULT FALSE,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP,
    occurrence_count INTEGER DEFAULT 1,
    confidence_score FLOAT DEFAULT 0.5,
    active BOOLEAN DEFAULT FALSE
);

-- 2. Parsing Patterns - תבניות לחילוץ נתונים
CREATE TABLE IF NOT EXISTS parsing_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type VARCHAR(50) NOT NULL,  -- 'field_extraction', 'payslip_separator', 'table_structure'
    pattern_regex TEXT NOT NULL,
    pattern_description TEXT,
    field_name VARCHAR(100),
    context_hints JSON,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    confidence_score FLOAT DEFAULT 0.5,
    created_from_feedback BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

-- 3. Split Improvements - שיפורי פיצול תלושים
CREATE TABLE IF NOT EXISTS split_improvements (
    id SERIAL PRIMARY KEY,
    original_file_path VARCHAR(500),
    detected_payslip_count INTEGER,
    actual_payslip_count INTEGER,
    split_method VARCHAR(100),  -- 'employee_id', 'page_break', 'employee_name', 'custom'
    split_accuracy FLOAT,
    user_corrections JSON,
    learned_patterns JSON,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Enhanced Feedback Entry - הרחבת טבלת המשוב הקיימת
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS payslip_id INTEGER REFERENCES payslips(id);
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS field_name VARCHAR(100);
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS original_value TEXT;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS corrected_value TEXT;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 0.5;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS applied_at TIMESTAMP;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS improvement_result JSON;

-- 5. Agent Performance Metrics - מדדי ביצועי סוכנים
CREATE TABLE IF NOT EXISTS agent_metrics (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL,
    metric_date DATE DEFAULT CURRENT_DATE,
    total_analyses INTEGER DEFAULT 0,
    successful_analyses INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    false_negatives INTEGER DEFAULT 0,
    accuracy_score FLOAT,
    avg_processing_time_ms INTEGER,
    feedback_count INTEGER DEFAULT 0,
    improvements_applied INTEGER DEFAULT 0,
    UNIQUE(agent_name, metric_date)
);

-- 6. Learning History - היסטוריית למידה
CREATE TABLE IF NOT EXISTS learning_history (
    id SERIAL PRIMARY KEY,
    learning_type VARCHAR(50), -- 'field', 'pattern', 'split', 'validation'
    before_state JSON,
    after_state JSON,
    improvement_metrics JSON,
    triggered_by VARCHAR(100), -- 'user_feedback', 'automatic', 'batch_learning'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_feedback_payslip ON feedback(payslip_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_agent ON feedback(agent_name);
CREATE INDEX IF NOT EXISTS idx_field_definitions_name ON field_definitions(field_name);
CREATE INDEX IF NOT EXISTS idx_field_definitions_confidence ON field_definitions(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_parsing_patterns_type ON parsing_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_parsing_patterns_confidence ON parsing_patterns(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_date ON agent_metrics(metric_date DESC);

-- Initial data
INSERT INTO agent_metrics (agent_name, metric_date, total_analyses)
VALUES
    ('parser', CURRENT_DATE, 0),
    ('validator', CURRENT_DATE, 0),
    ('analyzer', CURRENT_DATE, 0),
    ('reporter', CURRENT_DATE, 0)
ON CONFLICT (agent_name, metric_date) DO NOTHING;