CREATE TABLE IF NOT EXISTS agricultural_prices (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    source_record_id VARCHAR(100),
    product_type VARCHAR(50) NOT NULL,
    product_name VARCHAR(150) NOT NULL,
    market_name VARCHAR(150),
    province VARCHAR(100),
    reported_date DATE NOT NULL,
    price_min NUMERIC(10, 2),
    price_max NUMERIC(10, 2),
    price_value NUMERIC(10, 2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    currency VARCHAR(10) DEFAULT 'THB',
    source_url TEXT,
    collected_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_product_market_date UNIQUE (source_name, product_name, market_name, reported_date, unit)
);

CREATE TABLE IF NOT EXISTS rejected_records (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    raw_data JSONB,
    rejection_reason TEXT,
    rejected_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id VARCHAR(100) PRIMARY KEY,
    dag_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    start_time TIMESTAMP WITHOUT TIME ZONE,
    end_time TIMESTAMP WITHOUT TIME ZONE,
    records_extracted INT DEFAULT 0,
    records_passed INT DEFAULT 0,
    records_rejected INT DEFAULT 0,
    records_upserted INT DEFAULT 0,
    error_message TEXT
);