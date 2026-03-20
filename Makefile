.PHONY: up down seed-data simulate dbt-run dbt-test dbt-docs reset lint help

# ─── Variáveis ───────────────────────────────────────────────────────────────
COMPOSE = docker compose -f infra/docker/docker-compose.yml
DBT     = docker exec -it dbt dbt
PY      = python3

# ─── Stack ───────────────────────────────────────────────────────────────────
up: ## Sobe toda a stack Docker
	$(COMPOSE) up -d
	@echo "✅ Stack no ar. Acesse:"
	@echo "   Dagster   → http://localhost:3000"
	@echo "   Metabase  → http://localhost:3001"
	@echo "   MinIO     → http://localhost:9001  (minioadmin / minioadmin)"
	@echo "   Grafana   → http://localhost:3002  (admin / admin)"
	@echo "   Redpanda  → http://localhost:8080"

down: ## Derruba a stack
	$(COMPOSE) down

reset: ## Derruba, limpa volumes e reinicia do zero
	$(COMPOSE) down -v --remove-orphans
	@echo "🗑️  Volumes apagados."
	$(COMPOSE) up -d
	@echo "✅ Stack reiniciada limpa."

# ─── Dados ───────────────────────────────────────────────────────────────────
seed-data: ## Gera 12 meses de histórico e carrega no Postgres
	@echo "⏳ Gerando seed data (12 meses, 12 ativos)..."
	$(PY) simulator/historical_backfill.py
	@echo "📦 Carregando CSVs no Postgres via dbt seed..."
	$(DBT) seed --project-dir dbt_project
	@echo "✅ Banco operacional populado."

simulate: ## Inicia streaming ao vivo via Redpanda (Ctrl+C para parar)
	@echo "🔴 Iniciando simulação ao vivo — sensor → Redpanda → Dagster → Gold"
	@echo "   Ctrl+C para parar."
	$(PY) simulator/live_streaming.py

# ─── dbt ─────────────────────────────────────────────────────────────────────
dbt-run: ## Executa todos os modelos dbt (staging → intermediate → marts)
	$(DBT) run --project-dir dbt_project

dbt-test: ## Executa todos os testes dbt
	$(DBT) test --project-dir dbt_project

dbt-docs: ## Gera e abre documentação + lineage no browser
	$(DBT) docs generate --project-dir dbt_project
	$(DBT) docs serve --project-dir dbt_project --port 8081
	@echo "📖 Docs em http://localhost:8081"

dbt-staging: ## Roda apenas modelos staging
	$(DBT) run --project-dir dbt_project --select staging

dbt-marts: ## Roda apenas modelos marts (Gold)
	$(DBT) run --project-dir dbt_project --select marts

# ─── Qualidade ───────────────────────────────────────────────────────────────
lint: ## ruff (Python) + sqlfluff (SQL)
	ruff check simulator/ dagster/
	sqlfluff lint dbt_project/models/ --dialect duckdb

format: ## Formata código Python e SQL
	ruff format simulator/ dagster/
	sqlfluff fix dbt_project/models/ --dialect duckdb

# ─── Utilitários ─────────────────────────────────────────────────────────────
logs: ## Exibe logs da stack em tempo real
	$(COMPOSE) logs -f

ps: ## Status dos containers
	$(COMPOSE) ps

help: ## Lista todos os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
