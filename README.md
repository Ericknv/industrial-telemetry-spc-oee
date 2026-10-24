```markdown
# 🏭 Industrial Telemetry & Manufacturing Analytics Suite (MES)

Plataforma analítica industrial de alta performance projetada para monitoramento operacional em tempo real de linhas de produção contínuas. A solução unifica o rastreamento em nível de telemetria de **OEE (Overall Equipment Effectiveness)**, engenharia de confiabilidade e gestão de perdas operacionais (**Downtime / TPM**) e **Controle Estatístico de Processo (CEP / SPC)** em conformidade com as normas industriais (ISO 22514 / IATF 16949).

Desenvolvida sob o paradigma de processamento analítico colunar em memória (OLAP com **DuckDB** e **Polars**), a arquitetura elimina a latência de consultas relacionais tradicionais, garantindo renderização instantânea de séries temporais de alta frequência via **Plotly Dash** sob um design system de alto contraste orientado a chão de fábrica.

---

## 📑 Sumário Executivo

1. [Visão Geral e Objetivos de Engenharia](#-visão-geral-e-objetivos-de-engenharia)
2. [Arquitetura da Solução e Fluxo de Dados](#-arquitetura-da-solução-e-fluxo-de-dados)
3. [Stack Tecnológica e Justificativas Técnicas](#-stack-tecnológica-e-justificativas-técnicas)
4. [Fundamentação Teórica e Modelagem Matemática](#-fundamentação-teórica-e-modelagem-matemática)
   - [Overall Equipment Effectiveness (OEE)](#1-overall-equipment-effectiveness-oee)
   - [Confiabilidade Operacional e TPM (MTBF, MTTR, Disponibilidade Técnica)](#2-confiabilidade-operacional-e-tpm)
   - [Controle Estatístico de Processo (CEP / SPC)](#3-controle-estatístico-de-processo-cep--spc)
   - [Regras de Nelson para Detecção de Causas Especiais](#4-regras-de-nelson-para-detecção-de-causas-especiais)
5. [Módulos da Plataforma](#-módulos-da-plataforma)
   - [Aba 1: Desempenho Operacional (OEE) e Simulador What-If](#aba-1-desempenho-operacional-oee-e-simulador-what-if)
   - [Aba 2: Confiabilidade & Gestão de Downtime (TPM)](#aba-2-confiabilidade--gestão-de-downtime-tpm)
   - [Aba 3: Engenharia da Qualidade & Cartas de Controle (CEP)](#aba-3-engenharia-da-qualidade--cartas-de-controle-cep)
6. [Mecanismo de Exportação para Auditoria](#-mecanismo-de-exportação-para-auditoria)
7. [Design System Industrial (Slate High-Contrast)](#-design-system-industrial-slate-high-contrast)
8. [Estrutura de Diretórios do Projeto](#-estrutura-de-diretórios-do-projeto)
9. [Instalação e Execução Passo a Passo](#-instalação-e-execução-passo-a-passo)
10. [Governança, Versionamento e Ciclo de Releases](#-governança-versionamento-e-ciclo-de-releases)

---

## 🎯 Visão Geral e Objetivos de Engenharia

Em ambientes de manufatura avançada, decisões operacionais requerem a convergência de dados de automação (CLPs e sensores) com ferramentas estatísticas aplicadas. Os principais desafios resolvidos por esta plataforma incluem:

* **Eliminação de Silos de Informação:** Centralização de apontamentos de parada, telemetria de peças produzidas e controle dimensional em um único repositório analítico local.
* **Diagnóstico de Causa-Raiz (Root Cause Analysis):** Estratificação imediata de gargalos por departamento fabril (Manutenção Mecânica, Elétrica/Automação, Engenharia de Processos, Logística e Qualidade).
* **Engenharia Preditiva e What-If:** Avaliação em tempo real do retorno produtivo resultante da implementação de projetos de melhoria contínua (Kaizen, SMED e Poka-Yoke).
* **Vigilância de Estabilidade do Processo:** Monitoramento em linha de variáveis críticas de controle (CTQs) com detecção prematura de desvios de processo antes da ocorrência de não conformidades dimensionais.

---

## 🏛 Arquitetura da Solução e Fluxo de Dados

A arquitetura adota o isolamento rigoroso entre **camada de persistência colunar**, **camada analítica/regras de negócio** e **camada de apresentação reativa**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   DISPOSITIVOS DE CHÃO DE FÁBRICA                      │
│        (Sensores Fotoelétricos, CNCs, Robôs Industriais, AGVs)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Ingestão Estocástica / Telemetria
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   CAMADA DE PERSISTÊNCIA: DuckDB                       │
│    • operational_events: Séries temporais de turnos, tempos e paradas  │
│    • dimensional_inspections: Amostragens dimensionais para CEP        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Consultas Vetorizadas (OLAP In-Memory)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             MOTORES DE PROCESSAMENTO VETORIZADO: Polars                │
│    • OEEEngine: Decomposição A-P-Q, Cascata de Tempo e What-If         │
│    • DowntimeEngine: Cálculo de MTBF, MTTR, Disponibilidade Técnica    │
│    • SPCEngine: Subgrupos racionais, Limites de Controle, Cp/Cpk       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ DataFrames Apache Arrow em Memória
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               CAMADA DE APRESENTAÇÃO: Plotly Dash                      │
│    • Layout Panorâmico Horizontal (12 Colunas) em Slate Dark Theme     │
│    • Gráficos: Swimlanes Gantt, Waterfall, Paretos, Histograma Gauss   │
│    • Download Engine: Despacho em memória de CSV e planilhas .xlsx     │
└────────────────────────────────────────────────────────────────────────┘

```

---

## 🛠 Stack Tecnológica e Justificativas Técnicas

* **Python 3.10+:** Linguagem-base para rápida modelagem estatística e ecossistema analítico.
* **DuckDB (Embedded Analytical OLAP):**
* *Por que não SQLite ou PostgreSQL?* O DuckDB opera sob formato colunar vetorizado (SIMD), permitindo agregações de milhões de registros operacionais com tempo de execução em milissegundos, dispensando a complexidade de configuração e manutenção de serviços externos de banco de dados.


* **Polars (DataFrames de Alta Performance):**
* *Por que não Pandas tradicional?* O Polars é construído em Rust sobre a especificação Apache Arrow. Ele executa operações paralelas nativas (*multithread*), utiliza zero-copy para manipulação de memória e apresenta consumo de CPU e RAM expressivamente inferior no processamento de séries temporais.


* **Plotly Dash & Dash Bootstrap Components:**
* Framework reativo puro em Python para construção de aplicações analíticas corporativas sem necessidade de desenvolvimento front-end isolado em JavaScript/React.


* **openpyxl / xlsxwriter:**
* Motores para construção e formatação condicional de planilhas Excel em memória direta via streams de bytes (`io.BytesIO`).



---

## 🧮 Fundamentação Teórica e Modelagem Matemática

### 1. Overall Equipment Effectiveness (OEE)

O OEE mede a eficiência real de um equipamento ou linha durante o tempo em que esteve planejado para produzir, em estrita conformidade com as normas SEMI E10 e a metodologia JIPM (*Japan Institute of Plant Maintenance*):

$$\text{OEE} = A \times P \times Q$$

#### A. Fator Disponibilidade ($A$)

Reflete as perdas decorrentes de paradas não programadas e tempos de preparação de linha:

$$A = \frac{\text{Tempo Operacional (Operating Time)}}{\text{Tempo Planejado de Carga (Planned Production Time)}}$$

$$\text{Onde: } \text{Tempo Operacional} = \text{Tempo Planejado} - \sum \text{Downtime (Setups + Quebras + Falhas)}$$

#### B. Fator Performance / Desempenho ($P$)

Mede a eficiência do ciclo produtivo contra a velocidade de projeto da máquina, considerando o Tempo de Ciclo Teórico Ideal ($TC_0 = 4{,}0\text{ s}$):

$$P = \frac{\text{Total de Peças Produzidas} \times TC_0}{\text{Tempo Operacional}}$$

*Nota: Desvios de velocidade, microparadas imperceptíveis por sensores e lentidão operacional degradam este fator.*

#### C. Fator Qualidade ($Q$)

Quantifica a taxa de itens conforms produzidos logo na primeira passagem operacional:

$$Q = \frac{\text{Peças Boas}}{\text{Total de Peças Produzidas}} = \frac{\text{Total Produzido} - \text{Total Refugos}}{\text{Total Produzido}}$$

---

### 2. Confiabilidade Operacional e TPM

A gestão de paradas decompõe eventos operacionais em categorias estruturadas e calcula os indicadores centrais da Manutenção Produtiva Total:

#### A. Mean Time Between Failures (MTBF)

Representa a confiabilidade do sistema, medindo o tempo médio em que a esteira/estação permaneceu em regime estável de fabricação entre duas falhas corretivas:

$$\text{MTBF} = \frac{\text{Tempo Total de Produção Efetiva (RUN)}}{\text{Número Total de Falhas Não-Planejadas}}$$

#### B. Mean Time To Repair (MTTR)

Mede a mantenabilidade da linha e a eficiência da resposta da equipe técnica especializada na resolução de intervenções corretivas:

$$\text{MTTR} = \frac{\text{Tempo Total Gasto em Paradas Não-Planejadas}}{\text{Número Total de Falhas Não-Planejadas}}$$

#### C. Disponibilidade Técnica Operacional

Relação intrínseca entre os tempos médios de operação contínua e tempos médios de indisponibilidade por quebra:

$$A_{\text{técnica}} = \frac{\text{MTBF}}{\text{MTBF} + \text{MTTR}}$$

---

### 3. Controle Estatístico de Processo (CEP / SPC)

O módulo de qualidade monitora o diâmetro nominal crítico de um componente mecânico usinado ($\mu = 25{,}000\text{ mm}$, com limites de engenharia estabelecidos em $\text{LSL} = 24{,}850\text{ mm}$ e $\text{USL} = 25{,}150\text{ mm}$).

A amostragem utiliza o conceito de **Subgrupos Racionais** ($k$ amostras compostas por $n = 5$ peças consecutivas).

#### A. Carta de Controle de Médias ($\bar{X}$)

Monitora a tendência central e a estabilidade da média do processo:

$$\bar{X}_i = \frac{1}{n} \sum_{j=1}^{n} X_{ij}, \quad \bar{\bar{X}} = \frac{1}{k} \sum_{i=1}^{k} \bar{X}_i$$

Os limites de controle estatístico (3 sigmas) são deduzidos via constante tabelada $A_2$ (para $n=5$, $A_2 = 0{,}577$):

$$\text{UCL}_{\bar{X}} = \bar{\bar{X}} + A_2 \bar{R}$$

$$\text{CL}_{\bar{X}} = \bar{\bar{X}}$$

$$\text{LCL}_{\bar{X}} = \bar{\bar{X}} - A_2 \bar{R}$$

#### B. Carta de Controle de Amplitude ($R$)

Monitora a variabilidade inerente intra-subgrupo (dispersão imediata do equipamento):

$$R_i = \max(X_{ij}) - \min(X_{ij}), \quad \bar{R} = \frac{1}{k} \sum_{i=1}^{k} R_i$$

Limites de dispersão calculados com as constantes $D_3$ e $D_4$ (para $n=5$, $D_3 = 0{,}000$ e $D_4 = 2{,}114$):

$$\text{UCL}_R = D_4 \bar{R}$$

$$\text{CL}_R = \bar{R}$$

$$\text{LCL}_R = D_3 \bar{R} = 0$$

#### C. Índices de Capabilidade do Processo ($C_p$ e $C_{pk}$)

A dispersão do processo ($\hat{\sigma}$) é estimada de forma não-viesada a partir da amplitude média utilizando a constante estatística $d_2$ (para $n=5$, $d_2 = 2{,}326$):

$$\hat{\sigma} = \frac{\bar{R}}{d_2}$$

* **Índice de Capacidade Potencial ($C_p$):** Razão entre a largura de tolerância de projeto e a variação natural de 6 sigmas do processo:

$$C_p = \frac{\text{USL} - \text{LSL}}{6\hat{\sigma}}$$


* **Índice de Capabilidade Real ($C_{pk}$):** Considera a centralização da média em relação aos limites de especificação:

$$C_{pu} = \frac{\text{USL} - \bar{\bar{X}}}{3\hat{\sigma}}, \quad C_{pl} = \frac{\bar{\bar{X}} - \text{LSL}}{3\hat{\sigma}}$$


$$C_{pk} = \min(C_{pu}, C_{pl})$$



*Interpretação Industrial:* $C_{pk} \ge 1{,}33$ classifica o processo como plenamente capaz e estável para atendimento a requisitos de fornecimento automotivo e manufatura seriada.

---

### 4. Regras de Nelson para Detecção de Causas Especiais

O motor de regras avalia continuamente a média dos subgrupos para disparar alertas automáticos antes que o processo produza refugo em massa:

* **Regra 1 (Instabilidade Extrema):** Pelo menos 1 ponto além de 3 desvios-padrão dos limites calculados ($> \text{UCL}$ ou $< \text{LCL}$).
* **Regra 2 (Mudança de Nível de Processo):** 9 pontos consecutivos situados rigorosamente do mesmo lado da linha média central ($\bar{\bar{X}}$).
* **Regra 3 (Tendência Sistemática):** 6 pontos consecutivos estritamente crescentes ou estritamente decrescentes (indício de desgaste de ferramenta, aquecimento de mancais ou variação térmica).
* **Regra 4 (Variabilidade Excessiva por Alternância):** 14 pontos consecutivos alternando sistematicamente para cima e para baixo.

---

## 💻 Módulos da Plataforma

### Aba 1: Desempenho Operacional (OEE) e Simulador What-If

* **Filtro de Turno:** Segmentação imediata dos cálculos para visualização Consolidada Geral (24h), Turno 1 (Manhã), Turno 2 (Tarde) e Turno 3 (Noite).
* **Quatro Cards Principais:** OEE Global, Disponibilidade, Performance e Qualidade com destaque de alto contraste.
* **Gantt Operacional em Swimlanes:** Linha do tempo horizontal contínua de 24h disposta em raias dedicadas por evento (`PRODUÇÃO REGULAR (RUN)`, `SETUP_AJUSTE`, `FALHA_MECANICA`, `FALTA_MATERIAL`, `MICROPARADA_SENSOR`, `INSPECAO_QUALIDADE`).
* **Decomposição em Cascata (Waterfall):** Quantificação em minutos da perda de tempo por paradas de linha, perda de ritmo e refugos materiais.
* **Diagrama de Pareto de Causas:** Ordenação de motivos de interrupção operacional com curva de impacto acumulado percentual.
* **Simulador de Sensibilidade What-If:**
* Três sliders analíticos: Redução de Setup (SMED), Redução de Falhas (TPM) e Eliminação de Refugo (Poka-Yoke).
* Projeção instantânea de novo OEE percentual, minutos de linha recuperados e volume adicional de peças boas.



### Aba 2: Confiabilidade & Gestão de Downtime (TPM)

* **Cards de Confiabilidade:** Apresentação em destaque dos indicadores $MTBF$, $MTTR$, $A_{\text{técnica}}$ e contagem total de falhas não-planejadas.
* **Pareto por Setor Responsável:** Gráfico bicaudal ordenando horas de parada atribuídas a cada área industrial (`Manutenção Mecânica`, `Automação & Elétrica`, `Logística & Suprimentos`, `Engenharia de Processo`, `Garantia da Qualidade`).
* **Classificação de Paradas (Donut Chart):** Decomposição percentual direta entre eventos **Planejados** (preparações e auditorias) e **Não-Planejados** (quebras e faltas operacionais).
* **Tabela de Ocorrências Cronológicas:** Log tabular detalhado das paradas contendo horários de início/término, duração em minutos, setor acionado, submotivo e turno associado.

### Aba 3: Engenharia da Qualidade & Cartas de Controle (CEP)

* **Cards de Capacidade:** Apresentação dinâmica dos índices de capabilidade $C_p$, $C_{pk}$, Média Geral $\bar{\bar{X}}$ e Desvio Padrão Estimado $\hat{\sigma}$.
* **Banner Dinâmico de Alertas Nelson:** Caixa de notificação inteligente que relata a conformidade do processo ou discrimina subgrupos específicos envolvidos em violações estatísticas.
* **Histograma Dimensional Gaussiano:** Distribuição contínua de medições individuais sobreposta com curva normal ajustada e limites visuais verticais de especificação ($\text{LSL}$, $\text{Nominal}$, $\text{USL}$).
* **Cartas de Controle de Shewhart:** Gráficos sincronizados $\bar{X}$ e $R$ com limites $3\sigma$ e marcação em vermelho de pontos fora de controle.

---

## 📤 Mecanismo de Exportação para Auditoria

Cada módulo analítico possui botões para geração instantânea de dados tabulares em formatos universais:

* **Exportação CSV:** Utiliza o método nativo de serialização rápida do Polars (`write_csv`), entregando dados estruturados para integração com outros sistemas ou ferramentas analíticas.
* **Exportação Excel (.xlsx):**
* O processamento ocorre 100% em memória RAM por meio de buffers de bytes (`io.BytesIO`), sem geração de arquivos temporários no disco do servidor.
* Planilhas estruturadas com múltiplas abas estilizadas (ex.: `Resumo_OEE`, `Pareto_Paradas`, `Resumo_TPM`, `Historico_Paradas`, `Subgrupos_Limites_Regras`, `Medicoes_Individuais`).



---

## 🎨 Design System Industrial (Slate High-Contrast)

A interface utiliza uma folha de estilo customizada (`styles.css`) projetada para terminais de chão de fábrica e ambientes de sala de controle (CCO):

* **Fundo de Aplicação:** `#0f172a` (Slate 900 — redução de fadiga visual e consumo energético em displays industriais).
* **Superfície de Cartões:** `#1e293b` (Slate 800 — delimitação nítida de áreas de conteúdo com bordas em `#334155`).
* **Tipografia Técnica:** Hierarquia limpa baseada em fontes do sistema (-apple-system, Segoe UI, Roboto), garantindo legibilidade à distância.
* **Paleta Semântica Funcional:**
* **Ciano (`#38bdf8`):** Métricas operacionais, valores de telemetria e limites de amplitude.
* **Verde Esmeralda (`#10b981`):** Produção regular (RUN), processos sob controle e metas superadas.
* **Amarelo Âmbar (`#f59e0b`):** Setups de máquina, paradas planejadas e curvas acumuladas de Pareto.
* **Vermelho Carmim (`#ef4444`):** Falhas mecânicas, limites de controle $3\sigma$ e violações de regras estatísticas.


* **Tratamento de Controles:** Eliminação completa de inputs numéricos residuais em sliders (`rc-slider`) e blindagem de estilo escuro em seletores `dcc.Dropdown` contra herança indevida de transparência.

---

## 📁 Estrutura de Diretórios do Projeto

```text
industrial-telemetry-spc-oee/
├── .gitignore                      # Regras de exclusão de binários, caches e venv
├── requirements.txt                # Dependências versionadas do ecossistema Python
├── README.md                       # Documentação técnica e arquitetural da suite
├── data/
│   └── telemetry.duckdb            # Banco colunar persistido (gerado via simulação)
└── src/
    ├── __init__.py
    ├── config.py                   # Constantes e configurações globais
    ├── core/                       # Motores de cálculo analítico isolados
    │   ├── __init__.py
    │   ├── oee_engine.py           # Algoritmos de OEE, cascata e simulação What-If
    │   ├── downtime_engine.py      # Cálculos de confiabilidade TPM (MTBF, MTTR, setores)
    │   └── spc_engine.py           # Estatística de subgrupos, constantes e Regras de Nelson
    ├── dashboard/                  # Camada visual e orquestração de callbacks Dash
    │   ├── __init__.py
    │   ├── app.py                  # Ponto de entrada da aplicação e barramento de eventos
    │   ├── assets/
    │   │   └── styles.css          # Folha de estilo do Design System Slate Industrial
    │   ├── components/
    │   │   ├── __init__.py
    │   │   └── charts.py           # Fábrica de figuras estatísticas e operacionais (Plotly)
    │   └── layouts/
    │       ├── __init__.py
    │       ├── tab_oee.py          # Estrutura visual da aba de Eficiência (OEE)
    │       ├── tab_downtime.py     # Estrutura visual da aba de Confiabilidade (TPM)
    │       └── tab_spc.py          # Estrutura visual da aba de Qualidade e CEP
    └── ingestion/                  # Modelagem de dados e geração de telemetria
        ├── __init__.py
        ├── pipeline.py             # Interfaces de consumo e sincronização de dados
        └── simulator.py            # Gerador estocástico da telemetria de 24 horas fabris

```

---

## 🚀 Instalação e Execução Passo a Passo

### Pré-requisitos

* Sistema Operacional: Windows 10/11, Linux (Ubuntu/Debian) ou macOS
* Python 3.10 ou superior
* Gerenciador de dependências `pip` e Git instalados

### 1. Clonar o Repositório

```bash
git clone [https://github.com/SEU_USUARIO/industrial-telemetry-spc-oee.git](https://github.com/SEU_USUARIO/industrial-telemetry-spc-oee.git)
cd industrial-telemetry-spc-oee

```

### 2. Configurar o Ambiente Virtual

No Windows (Prompt de Comando / CMD):

```cmd
python -m venv venv
venv\Scripts\activate

```

No Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate

```

### 3. Instalar Dependências do Sistema

```bash
pip install --upgrade pip
pip install -r requirements.txt

```

### 4. Inicializar o Banco de Dados Industrial (DuckDB)

Execute o simulador para criar as tabelas `operational_events` e `dimensional_inspections` e povoar 24 horas ininterruptas de operação fabril:

```bash
python -m src.ingestion.simulator

```

*Saída esperada:* `Base industrial gerada com sucesso e enriquecida com atributos de Downtime/TPM.`

### 5. Iniciar o Servidor do Dashboard

```bash
python -m src.dashboard.app

```

Abra o navegador e acesse:

```text
[http://127.0.0.1:8050](http://127.0.0.1:8050)

```

---

## 🌿 Governança, Versionamento e Ciclo de Releases

O projeto adota o padrão de desenvolvimento e versionamento baseado em ramificações do Git:

* `main`: Ramo estável com código validado para produção.
* `feature/design-system-3.0`: Ramo de trabalho ativo onde foram consolidados os novos módulos de Downtime/TPM, o Design System Slate e as exportações em memória.

### Histórico de Releases:

* **v1.0 (MVP Baseline):** Ingestão DuckDB, cálculos analíticos de OEE básico e cartas de controle Shewhart simples.
* **v2.0 (Analytics Evolution):** Implementação do gráfico de Gantt em Swimlanes, Simulador What-If de sensibilidade operacional, Histograma Gaussiano de capacidade e exportação tabular.
* **v3.0 (Enterprise Suite):** Reestruturação panorâmica horizontal, introdução do módulo de Confiabilidade & TPM ($MTBF$, $MTTR$, Pareto setorial multidepartamental), supressão de artefatos visuais e refatoração completa com testes arquivo por arquivo via metodologia pente-fino.

---

## 📄 Licença e Uso

Este projeto está estruturado para fins acadêmicos, de portfólio de engenharia e demonstração de sistemas avançados de manufatura (MES/Analytics). Os modelos de dados e cálculos matemáticos podem ser livremente estendidos para conexões com gateways OPC UA, barramentos MQTT ou bancos corporativos (TimescaleDB, Snowflake, BigQuery).

```

```