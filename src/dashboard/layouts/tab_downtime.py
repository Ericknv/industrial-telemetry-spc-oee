"""
Layout da Aba de Downtime & Confiabilidade Industrial (TPM):
Estrutura horizontal em alto contraste exibindo métricas de MTBF, MTTR,
Disponibilidade Técnica, Pareto por Setor Fabril e classificação de paradas.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


def render_tab_downtime() -> html.Div:
    return html.Div(
        [
            # Barra Superior: Filtro de Turno e Ações de Exportação
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "SELEÇÃO DE TURNO OPERACIONAL",
                                className="kpi-title mb-2 d-block",
                            ),
                            html.Div(
                                dcc.Dropdown(
                                    id="downtime-shift-filter",
                                    options=[
                                        {"label": "Consolidado Geral (24h)", "value": "ALL"},
                                        {"label": "Turno 1 (06:00 - 14:00)", "value": "Turno 1 (Manhã)"},
                                        {"label": "Turno 2 (14:00 - 22:00)", "value": "Turno 2 (Tarde)"},
                                        {"label": "Turno 3 (22:00 - 06:00)", "value": "Turno 3 (Noite)"},
                                    ],
                                    value="ALL",
                                    clearable=False,
                                    style={
                                        "backgroundColor": "#1e293b",
                                        "color": "#38bdf8",
                                    },
                                ),
                                style={"backgroundColor": "#1e293b", "borderRadius": "6px"},
                            ),
                        ],
                        width=12,
                        md=4,
                        className="mb-4",
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                "EXPORTAÇÃO DE AUDITORIA DE PARADAS",
                                className="kpi-title mb-2 d-block",
                            ),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        "Exportar CSV de Paradas",
                                        id="btn-export-downtime-csv",
                                        color="secondary",
                                        outline=True,
                                        className="fw-bold px-3",
                                    ),
                                    dbc.Button(
                                        "Exportar Excel (.xlsx)",
                                        id="btn-export-downtime-excel",
                                        color="success",
                                        outline=True,
                                        className="fw-bold px-3 ms-2",
                                    ),
                                ]
                            ),
                            dcc.Download(id="download-downtime-report"),
                        ],
                        width=12,
                        md=8,
                        className="mb-4 d-flex flex-column align-items-md-end justify-content-end",
                    ),
                ]
            ),
            # Cartões de Métricas de Confiabilidade e TPM
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("MTBF (TEMPO MÉDIO ENTRE FALHAS)", className="kpi-title"),
                                html.Div(id="kpi-mtbf", className="kpi-value", style={"color": "#10b981"}),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("MTTR (TEMPO MÉDIO DE REPARO)", className="kpi-title"),
                                html.Div(id="kpi-mttr", className="kpi-value", style={"color": "#f59e0b"}),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("DISPONIBILIDADE TÉCNICA", className="kpi-title"),
                                html.Div(id="kpi-tech-avail", className="kpi-value", style={"color": "#38bdf8"}),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("FALHAS CRÍTICAS (NÃO-PLANEJADAS)", className="kpi-title"),
                                html.Div(id="kpi-failures-count", className="kpi-value", style={"color": "#ef4444"}),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                ]
            ),
            # Gráficos Analíticos em 2 Colunas
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            dcc.Graph(id="chart-pareto-sector", config={"displayModeBar": False}),
                            className="kpi-card p-2 mb-4",
                        ),
                        width=12,
                        lg=8,
                    ),
                    dbc.Col(
                        html.Div(
                            dcc.Graph(id="chart-donut-stop-type", config={"displayModeBar": False}),
                            className="kpi-card p-2 mb-4",
                        ),
                        width=12,
                        lg=4,
                    ),
                ]
            ),
            # Log Cronológico Tabular das Ocorrências
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.Span(
                                    "REGISTRO CRONOLÓGICO DE OCORRÊNCIAS DE PARADA",
                                    className="kpi-title mb-3 d-block",
                                ),
                                html.Div(id="table-downtime-events-container"),
                            ],
                            className="kpi-card p-3 mb-4",
                        ),
                        width=12,
                    )
                ]
            ),
        ]
    )