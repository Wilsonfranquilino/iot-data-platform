# 🏭 Industrial Asset Monitor

**Plataforma de Dados para Monitoramento e Manutenção Preditiva de Ativos Industriais**

[![CI](https://github.com/Wilsonfranquilino/iot-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Wilsonfranquilino/iot-data-platform/actions)
[![dbt](https://img.shields.io/badge/dbt-1.8+-orange)](https://www.getdbt.com/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.x-yellow)](https://duckdb.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **POC de portfólio** — Analytics Engineering end-to-end: do sensor simulado ao dashboard, passando por Redpanda, Dagster, MinIO + Iceberg, dbt e Metabase. 100% local via Docker, cloud-ready com Terraform.

---

## 📐 Problema de Negócio

Uma planta industrial de pequeno porte (até 20 equipamentos) opera sem nenhum sistema de dados. A manutenção é **100% corretiva** — a equipe só age quando a máquina já falhou. O principal custo é a **perda de produto em processo**: material descartado quando a linha para de surpresa.

**Esta plataforma entrega:**
- Visibilidade em tempo real do estado de cada ativo
- Alertas automáticos para técnicos de manutenção (temperatura, vibração, consumo anômalo)
- KPIs de confiabilidade para a gestão (Disponibilidade, MTBF, MTTR, OEE)
- Dataset de features prontas para modelos de manutenção preditiva (ML)

---

## 🏗️ Arquitetura

```
                    ┌─────────────────────────────────────────────────┐
                    │              ZONA DE CONSUMO                     │
  Gerentes ──────►  │  Metabase Dashboards (Gold via Iceberg)          │
  Técnicos ──────►  │  Alertas em Tempo Real                           │
  Analistas ─────►  │  DuckDB Isolado → mart_availability, mart_alerts  │
  Data Scientists ► │  Jupyter + PyIceberg → Silver + feat_ml_*         │
                    └───────────────────┬─────────────────────────────┘
                                        │ lê Iceberg (zero cópia)
                    ┌───────────────────▼─────────────────────────────┐
                    │           GOLD  (dbt marts)                      │
                    │  fact_sensor_readings · fact_maintenance          │
                    │  dim_asset · dim_date                             │
                    │  mart_availability · mart_mtbf_mttr               │
                    │  mart_alerts · mart_energy · feat_ml_*            │
                    └───────────────────┬─────────────────────────────┘
                                        │ dbt models
                    ┌───────────────────▼─────────────────────────────┐
                    │         SILVER  (dbt staging + intermediate)      │
                    │  stg_sensor_readings · stg_assets · stg_status   │
                    │  stg_maintenance · int_asset_metrics              │
                    └───────────────────┬─────────────────────────────┘
                                        │ Great Expectations
                    ┌───────────────────▼─────────────────────────────┐
                    │           BRONZE  (schema validado)              │
                    └───────────────────┬─────────────────────────────┘
                                        │ Dagster assets
                    ┌───────────────────▼─────────────────────────────┐
                    │         LANDING  (raw imutável)  — MinIO/Iceberg  │
                    └───────────────────┬─────────────────────────────┘
                            ┌───────────┴───────────┐
               ┌────────────▼──────┐     ┌──────────▼──────────────┐
               │  Redpanda (stream) │     │  Postgres  (batch seed)  │
               └────────────┬──────┘     └──────────┬──────────────┘
                            │                        │
               ┌────────────▼──────────────────────▼──────────────┐
               │           Simulador Python (IoT)                   │
               │  12 ativos · 2 leituras/min · 7 padrões de eventos │
               └────────────────────────────────────────────────────┘
```

---

## 🗂️ Estrutura do Repositório

```
iot-data-platform/
├── .github/workflows/          # CI/CD — GitHub Actions
│   └── ci.yml                  # lint, dbt compile, dbt test
├── docs/                       # Documentação técnica
│   ├── discovery_scope.md      # Discovery e escopo aprovado
│   ├── architecture.md         # Decisões de arquitetura (ADRs)
│   └── cloud_migration.md      # Guia AWS/GCP/Azure
├── infra/
│   ├── docker/                 # docker-compose e Dockerfiles
│   │   └── docker-compose.yml  # Stack completa em 1 comando
│   └── terraform/              # IaC cloud-ready
├── simulator/                  # Simulador IoT Python
│   ├── historical_backfill.py  # Gera 12 meses de CSVs (seed data)
│   ├── live_streaming.py       # Publica em Redpanda a cada 30s
│   └── models.py               # Modelos de ativos e eventos
├── postgres/
│   ├── init/                   # DDL — schema 3NF
│   └── seeds/                  # CSVs gerados pelo simulador
├── dbt_project/                # Transformações dbt (Silver → Gold)
│   ├── models/
│   │   ├── staging/            # stg_* — limpeza por tabela
│   │   ├── intermediate/       # int_* — joins e métricas
│   │   └── marts/              # fact_*, dim_*, mart_*, feat_ml_*
│   ├── tests/                  # Testes customizados
│   ├── macros/                 # Macros reutilizáveis
│   └── dbt_project.yml
├── dagster/                    # Orquestração do pipeline
│   ├── assets/                 # Assets por camada (Landing→Gold)
│   ├── jobs/                   # Jobs agendados
│   └── resources/              # Conexões (MinIO, Iceberg, Postgres)
├── monitoring/
│   ├── prometheus/             # prometheus.yml
│   ├── grafana/dashboards/     # JSONs dos dashboards
│   └── loki/                   # Configuração de logs
├── notebooks/                  # Jupyter — exploração DS
├── scripts/                    # Utilitários (setup, reset, etc.)
├── Makefile                    # Comandos principais
└── README.md
```

---

## 🚀 Início Rápido

### Pré-requisitos
- Docker + Docker Compose v2
- Python 3.12+
- Make

### Setup completo em 3 comandos

```bash
# 1. Clone e configure o ambiente
git clone https://github.com/Wilsonfranquilino/iot-data-platform.git
cd iot-data-platform
cp .env.example .env

# 2. Suba a stack e popule o banco com 12 meses de histórico
make up
make seed-data

# 3. Execute o pipeline dbt (Silver → Gold)
make dbt-run
```

### Modo Live Streaming (demo ao vivo)

```bash
make simulate   # Loop infinito: sensor → Redpanda → Dagster → Gold → Metabase
```

### Comandos disponíveis

```bash
make up           # Sobe toda a stack Docker
make down         # Derruba a stack
make seed-data    # Gera 12 meses de histórico e carrega no Postgres
make simulate     # Inicia streaming ao vivo via Redpanda
make dbt-run      # Executa todos os modelos dbt
make dbt-test     # Executa todos os testes dbt
make dbt-docs     # Abre documentação e lineage no browser
make reset        # Derruba, limpa volumes e reinicia do zero
make lint         # ruff + sqlfluff
```

---

## 📊 Equipamentos Monitorados

| ID | Tipo | Qtd | Linha | Sensores |
|---|---|---|---|---|
| CMP-001..004 | Compressor | 4 | A (2) e B (2) | temp, pressão, vibração, kWh, status |
| MTR-001..004 | Motor elétrico | 4 | A (2) e B (2) | temp, RPM, corrente, vibração, status |
| BMB-001..004 | Bomba hidráulica | 4 | A (2) e B (2) | temp, pressão, fluxo, kWh, status |

---

## 🔔 Alertas em Tempo Real

| Alerta | Severidade | Regra |
|---|---|---|
| Temperatura crítica | 🔴 CRITICAL | `temperature_c > 100°C` por 2 leituras consecutivas |
| Temperatura alta | 🟡 WARNING | `temperature_c > 90°C` por 3 leituras consecutivas |
| Vibração crítica | 🔴 CRITICAL | `vibration_mms > 10 mm/s` |
| Vibração alta | 🟡 WARNING | `vibration_mms > 7 mm/s` |
| Parada não agendada | 🔴 CRITICAL | `status = FAULT` sem MAINT nas últimas 4h |
| Consumo anômalo | 🟡 WARNING | `energy_kwh > 2× média 7 dias` |
| Sensor offline | 🟡 WARNING | Ausência de leituras por > 5 minutos |

---

## 📈 KPIs da Gestão

| KPI | Cálculo |
|---|---|
| **Disponibilidade (%)** | `(tempo RUNNING / tempo total) × 100` — por equipamento/linha/período |
| **MTBF (horas)** | `tempo total operando ÷ número de falhas` |
| **MTTR (horas)** | `tempo total em MAINT ou FAULT ÷ número de ocorrências` |
| **OEE simplificado** | `Disponibilidade × (RPM_atual / RPM_nominal)` |

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Equivalente Cloud |
|---|---|---|
| Simulação IoT | Python 3.12 | AWS IoT Core |
| Streaming | Redpanda | MSK / Pub/Sub |
| Storage + Formato | MinIO + Apache Iceberg | S3 + Iceberg |
| Catálogo Iceberg | Lakekeeper (REST Catalog) | AWS Glue Catalog |
| Transformação | dbt-core + DuckDB | dbt Cloud + BigQuery |
| Orquestração | Dagster OSS | Dagster Cloud |
| Qualidade | Great Expectations | idem (cloud-native) |
| BI | Metabase OSS | Looker / QuickSight |
| Consumo analistas | DuckDB isolado | BigQuery sandbox |
| Consumo DS | Jupyter + PyIceberg + Polars | idem |
| Observabilidade | Prometheus + Grafana + Loki | Datadog |
| IaC | Terraform | idem |

---

## 👥 Perfis de Acesso

| Perfil | Interface | Dados visíveis |
|---|---|---|
| Gerente | Metabase dashboards | Gold (KPIs prontos) |
| Técnico | Metabase + alertas | Gold (alertas em tempo real) |
| Analista de Processo | DuckDB isolado | Gold (marts SQL) |
| Cientista de Dados | Jupyter + PyIceberg | Silver + feat_ml_* Gold |
| Analytics Engineer | Tudo | Acesso completo |

---

## 📁 Documentação

- [Discovery e Escopo](docs/discovery_scope.md)
- [Decisões de Arquitetura](docs/architecture.md)
- [Guia de Migração Cloud](docs/cloud_migration.md)
- [dbt Docs](make dbt-docs)

---

## 📜 Licença

MIT — veja [LICENSE](LICENSE)

---

*Portfólio público de Analytics Engineering — Wilson Franquilino*  
*github.com/Wilsonfranquilino/iot-data-platform*
