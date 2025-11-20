-- Development Planning Module Migration v1.0.0
-- Create features and feature_steps tables for development planning

-- Create features table
CREATE TABLE IF NOT EXISTS features (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'planned',
    priority VARCHAR(20) DEFAULT 'medium',
    target_date DATE,
    created_by_id UUID NOT NULL REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_feature_status CHECK (status IN ('planned', 'in_development', 'testing', 'completed', 'on_hold')),
    CONSTRAINT valid_feature_priority CHECK (priority IN ('low', 'medium', 'high', 'critical'))
);

-- Create feature_steps table
CREATE TABLE IF NOT EXISTS feature_steps (
    id SERIAL PRIMARY KEY,
    feature_id INTEGER NOT NULL REFERENCES features(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'todo',
    step_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_step_status CHECK (status IN ('todo', 'in_progress', 'done'))
);

-- Create feature_comments table
CREATE TABLE IF NOT EXISTS feature_comments (
    id SERIAL PRIMARY KEY,
    feature_id INTEGER NOT NULL REFERENCES features(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id),
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for features
CREATE INDEX IF NOT EXISTS idx_features_status ON features(status);
CREATE INDEX IF NOT EXISTS idx_features_priority ON features(priority);
CREATE INDEX IF NOT EXISTS idx_features_created_by ON features(created_by_id);
CREATE INDEX IF NOT EXISTS idx_features_target_date ON features(target_date);
CREATE INDEX IF NOT EXISTS idx_features_created_at ON features(created_at DESC);

-- Create indexes for feature_steps
CREATE INDEX IF NOT EXISTS idx_feature_steps_feature_id ON feature_steps(feature_id);
CREATE INDEX IF NOT EXISTS idx_feature_steps_status ON feature_steps(status);
CREATE INDEX IF NOT EXISTS idx_feature_steps_order ON feature_steps(feature_id, step_order);

-- Create indexes for feature_comments
CREATE INDEX IF NOT EXISTS idx_feature_comments_feature_id ON feature_comments(feature_id);
CREATE INDEX IF NOT EXISTS idx_feature_comments_user_id ON feature_comments(user_id);

-- Add development module to modules table
INSERT INTO modules (module_key, module_name, description, icon, display_order, is_active)
VALUES ('development', 'Development Planning', 'Plan features and track development progress', 'code', 11, TRUE)
ON CONFLICT (module_key) DO NOTHING;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_features_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_features_updated_at
    BEFORE UPDATE ON features
    FOR EACH ROW
    EXECUTE FUNCTION update_features_updated_at();

CREATE OR REPLACE TRIGGER trigger_feature_steps_updated_at
    BEFORE UPDATE ON feature_steps
    FOR EACH ROW
    EXECUTE FUNCTION update_features_updated_at();

CREATE OR REPLACE TRIGGER trigger_feature_comments_updated_at
    BEFORE UPDATE ON feature_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_features_updated_at();
