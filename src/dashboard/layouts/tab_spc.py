"""
Layout da Aba de CEP:
Adiciona o container do histograma de capacidade, cartas de controle, alertas Nelson
e botões de exportação de dados em CSV e Excel.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


def render_tab_spc() -> html.Div:
    return html.Div(
        [
            # Barra Superior de Ações e Exportação
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "EXPORTAÇÃO DOS DADOS DE QUALIDADE (CEP)",
                                className="kpi-title mb-2 d-block",
                                style={"color": "#94a3b8", "fontWeight": "600"},
                            ),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        "Exportar CSV",
                                        id="btn-export-spc-csv",
                                        color="secondary",
                                        className="fw-bold px-3",
                                        outline=True,
                                    ),
                                    dbc.Button(
                                        "Exportar Excel (.xlsx)",
                                        id="btn-export-spc-excel",
                                        color="success",
                                        className="fw-bold px-3 ms-2",
                                        outline=True,
                                    ),
                                ]
                            ),
                            dcc.Download(id="download-spc-report"),
                        ],
                        width=12,
                        className="mb-4 d-flex flex-column align-items-end justify-content-end",
                    )
                ]
            ),
            # Cartões de Métricas Estatísticas
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("POTENCIAL DE PROCESSO (Cp)", className="kpi-title"),
                                html.Div(id="kpi-cp", className="kpi-value"),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("CAPABILIDADE REAL (Cpk)", className="kpi-title"),
                                html.Div(id="kpi-cpk", className="kpi-value text-info"),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("MÉDIA DO PROCESSO (X̿)", className="kpi-title"),
                                html.Div(id="kpi-xbar", className="kpi-value"),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("DISPERSÃO ESTIMADA (σ̂)", className="kpi-title"),
                                html.Div(id="kpi-sigma", className="kpi-value"),
                            ],
                            className="kpi-card p-3 mb-3",
                        ),
                        width=6,
                        lg=3,
                    ),
                ]
            ),
            # Alerta das Regras de Nelson
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Alert(
                            id="alert-nelson-rules",
                            color="danger",
                            className="mb-4 shadow-sm border-0",
                        ),
                        width=12,
                    )
                ]
            ),
            # Histograma de Capacidade
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            dcc.Graph(id="chart-hist-capability", config={"displayModeBar": False}),
                            className="kpi-card p-2 mb-4",
                        ),
                        width=12,
                    )
                ]
            ),
            # Cartas de Controle Shewhart (X-barra e R)
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            dcc.Graph(id="chart-xbar", config={"displayModeBar": False}),
                            className="kpi-card p-2 mb-4",
                        ),
                        width=12,
                        lg=6,
                    ),
                    dbc.Col(
                        html.Div(
                            dcc.Graph(id="chart-r", config={"displayModeBar": False}),
                            className="kpi-card p-2 mb-4",
                        ),
                        width=12,
                        lg=6,
                    ),
                ]
            ),
        ]
    )