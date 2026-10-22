# 🏭 Industrial Telemetry & Manufacturing Analytics Suite (MES)

Plataforma de alta performance para monitoramento de chão de fábrica em tempo real, integrando telemetria operacional, cálculo de **OEE**, engenharia de confiabilidade (**TPM / Downtime**) e **Controle Estatístico de Processo (CEP / SPC)**.

Construído sob uma arquitetura analítica moderna (OLAP em memória) combinando **DuckDB**, **Polars** e **Plotly Dash**, o sistema elimina gargalos de latência no processamento colunar de séries temporais industriais.

---

## 📐 Arquitetura da Solução

O pipeline adota uma separação estrita entre a camada de persistência colunar, o motor de regras de negócio industriais e a camada de interface reativa:

```text
┌─────────────────────────────────────────────────────────────┐
│                   DISPOSITIVOS DE CHÃO DE FÁBRICA           │
│             (Sensores Fotoelétricos, CNCs, AGVs e CLP)      │
└──────────────────────────────┬──────────────────────────────┘
                               │ Ingestão Batch / Streaming
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 CAMADA DE DADOS: DuckDB                     │
│    • operational_events (Séries temporais, turnos, paradas) │
│    • dimensional_inspections (Subgrupos racionais para CEP) │
└──────────────────────────────┬──────────────────────────────┘
                               │ Consultas Vetorizadas (OLAP)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 PROCESSAMENTO: Polars Engines               │
│    • OEEEngine: Decomposição A-P-Q & Simulador What-If      │
│    • DowntimeEngine: Confiabilidade TPM (MTBF, MTTR)        │
│    • SPCEngine: Cartas X̄-R, Regras de Nelson & Índices Cp/Cpk│
└──────────────────────────────┬──────────────────────────────┘
                               │ DataFrames em Memória
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             INTERFACE & ANALYTICS: Plotly Dash              │
│    • Design System Slate Panorâmico (Alto Contraste)         │
│    • Gantt Swimlanes, Waterfall, Paretos & Histogramas      │
│    • Exportação de Relatórios de Auditoria (CSV / XLSX)     │
└─────────────────────────────────────────────────────────────┘
