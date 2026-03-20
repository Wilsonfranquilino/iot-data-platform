"""
Live Streaming — Simulador IoT em tempo real.

Publica leituras de todos os 12 ativos no Redpanda a cada 30 segundos.
Mantém estado por ativo para simular falhas e anomalias progressivas.

Uso:
    python simulator/live_streaming.py
    make simulate
"""
import json
import os
import random
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from kafka import KafkaProducer

from models import ASSETS
from historical_backfill import AssetSimulator

load_dotenv()

BROKERS       = os.getenv("REDPANDA_BROKERS", "localhost:19092")
TOPIC         = "sensor.readings.raw"
INTERVAL      = 30   # segundos entre leituras


def make_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=BROKERS.split(","),
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
        acks="all",
        retries=5,
    )


def main():
    print(f"🔴 Live Streaming iniciado")
    print(f"   Broker : {BROKERS}")
    print(f"   Tópico : {TOPIC}")
    print(f"   Ativos : {len(ASSETS)}")
    print(f"   Intervalo: {INTERVAL}s | Ctrl+C para parar\n")

    producer = make_producer()

    # Simuladores com estado persistente
    simulators = {a.asset_id: AssetSimulator(a) for a in ASSETS}
    now = datetime.now(tz=timezone.utc)
    for sim in simulators.values():
        from datetime import timedelta
        sim.plan_events(now, now + timedelta(days=365))

    iteration = 0
    while True:
        ts = datetime.now(tz=timezone.utc)
        iteration += 1

        for sim in simulators.values():
            reading = sim.generate_reading(ts)
            if not reading:
                continue

            producer.send(
                topic=TOPIC,
                key=reading["asset_id"],
                value=reading,
            )

        producer.flush()

        alerts = [
            a.asset_id for a in ASSETS
            if simulators[a.asset_id].generate_reading(ts) and
               simulators[a.asset_id].generate_reading(ts).get("status") == "FAULT"
        ]

        status_str = f"🔴 FAULT: {alerts}" if alerts else "🟢 OK"
        print(f"[{ts.strftime('%H:%M:%S')}] iter={iteration:04d} | "
              f"{len(ASSETS)} ativos publicados | {status_str}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
