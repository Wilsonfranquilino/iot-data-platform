"""
Historical Backfill — Gerador de seed data industrial.

Gera 12 meses de dados simulados com os 7 padrões de eventos definidos
no Discovery & Escopo v3, salvando CSVs em postgres/seeds/.

Uso:
    python simulator/historical_backfill.py             # 12 meses completos
    python simulator/historical_backfill.py --months 1  # 1 mês
    python simulator/historical_backfill.py --fast      # 1 dia, 1 ativo (CI)
"""
from __future__ import annotations
import argparse, csv, random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np
# tqdm optional

ROOT      = Path(__file__).parent.parent
SEEDS_DIR = ROOT / "postgres" / "seeds"
SEEDS_DIR.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(seed=42)
random.seed(42)
INTERVAL_SECONDS = 30

# ── Definição dos ativos ──────────────────────────────────────────────────────
@dataclass
class AssetDef:
    asset_id: str; name: str; asset_type: str; line_id: str
    manufacturer: str; model: str; installed_at: str
    temp_min: float=20.0; temp_max: float=85.0
    vib_min:  float=0.1;  vib_max:  float=4.5
    pressure_min: float=2.0; pressure_max: float=8.0
    rpm_min: int=800; rpm_max: int=3600
    current_min: float=5.0; current_max: float=45.0
    flow_min: float=10.0; flow_max: float=120.0
    energy_base: float=50.0

ASSETS: list[AssetDef] = [
    AssetDef("CMP-001","Compressor 01 - Linha A","compressor","LINE_A","Atlas Copco","GA-110","2022-03-15",energy_base=75.0),
    AssetDef("CMP-002","Compressor 02 - Linha A","compressor","LINE_A","Atlas Copco","GA-110","2022-03-15",energy_base=78.0),
    AssetDef("CMP-003","Compressor 01 - Linha B","compressor","LINE_B","Schulz","MSV-40","2021-07-20",energy_base=72.0),
    AssetDef("CMP-004","Compressor 02 - Linha B","compressor","LINE_B","Schulz","MSV-40","2021-07-20",energy_base=80.0),
    AssetDef("MTR-001","Motor Elétrico 01 - Linha A","motor","LINE_A","WEG","W22 75cv","2023-01-10",rpm_min=1200,rpm_max=3000,energy_base=30.0,temp_min=25.0,temp_max=80.0),
    AssetDef("MTR-002","Motor Elétrico 02 - Linha A","motor","LINE_A","WEG","W22 75cv","2023-01-10",rpm_min=1200,rpm_max=3000,energy_base=28.0,temp_min=25.0,temp_max=80.0),
    AssetDef("MTR-003","Motor Elétrico 01 - Linha B","motor","LINE_B","Siemens","SIMOTICS 90kW","2022-09-05",rpm_min=1200,rpm_max=3000,energy_base=32.0,temp_min=25.0,temp_max=80.0),
    AssetDef("MTR-004","Motor Elétrico 02 - Linha B","motor","LINE_B","Siemens","SIMOTICS 90kW","2022-09-05",rpm_min=1200,rpm_max=3000,energy_base=31.0,temp_min=25.0,temp_max=80.0),
    AssetDef("BMB-001","Bomba Hidráulica 01 - Linha A","pump","LINE_A","KSB","Etanorm 32-160","2022-06-01",rpm_min=800,rpm_max=1800,energy_base=20.0),
    AssetDef("BMB-002","Bomba Hidráulica 02 - Linha A","pump","LINE_A","KSB","Etanorm 32-160","2022-06-01",rpm_min=800,rpm_max=1800,energy_base=22.0),
    AssetDef("BMB-003","Bomba Hidráulica 01 - Linha B","pump","LINE_B","Grundfos","NK 32-160","2021-11-15",rpm_min=800,rpm_max=1800,energy_base=19.0),
    AssetDef("BMB-004","Bomba Hidráulica 02 - Linha B","pump","LINE_B","Grundfos","NK 32-160","2021-11-15",rpm_min=800,rpm_max=1800,energy_base=21.0),
]
ASSETS_BY_ID = {a.asset_id: a for a in ASSETS}

TECHNICIANS = [
    {"technician_id":1,"name":"Carlos Mendes", "specialty":"mecanica",      "shift":"A"},
    {"technician_id":2,"name":"Ana Silva",      "specialty":"eletrica",      "shift":"B"},
    {"technician_id":3,"name":"Pedro Costa",    "specialty":"instrumentacao","shift":"C"},
    {"technician_id":4,"name":"Julia Ferreira", "specialty":"mecanica",      "shift":"A"},
]

# ── helpers ───────────────────────────────────────────────────────────────────
def _g(lo, hi, sf=0.05):
    return float(np.clip(rng.normal((lo+hi)/2, (hi-lo)*sf), lo, hi))

def normal_reading(a: AssetDef, ts: datetime) -> dict:
    return {
        "asset_id":      a.asset_id,
        "read_at":       ts.isoformat(),
        "temperature_c": round(_g(a.temp_min,     a.temp_max),     2),
        "vibration_mms": round(_g(a.vib_min,      a.vib_max),      3),
        "pressure_bar":  round(_g(a.pressure_min, a.pressure_max), 2) if a.asset_type in ("compressor","pump") else None,
        "rpm":           int(_g(a.rpm_min, a.rpm_max))               if a.asset_type in ("motor","pump")       else None,
        "current_a":     round(_g(a.current_min,  a.current_max),  2) if a.asset_type == "motor"              else None,
        "flow_lpm":      round(_g(a.flow_min,     a.flow_max),     2) if a.asset_type == "pump"               else None,
        "energy_kwh":    round(a.energy_base * _g(0.9, 1.1), 3),
        "status":        "RUNNING",
        "line_id":       a.line_id,
        "source":        "simulator",
    }

# ── 7 padrões de eventos ──────────────────────────────────────────────────────
def p_heating(r, hours):
    r["temperature_c"] = round(min(r["temperature_c"] + random.uniform(2,5)*hours, 115.0), 2)
    return r

def p_fault(r):
    r["status"] = "FAULT"
    if random.random() < 0.55:
        r["temperature_c"] = round(random.uniform(105,130), 2)
        r["vibration_mms"] = round(random.uniform(11, 16),  3)
        if r.get("pressure_bar") is not None: r["pressure_bar"] = round(random.uniform(9.5,12),2)
    else:
        for k in ("temperature_c","vibration_mms","pressure_bar","rpm","current_a","flow_lpm","energy_kwh"):
            r[k] = (0 if k=="rpm" else (0.0 if r.get(k) is not None else None))
    return r

def p_maint(r):
    r["status"] = "MAINT"
    for k in ("temperature_c","vibration_mms","pressure_bar","rpm","current_a","flow_lpm","energy_kwh"):
        r[k] = None
    return r

def p_bearing(r, days):
    r["vibration_mms"] = round(min(r["vibration_mms"] + 0.04*days, 12.0), 3)
    return r

def p_energy(r):
    if r.get("energy_kwh") is not None:
        r["energy_kwh"] = round(r["energy_kwh"] * random.uniform(2.0,2.6), 3)
    return r

def p_corrupt(r):
    cands = [k for k in ("temperature_c","vibration_mms","pressure_bar") if r.get(k) is not None]
    if cands:
        k = random.choice(cands)
        r[k] = None if random.random()<0.5 else random.choice([-999.0,9999.0])
    return r

# ── Plano de eventos ──────────────────────────────────────────────────────────
@dataclass
class Plan:
    fault_times:     list[datetime] = field(default_factory=list)
    heat_windows:    list[tuple] = field(default_factory=list)
    maint_windows:   list[tuple] = field(default_factory=list)
    bearing_start:   datetime | None = None
    energy_windows:  list[tuple] = field(default_factory=list)
    status_events:   list[tuple] = field(default_factory=list)

def make_plan(a: AssetDef, start: datetime, end: datetime) -> Plan:
    p = Plan()
    if random.random() < 0.30:
        p.bearing_start = start + timedelta(days=random.uniform(20,(end-start).days*0.4))
    cursor = start
    while cursor < end:
        # falha corretiva
        ft = cursor + timedelta(days=random.uniform(18,28), hours=random.uniform(0,23))
        if ft < end:
            p.fault_times.append(ft)
            hs = ft - timedelta(hours=random.uniform(4,8))
            p.heat_windows.append((hs, ft))
            ms = ft + timedelta(minutes=random.uniform(10,30))
            me = ms + timedelta(hours=random.uniform(2,6))
            p.maint_windows.append((ms, me))
            p.status_events += [(ft,"FAULT","RUNNING"),(ms,"MAINT","FAULT"),(me,"RUNNING","MAINT")]
        # manutenção preventiva
        pt = cursor + timedelta(days=random.uniform(5,15), hours=random.uniform(6,10))
        if pt < end:
            pe = pt + timedelta(hours=random.uniform(2,4))
            p.maint_windows.append((pt,pe))
            p.status_events += [(pt,"MAINT","RUNNING"),(pe,"RUNNING","MAINT")]
        # anomalia de energia
        et = cursor + timedelta(days=random.uniform(1,28))
        if et < end:
            p.energy_windows.append((et, et+timedelta(hours=random.uniform(1,4))))
        cursor += timedelta(days=30)
    p.status_events.sort(key=lambda x: x[0])
    return p

def classify(ts: datetime, p: Plan, a: AssetDef) -> dict:
    r = normal_reading(a, ts)
    for ms,me in p.maint_windows:
        if ms <= ts <= me: return p_maint(r)
    for ft in p.fault_times:
        if abs((ts-ft).total_seconds()) <= INTERVAL_SECONDS/2: return p_fault(r)
    for hs,he in p.heat_windows:
        if hs <= ts < he: r = p_heating(r, (ts-hs).total_seconds()/3600)
    if p.bearing_start and ts >= p.bearing_start:
        r = p_bearing(r, (ts-p.bearing_start).days)
    for es,ee in p.energy_windows:
        if es <= ts <= ee: r = p_energy(r)
    if random.random() < 0.02: r = p_corrupt(r)
    return r

# ── Escrita dos CSVs auxiliares ───────────────────────────────────────────────
def write_assets():
    path = SEEDS_DIR/"assets.csv"
    with open(path,"w",newline="") as f:
        w = csv.DictWriter(f, ["asset_id","name","asset_type","line_id","manufacturer","model","installed_at"])
        w.writeheader()
        for a in ASSETS:
            w.writerow({"asset_id":a.asset_id,"name":a.name,"asset_type":a.asset_type,
                        "line_id":a.line_id,"manufacturer":a.manufacturer,"model":a.model,"installed_at":a.installed_at})
    print(f"   ✅ assets.csv — {len(ASSETS)} registros")

def write_technicians():
    path = SEEDS_DIR/"technicians.csv"
    with open(path,"w",newline="") as f:
        w = csv.DictWriter(f, ["technician_id","name","specialty","shift"])
        w.writeheader(); w.writerows(TECHNICIANS)
    print(f"   ✅ technicians.csv — {len(TECHNICIANS)} registros")

def write_status_log(plans: dict, start: datetime):
    rows = []
    for aid, p in plans.items():
        rows.append({"asset_id":aid,"status":"RUNNING","previous_status":None,
                     "changed_at":start.isoformat(),"notes":"inicio do periodo simulado"})
        labels = {"FAULT":"falha detectada","MAINT":"manutenção iniciada","RUNNING":"retorno à operação"}
        for (at,st,prev) in p.status_events:
            rows.append({"asset_id":aid,"status":st,"previous_status":prev,
                         "changed_at":at.isoformat(),"notes":labels.get(st,"")})
    rows.sort(key=lambda r:(r["asset_id"],r["changed_at"]))
    path = SEEDS_DIR/"asset_status_log.csv"
    with open(path,"w",newline="") as f:
        w = csv.DictWriter(f,["asset_id","status","previous_status","changed_at","notes"])
        w.writeheader(); w.writerows(rows)
    print(f"   ✅ asset_status_log.csv — {len(rows):,} registros")

def write_maintenance(plans: dict):
    rows = []
    rc_corr = ["Superaquecimento por falha de lubrificação","Desgaste de rolamento",
               "Vibração excessiva — desbalanceamento","Sobrecarga elétrica","Falha de vedação"]
    rc_prev = ["Manutenção periódica programada","Troca de filtros e lubrificação",
               "Inspeção e ajuste de correia","Verificação de alinhamento"]
    for aid, p in plans.items():
        for ms,me in sorted(p.maint_windows, key=lambda x:x[0]):
            is_corr = any(abs((ms-ft).total_seconds())<7200 for ft in p.fault_times)
            t = random.choice(TECHNICIANS)
            lo,hi = (2000,8000) if is_corr else (500,2000)
            rows.append({"asset_id":aid,"order_type":"corrective" if is_corr else "preventive",
                         "started_at":ms.isoformat(),"finished_at":me.isoformat(),
                         "technician_id":t["technician_id"],"cost_brl":round(random.uniform(lo,hi),2),
                         "root_cause":random.choice(rc_corr if is_corr else rc_prev)})
    rows.sort(key=lambda r:r["started_at"])
    path = SEEDS_DIR/"maintenance_orders.csv"
    with open(path,"w",newline="") as f:
        w = csv.DictWriter(f,["asset_id","order_type","started_at","finished_at","technician_id","cost_brl","root_cause"])
        w.writeheader(); w.writerows(rows)
    print(f"   ✅ maintenance_orders.csv — {len(rows):,} registros")

# ── Main ──────────────────────────────────────────────────────────────────────
def generate(months=12, fast=False):
    end_dt   = datetime.now(tz=timezone.utc).replace(second=0, microsecond=0)
    start_dt = end_dt - timedelta(days=months*30)
    assets   = [ASSETS[0]] if fast else ASSETS
    if fast: start_dt = end_dt - timedelta(days=1)
    total_ts = int((end_dt-start_dt).total_seconds()/INTERVAL_SECONDS)

    print("\n" + "═"*58)
    print("  Industrial Asset Monitor — Seed Data Generator")
    print("═"*58)
    print(f"  Período : {start_dt.date()} → {end_dt.date()}")
    print(f"  Ativos  : {len(assets)}")
    print(f"  ~{total_ts*len(assets):,} leituras estimadas")
    print("═"*58+"\n")

    print("📋 CSVs de referência...")
    write_assets(); write_technicians()

    print("\n📅 Planejando eventos...")
    plans = {}
    for a in assets:
        plans[a.asset_id] = make_plan(a, start_dt, end_dt)
        p = plans[a.asset_id]
        print(f"   {a.asset_id}: {len(p.fault_times)} falhas · {len(p.maint_windows)} manutenções")
    write_status_log(plans, start_dt)
    write_maintenance(plans)

    print(f"\n⚙️  Gerando sensor_readings.csv...")
    out_path = SEEDS_DIR/"sensor_readings.csv"
    fields = ["asset_id","read_at","temperature_c","vibration_mms","pressure_bar",
              "rpm","current_a","flow_lpm","energy_kwh","status","line_id","source"]
    total=fault=maint=corrupt=0
    interval = timedelta(seconds=INTERVAL_SECONDS)

    with open(out_path,"w",newline="") as f:
        writer = csv.DictWriter(f, fields); writer.writeheader()
        ts = start_dt; tick = 0
        while ts <= end_dt:
            for a in assets:
                row = classify(ts, plans[a.asset_id], a)
                writer.writerow(row); total+=1
                if row["status"]=="FAULT": fault+=1
                elif row["status"]=="MAINT": maint+=1
                if row["status"]=="RUNNING" and any(row.get(k) in (None,-999.0,9999.0)
                    for k in ("temperature_c","vibration_mms")): corrupt+=1
            ts += interval; tick+=1
            if tick % 2880 == 0:
                pct = tick/total_ts*100
                print(f"   {pct:.0f}% — {tick:,}/{total_ts:,} timestamps", flush=True)

    print(f"\n✅ sensor_readings.csv — {total:,} leituras")
    print(f"   FAULT  : {fault:,}  ({fault/total*100:.1f}%)")
    print(f"   MAINT  : {maint:,}  ({maint/total*100:.1f}%)")
    print(f"   CORRUPT: {corrupt:,} ({corrupt/total*100:.1f}%)")
    print(f"   NORMAL : {total-fault-maint:,}")
    print(f"\n📁 Arquivos em: {SEEDS_DIR}")
    print("   Próximo: make seed-data  →  dbt seed carrega no Postgres\n")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--months", type=int, default=12)
    p.add_argument("--fast",   action="store_true")
    args = p.parse_args()
    generate(months=args.months, fast=args.fast)
