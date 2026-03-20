-- ============================================================
-- Industrial Asset Monitor — Schema Operacional (3NF)
-- Simula banco SCADA/MES de planta industrial
-- ============================================================

-- ── Tipos de equipamento ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS asset_types (
    asset_type_id     SERIAL PRIMARY KEY,
    type_name         VARCHAR(50)  NOT NULL UNIQUE,  -- 'compressor', 'motor', 'pump'
    nominal_rpm       INTEGER,
    max_temperature_c FLOAT        NOT NULL DEFAULT 100.0,
    max_vibration_mms FLOAT        NOT NULL DEFAULT 10.0,
    created_at        TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ── Linhas de produção ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS production_lines (
    line_id     SERIAL PRIMARY KEY,
    line_name   VARCHAR(20)  NOT NULL UNIQUE,  -- 'LINE_A', 'LINE_B'
    plant_area  VARCHAR(100),
    shift_hours INTEGER      NOT NULL DEFAULT 8,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ── Técnicos de manutenção ───────────────────────────────────
CREATE TABLE IF NOT EXISTS technicians (
    technician_id SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    specialty     VARCHAR(50),  -- 'eletrica', 'mecanica', 'instrumentacao'
    shift         VARCHAR(10),  -- 'A', 'B', 'C'
    active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ── Ativos (equipamentos) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS assets (
    asset_id      VARCHAR(10)  PRIMARY KEY,   -- 'CMP-001', 'MTR-002'
    name          VARCHAR(100) NOT NULL,
    asset_type_id INTEGER      NOT NULL REFERENCES asset_types(asset_type_id),
    line_id       INTEGER      NOT NULL REFERENCES production_lines(line_id),
    manufacturer  VARCHAR(100),
    model         VARCHAR(100),
    serial_number VARCHAR(50),
    installed_at  TIMESTAMP    NOT NULL,
    active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ── Leituras de sensores (tabela de fato — alta frequência) ──
CREATE TABLE IF NOT EXISTS sensor_readings (
    reading_id    BIGSERIAL    PRIMARY KEY,
    asset_id      VARCHAR(10)  NOT NULL REFERENCES assets(asset_id),
    read_at       TIMESTAMP    NOT NULL,
    temperature_c FLOAT,          -- °C          | alerta: >90 warn, >100 crit
    vibration_mms FLOAT,          -- mm/s        | alerta: >7 warn, >10 crit
    pressure_bar  FLOAT,          -- bar         | alerta: <1.5 ou >9.0 crit
    rpm           INTEGER,        -- RPM         | alerta: <500 warn (motor)
    current_a     FLOAT,          -- Amperes     | alerta: >50 crit
    flow_lpm      FLOAT,          -- L/min       | alerta: <8 warn (bomba)
    energy_kwh    FLOAT,          -- kWh cumulativo
    source        VARCHAR(20)  DEFAULT 'simulator'
);

-- Particionamento implícito via índice em read_at
CREATE INDEX IF NOT EXISTS idx_sensor_readings_asset_time
    ON sensor_readings (asset_id, read_at DESC);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_time
    ON sensor_readings (read_at DESC);

-- ── Log de status dos ativos ─────────────────────────────────
CREATE TABLE IF NOT EXISTS asset_status_log (
    log_id          BIGSERIAL   PRIMARY KEY,
    asset_id        VARCHAR(10) NOT NULL REFERENCES assets(asset_id),
    status          VARCHAR(20) NOT NULL,   -- RUNNING, IDLE, FAULT, MAINT
    previous_status VARCHAR(20),
    changed_at      TIMESTAMP   NOT NULL,
    duration_minutes INTEGER,              -- preenchido quando status fecha
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_status_log_asset_time
    ON asset_status_log (asset_id, changed_at DESC);

-- ── Ordens de manutenção ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS maintenance_orders (
    order_id      BIGSERIAL    PRIMARY KEY,
    asset_id      VARCHAR(10)  NOT NULL REFERENCES assets(asset_id),
    order_type    VARCHAR(20)  NOT NULL,   -- 'corrective', 'preventive', 'predictive'
    started_at    TIMESTAMP    NOT NULL,
    finished_at   TIMESTAMP,
    technician_id INTEGER      REFERENCES technicians(technician_id),
    cost_brl      FLOAT,
    root_cause    TEXT,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Seed data inicial — tipos, linhas e técnicos
-- (ativos e leituras são inseridos pelo simulador Python)
-- ============================================================

INSERT INTO asset_types (type_name, nominal_rpm, max_temperature_c, max_vibration_mms)
VALUES
    ('compressor',  3600, 100.0, 10.0),
    ('motor',       3000, 100.0, 10.0),
    ('pump',        1800, 100.0, 10.0)
ON CONFLICT (type_name) DO NOTHING;

INSERT INTO production_lines (line_name, plant_area, shift_hours)
VALUES
    ('LINE_A', 'Área Norte', 8),
    ('LINE_B', 'Área Sul',   8)
ON CONFLICT (line_name) DO NOTHING;

INSERT INTO technicians (name, specialty, shift)
VALUES
    ('Carlos Mendes',  'mecanica',        'A'),
    ('Ana Silva',      'eletrica',        'B'),
    ('Pedro Costa',    'instrumentacao',  'C'),
    ('Julia Ferreira', 'mecanica',        'A')
ON CONFLICT DO NOTHING;
