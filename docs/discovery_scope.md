# Discovery e Escopo — Industrial Asset Monitor

> Documento de referência gerado a partir da reunião de kickoff em 18/03/2026.  
> Status: **Aprovado — prontos para iniciar.**

## Problema Central

Manutenção 100% corretiva gera parada de linha e perda de produto em processo.  
A plataforma entrega manutenção preditiva baseada em dados de sensores em tempo real.

## Escopo Aprovado

- **12 equipamentos** em 2 linhas: 4 compressores, 4 motores, 4 bombas
- **1 leitura a cada 30 segundos** por ativo (2 leituras/min)
- **12 meses de histórico simulado** para seed data e modelagem
- **Alertas em tempo real**: temperatura, vibração, consumo, parada não agendada
- **KPIs**: Disponibilidade, MTBF, MTTR, OEE simplificado

## Fora do Escopo

- Treinamento e deployment de modelos ML (apenas feature store)
- Integração com sensores físicos reais
- Autenticação SSO no Metabase
- Deploy em cloud (apenas documentação de migração + Terraform plan)
- CMMS, relatórios financeiros

## Sequência de Entregas

| # | Etapa | Status |
|---|---|---|
| 1 | Repositório GitHub | ✅ Concluído |
| 2 | Geração de seed data | 🔜 |
| 3 | Postgres + dbt seed | 🔜 |
| 4 | Modelagem dimensional | 🔜 |
| 5 | dbt models | 🔜 |
| 6 | dbt tests + docs | 🔜 |
| 7 | Stack completa (Docker) | 🔜 |
| 8 | Pipeline streaming | 🔜 |
| 9 | Consumo e BI | 🔜 |
| 10 | Observabilidade | 🔜 |
| 11 | Segurança e Terraform | 🔜 |
| 12 | Entrega LinkedIn | 🔜 |
