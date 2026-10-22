"""
Layout da Aba de OEE:
Visual refinado em alto contraste, cards industriais, linha do tempo Gantt,
gráficos de perdas, simulador interativo What-If e botões de exportação de dados.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

STYLE_MARK_DIM = {"color": "#94a3b8", "fontSize": "0.85rem", "fontWeight": "500"}
SLIDER_MARKS = {
    0: {"label": "0%", "style": STYLE_MARK_DIM},
    25: {"label": "-25%", "style": STYLE_MARK_DIM},
    50: {"label": "-50%", "style": STYLE_MARK_DIM},
    75: {"label": "-75%", "style": STYLE_MARK_DIM},
    100: {"label": "-100%", "style": STYLE_MARK_DIM},
}

DROPDOWN_STYLE = {
    "backgroundColor": "#1e293b",
    "color": "#0f172a",
    "border": "1px solid #475569",
    "borderRadius": "6px",
}


def render_tab_oee() -> html.Div:
    return html.Div(
        [
            # Seletor de turno operacional e Botões de Exportação
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "SELEÇÃO DE TURNO OPERACIONAL",
                                className="kpi-title mb-2 d-block",
                                style={"color": "#94a3b8", "fontWeight": "600"},
                            ),
                            html.Div(
                                dcc.Dropdown(
                                    id="oee-shift-filter",
                                    options=[
                                        {"label": "Consolidado Geral (24h)", "value": "ALL"},
                                        {"label": "Turno 1 (06:00 - 14:00)", "value": "Turno 1 (Manhã)"},
                                        {"label": "Turno 2 (14:00 - 22:00)", "value": "Turno 2 (Tarde)"},
                                        {"label": "Turno 3 (22:00 - 06:00)", "value": "Turno 3 (Noite)"},
                                    ],
                                    value="ALL",
                                    clearable=False,
                                    style=DROPDOWN_STYLE,
                                ),
                                style={"color": "#0f172a"},
                            ),
                        ],
                        width=12,
                        md=5,
                        className="mb-4",
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                "EXPORTAÇÃO DE RELATÓRIO OPERACIONAL",
                                className="kpi-title mb-2 d-block",
                                style={"color": "#94a3b8", "fontWeight": "600"},
                            ),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        "Exportar CSV",
                                        id="btn-export-oee-csv",
                                        color="secondary",
                                        className="fw-bold px-3",
                                        outline=True,
                                    ),
                                    dbc.Button(
                                        "Exportar Excel (.xlsx)",
                                        id="btn-export-oee-excel",
                                        color="success",
                                        className="fw-bold px-3 ms-2",
                                        outline=True,
                                    ),
                                ]
                            ),
                            # Componente invisível de Download
                            dcc.Download(id="download-oee-report"),
                        ],
                        width=12,
                        md=7,
                        className="mb-4 d-flex flex-column align-items-md-end justify-content-end",
                    ),
                ]
            ),
            # Cartões de KPI Reais
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("OEE GLOBAL REAL", className="kpi-title"),
                                html.Div(id="kpi-oee", className="kpi-value", style={"color": "#38bdf8"}),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("DISPONIBILIDADE (A)", className="kpi-title"),
                                html.Div(id="kpi-availability", className="kpi-value", style={"color": "#f8fafc"}),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("PERFORMANCE (P)", className="kpi-title"),
                                html.Div(id="kpi-performance", className="kpi-value", style={"color": "#f8fafc"}),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("QUALIDADE (Q)", className="kpi-title"),
                                html.Div(id="kpi-quality", className="kpi-value", style={"color": "#f8fafc"}),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                ]
            ),
            # Linha do Tempo Operacional (Gantt)
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            dcc.Graph(id="chart-oee-timeline", config={"displayModeBar": False}),
                            className="kpi-card p-2 mb-4",
                        ),
                        width=12,
                    )
                ]
            ),
            # Gráficos em contêineres Slate (Cascata e Pareto)
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            dcc.Graph(id="chart-oee-waterfall", config={"displayModeBar": False}),
                            className="kpi-card p-2 mb-4",
                        ),
                        width=12,
                        lg=6,
                    ),
                    dbc.Col(
                        html.Div(
                            dcc.Graph(id="chart-pareto", config={"displayModeBar": False}),
                            className="kpi-card p-2 mb-4",
                        ),
                        width=12,
                        lg=6,
                    ),
                ]
            ),
            # SEÇÃO: Simulador What-If de Engenharia
            html.Div(
                [
                    html.H4(
                        "Simulador de Sensibilidade e Melhoria Contínua (What-If)",
                        style={"color": "#f8fafc", "fontWeight": "700", "marginTop": "15px", "marginBottom": "5px"},
                    ),
                    html.P(
                        "Projete ganhos de produção e OEE simulando a eliminação de causas-raiz em Kaizen e SMED.",
                        style={"color": "#94a3b8", "marginBottom": "25px", "fontSize": "0.95rem"},
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Span(
                                                    "REDUÇÃO DE SETUP (SMED):",
                                                    className="kpi-title",
                                                    style={"color": "#cbd5e1"},
                                                ),
                                                html.Span(
                                                    id="badge-setup-value",
                                                    className="badge bg-primary ms-2 px-2 py-1",
                                                    style={"fontSize": "0.9rem", "fontWeight": "bold"},
                                                ),
                                            ],
                                            className="d-flex align-items-center mb-2",
                                        ),
                                        dcc.Slider(
                                            id="slider-setup-reduction",
                                            min=0,
                                            max=100,
                                            step=5,
                                            value=20,
                                            marks=SLIDER_MARKS,
                                            updatemode="drag",
                                        ),
                                        html.Br(),
                                        html.Div(
                                            [
                                                html.Span(
                                                    "REDUÇÃO DE FALHAS MECÂNICAS (TPM):",
                                                    className="kpi-title",
                                                    style={"color": "#cbd5e1"},
                                                ),
                                                html.Span(
                                                    id="badge-breakdown-value",
                                                    className="badge bg-danger ms-2 px-2 py-1",
                                                    style={"fontSize": "0.9rem", "fontWeight": "bold"},
                                                ),
                                            ],
                                            className="d-flex align-items-center mb-2",
                                        ),
                                        dcc.Slider(
                                            id="slider-breakdown-reduction",
                                            min=0,
                                            max=100,
                                            step=5,
                                            value=30,
                                            marks=SLIDER_MARKS,
                                            updatemode="drag",
                                        ),
                                        html.Br(),
                                        html.Div(
                                            [
                                                html.Span(
                                                    "REDUÇÃO DE REFUGOS (POKA-YOKE):",
                                                    className="kpi-title",
                                                    style={"color": "#cbd5e1"},
                                                ),
                                                html.Span(
                                                    id="badge-scrap-value",
                                                    className="badge bg-warning text-dark ms-2 px-2 py-1",
                                                    style={"fontSize": "0.9rem", "fontWeight": "bold"},
                                                ),
                                            ],
                                            className="d-flex align-items-center mb-2",
                                        ),
                                        dcc.Slider(
                                            id="slider-scrap-reduction",
                                            min=0,
                                            max=100,
                                            step=5,
                                            value=50,
                                            marks=SLIDER_MARKS,
                                            updatemode="drag",
                                        ),
                                    ],
                                    className="kpi-card p-4 h-100",
                                ),
                                width=12,
                                lg=7,
                            ),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Span(
                                            "PROJEÇÃO DE GANHO OPERACIONAL",
                                            className="kpi-title mb-4 d-block",
                                            style={"color": "#cbd5e1"},
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Small("OEE Projetado", style={"color": "#94a3b8", "display": "block"}),
                                                        html.H3(id="sim-oee-value", style={"color": "#10b981", "fontWeight": "800", "fontSize": "2.2rem", "marginBottom": "0px"}),
                                                        html.Small(id="sim-oee-delta", style={"color": "#38bdf8", "fontWeight": "600"}),
                                                    ],
                                                    width=6,
                                                    className="mb-3",
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.Small("Tempo Recuperado", style={"color": "#94a3b8", "display": "block"}),
                                                        html.H3(id="sim-time-saved", style={"color": "#f59e0b", "fontWeight": "800", "fontSize": "2.2rem", "marginBottom": "0px"}),
                                                        html.Small("minutos em operação", style={"color": "#94a3b8"}),
                                                    ],
                                                    width=6,
                                                    className="mb-3",
                                                ),
                                            ]
                                        ),
                                        html.Hr(style={"borderColor": "#334155"}),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Small("Peças Boas Adicionais", style={"color": "#94a3b8", "display": "block"}),
                                                        html.H3(id="sim-extra-parts", style={"color": "#38bdf8", "fontWeight": "800", "fontSize": "2.2rem", "marginBottom": "0px"}),
                                                        html.Small(id="sim-total-good-parts", style={"color": "#cbd5e1", "fontSize": "0.9rem"}),
                                                    ],
                                                    width=12,
                                                )
                                            ]
                                        ),
                                    ],
                                    className="kpi-card p-4 h-100 d-flex flex-column justify-content-center",
                                ),
                                width=12,
                                lg=5,
                            ),
                        ],
                        className="mb-4",
                    ),
                ]
            ),
        ]
    )