CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY,
    supplier_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    country_code TEXT NOT NULL,
    region TEXT,
    lead_time_days INTEGER,
    reliability_score REAL,
    active INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    brand TEXT,
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive', 'discontinued')),
    default_supplier_id INTEGER,
    origin_country_code TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (default_supplier_id) REFERENCES suppliers (id)
);

CREATE TABLE IF NOT EXISTS product_suppliers (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    is_primary INTEGER NOT NULL,
    supplier_sku TEXT,
    lead_time_days INTEGER,
    min_order_qty INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (product_id, supplier_id),
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sales_history (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    sales_date TEXT NOT NULL,
    channel TEXT NOT NULL,
    region_code TEXT NOT NULL,
    units_sold INTEGER NOT NULL,
    gross_revenue REAL NOT NULL,
    net_revenue REAL NOT NULL,
    returns_qty INTEGER NOT NULL,
    promo_flag INTEGER NOT NULL,
    stockout_flag INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    warehouse_code TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    on_hand_qty INTEGER NOT NULL,
    reserved_qty INTEGER NOT NULL,
    inbound_qty INTEGER NOT NULL,
    reorder_point INTEGER NOT NULL,
    safety_stock INTEGER NOT NULL,
    days_of_cover REAL,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fulfillment_snapshots (
    id INTEGER PRIMARY KEY,
    product_id INTEGER,
    region_code TEXT NOT NULL,
    warehouse_code TEXT,
    captured_at TEXT NOT NULL,
    backlog_orders INTEGER NOT NULL,
    avg_ship_delay_hours REAL NOT NULL,
    on_time_rate REAL NOT NULL,
    sla_risk_level INTEGER NOT NULL CHECK (sla_risk_level BETWEEN 1 AND 5),
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS risk_events (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    risk_type TEXT NOT NULL,
    severity INTEGER NOT NULL CHECK (severity BETWEEN 1 AND 5),
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    country_code TEXT,
    route_code TEXT,
    affected_supplier_id INTEGER,
    affected_product_id INTEGER,
    event_date TEXT,
    detected_at TEXT NOT NULL,
    expires_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('open', 'monitoring', 'resolved')),
    source_url TEXT,
    source_name TEXT,
    citation_snippet TEXT,
    confidence REAL,
    payload_json TEXT,
    FOREIGN KEY (affected_supplier_id) REFERENCES suppliers (id),
    FOREIGN KEY (affected_product_id) REFERENCES products (id)
);

CREATE TABLE IF NOT EXISTS country_risk_scores (
    id INTEGER PRIMARY KEY,
    country_code TEXT NOT NULL,
    score_date TEXT NOT NULL,
    overall_score REAL NOT NULL,
    geopolitical_score REAL NOT NULL,
    tariff_score REAL NOT NULL,
    logistics_score REAL NOT NULL,
    weather_score REAL NOT NULL,
    labor_score REAL NOT NULL,
    active_event_count INTEGER NOT NULL,
    highest_severity INTEGER NOT NULL CHECK (highest_severity BETWEEN 1 AND 5),
    summary TEXT,
    UNIQUE (country_code, score_date)
);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    report_type TEXT NOT NULL,
    scope_type TEXT NOT NULL,
    scope_id TEXT,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'partial', 'failed')),
    requested_by TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    json_path TEXT,
    markdown_path TEXT,
    summary TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    context_scope TEXT NOT NULL CHECK (context_scope IN ('global', 'product', 'supplier', 'country')),
    context_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_message_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    message_text TEXT NOT NULL,
    citations_json TEXT,
    agent_trace_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS imports (
    id TEXT PRIMARY KEY,
    import_type TEXT NOT NULL CHECK (import_type IN ('products', 'suppliers', 'sales', 'inventory', 'fulfillment')),
    filename TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    row_count INTEGER NOT NULL,
    inserted_count INTEGER NOT NULL,
    error_count INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    trigger_type TEXT NOT NULL CHECK (trigger_type IN ('dashboard', 'chat', 'map', 'product', 'report', 'refresh')),
    trigger_ref TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'partial')),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    input_ref TEXT,
    output_ref TEXT,
    error_message TEXT,
    duration_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_suppliers_country_code
    ON suppliers (country_code);

CREATE INDEX IF NOT EXISTS idx_products_sku
    ON products (sku);

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products (category);

CREATE INDEX IF NOT EXISTS idx_product_suppliers_product_id
    ON product_suppliers (product_id);

CREATE INDEX IF NOT EXISTS idx_product_suppliers_supplier_id
    ON product_suppliers (supplier_id);

CREATE INDEX IF NOT EXISTS idx_sales_history_product_date
    ON sales_history (product_id, sales_date);

CREATE INDEX IF NOT EXISTS idx_sales_history_region_channel
    ON sales_history (region_code, channel);

CREATE INDEX IF NOT EXISTS idx_inventory_snapshots_product_snapshot_date
    ON inventory_snapshots (product_id, snapshot_date);

CREATE INDEX IF NOT EXISTS idx_fulfillment_snapshots_product_captured_at
    ON fulfillment_snapshots (product_id, captured_at);

CREATE INDEX IF NOT EXISTS idx_fulfillment_snapshots_region_captured_at
    ON fulfillment_snapshots (region_code, captured_at);

CREATE INDEX IF NOT EXISTS idx_risk_events_country_status
    ON risk_events (country_code, status, severity);

CREATE INDEX IF NOT EXISTS idx_risk_events_supplier_status
    ON risk_events (affected_supplier_id, status);

CREATE INDEX IF NOT EXISTS idx_risk_events_product_status
    ON risk_events (affected_product_id, status);

CREATE INDEX IF NOT EXISTS idx_risk_events_event_date
    ON risk_events (event_date);

CREATE INDEX IF NOT EXISTS idx_country_risk_scores_country_score_date
    ON country_risk_scores (country_code, score_date);

CREATE INDEX IF NOT EXISTS idx_reports_scope_status
    ON reports (scope_type, status, created_at);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at
    ON chat_sessions (updated_at);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created_at
    ON chat_messages (session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_imports_type_started_at
    ON imports (import_type, started_at);

CREATE INDEX IF NOT EXISTS idx_agent_runs_trigger_started_at
    ON agent_runs (trigger_type, started_at);
