"""
Definições dos ativos industriais monitorados.
12 equipamentos em 2 linhas de produção — conforme Discovery e Escopo v3.
"""
from dataclasses import dataclass, field
from typing import Literal

AssetType = Literal["compressor", "motor", "pump"]
LineId    = Literal["LINE_A", "LINE_B"]


@dataclass
class AssetConfig:
    asset_id:     str
    name:         str
    asset_type:   AssetType
    line_id:      LineId

    # ── ranges normais de operação ──────────────────────────────────────────
    temp_min:     float = 20.0
    temp_max:     float = 85.0
    vib_min:      float = 0.1
    vib_max:      float = 4.5
    pressure_min: float = 2.0
    pressure_max: float = 8.0
    rpm_min:      int   = 800
    rpm_max:      int   = 3600
    current_min:  float = 5.0
    current_max:  float = 45.0
    flow_min:     float = 10.0
    flow_max:     float = 120.0
    energy_base:  float = 50.0   # kWh base por hora


# ── Thresholds de alerta (compartilhados) ──────────────────────────────────
THRESHOLDS = {
    "temperature_c": {"warning": 90.0,  "critical": 100.0},
    "vibration_mms": {"warning": 7.0,   "critical": 10.0},
    "pressure_bar":  {"low_critical": 1.5, "high_critical": 9.0},
    "current_a":     {"critical": 50.0},
    "flow_lpm":      {"warning": 8.0},
    "rpm":           {"warning_motor": 500},
    "energy_kwh":    {"anomaly_multiplier": 2.0},
    "sensor_offline_minutes": 5,
}


# ── Catálogo de ativos — 12 equipamentos, 2 linhas ─────────────────────────
ASSETS: list[AssetConfig] = [
    # Linha A — Compressores
    AssetConfig("CMP-001", "Compressor 01 - Linha A", "compressor", "LINE_A",
                energy_base=75.0),
    AssetConfig("CMP-002", "Compressor 02 - Linha A", "compressor", "LINE_A",
                energy_base=78.0),
    # Linha B — Compressores
    AssetConfig("CMP-003", "Compressor 01 - Linha B", "compressor", "LINE_B",
                energy_base=72.0),
    AssetConfig("CMP-004", "Compressor 02 - Linha B", "compressor", "LINE_B",
                energy_base=80.0),

    # Linha A — Motores elétricos
    AssetConfig("MTR-001", "Motor Elétrico 01 - Linha A", "motor", "LINE_A",
                rpm_min=1200, rpm_max=3000, energy_base=30.0),
    AssetConfig("MTR-002", "Motor Elétrico 02 - Linha A", "motor", "LINE_A",
                rpm_min=1200, rpm_max=3000, energy_base=28.0),
    # Linha B — Motores elétricos
    AssetConfig("MTR-003", "Motor Elétrico 01 - Linha B", "motor", "LINE_B",
                rpm_min=1200, rpm_max=3000, energy_base=32.0),
    AssetConfig("MTR-004", "Motor Elétrico 02 - Linha B", "motor", "LINE_B",
                rpm_min=1200, rpm_max=3000, energy_base=31.0),

    # Linha A — Bombas hidráulicas
    AssetConfig("BMB-001", "Bomba Hidráulica 01 - Linha A", "pump", "LINE_A",
                rpm_min=800, rpm_max=1800, energy_base=20.0),
    AssetConfig("BMB-002", "Bomba Hidráulica 02 - Linha A", "pump", "LINE_A",
                rpm_min=800, rpm_max=1800, energy_base=22.0),
    # Linha B — Bombas hidráulicas
    AssetConfig("BMB-003", "Bomba Hidráulica 01 - Linha B", "pump", "LINE_B",
                rpm_min=800, rpm_max=1800, energy_base=19.0),
    AssetConfig("BMB-004", "Bomba Hidráulica 02 - Linha B", "pump", "LINE_B",
                rpm_min=800, rpm_max=1800, energy_base=21.0),
]

ASSETS_BY_ID: dict[str, AssetConfig] = {a.asset_id: a for a in ASSETS}
