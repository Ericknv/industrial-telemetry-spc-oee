"""
Aplicação Principal Plotly Dash:
Painel Integrado de Telemetria Operacional, OEE, Simulador What-If,
Controle Estatístico de Processo (CEP) e Exportação de Relatórios Executivos (CSV/Excel).
"""

import io
from dash import Dash, Input, Output, ctx, dcc, html
import dash_bootstrap_components as dbc
import polars as pl

from src.core.oee_engine import OEEEngine
from src.core.spc_engine import SPCEngine
from src.dashboard.components.charts import (
    create_capability_histogram,
    create_oee_timeline_gantt,
    create_oee_waterfall,
    create_pareto_chart,
    create_r_chart,
    create_xbar_chart,
)
from src.dashboard.layouts.tab_oee import render_tab_oee
from src.dashboard.layouts.tab_spc import render_tab_spc

# Motores de cálculo
oee_engine = OEEEngine()
spc_engine = SPCEngine()

# Instância da aplicação Dash
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
    title="Industrial Analytics | OEE & SPC",
)

# Layout Raiz
app.layout = html.Div(
    [
        dbc.Container(
            [
                # Cabeçalho da Aplicação
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H2(
                                    "Plataforma de Telemetria e Qualidade Fabril",
                                    style={"color": "#f8fafc", "fontWeight": "700", "marginTop": "20px"},
                                ),
                                html.P(
                                    "Monitoramento Operacional Contínuo: OEE e Controle Estatístico de Processo",
                                    style={"color": "#94a3b8", "marginBottom": "25px", "fontSize": "1.05rem"},
                                ),
                            ],
                            width=12,
                        )
                    ]
                ),
                # Navegação em Abas
                dbc.Tabs(
                    [
                        dbc.Tab(
                            label="Desempenho Operacional (OEE)",
                            tab_id="tab-oee",
                            tab_style={"backgroundColor": "#1e293b", "border": "none"},
                            active_tab_style={"backgroundColor": "#334155", "color": "#38bdf8", "fontWeight": "bold"},
                        ),
                        dbc.Tab(
                            label="Engenharia da Qualidade (CEP)",
                            tab_id="tab-spc",
                            tab_style={"backgroundColor": "#1e293b", "border": "none"},
                            active_tab_style={"backgroundColor": "#334155", "color": "#38bdf8", "fontWeight": "bold"},
                        ),
                    ],
                    id="main-tabs",
                    active_tab="tab-oee",
                    className="mb-4",
                ),
                # Contêiner dinâmico do conteúdo da aba ativa
                html.Div(id="tab-content"),
            ],
            fluid=True,
            className="px-4 py-2",
        )
    ],
    style={"backgroundColor": "#0f172a", "minHeight": "100vh", "color": "#f8fafc"},
)


@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab"),
)
def switch_tabs(active_tab):
    if active_tab == "tab-oee":
        return render_tab_oee()
    elif active_tab == "tab-spc":
        return render_tab_spc()
    return html.Div("Selecione uma aba válida.")


@app.callback(
    [
        Output("kpi-oee", "children"),
        Output("kpi-availability", "children"),
        Output("kpi-performance", "children"),
        Output("kpi-quality", "children"),
        Output("chart-oee-timeline", "figure"),
        Output("chart-oee-waterfall", "figure"),
        Output("chart-pareto", "figure"),
    ],
    Input("oee-shift-filter", "value"),
)
def update_oee_tab(selected_shift):
    shift_arg = None if selected_shift == "ALL" else selected_shift

    metrics = oee_engine.calculate_oee(shift_arg)
    df_pareto = oee_engine.get_downtime_pareto(shift_arg)
    df_timeline = oee_engine.get_timeline_events(shift_arg)

    kpi_oee = f"{metrics.oee * 100:.1f}%"
    kpi_avail = f"{metrics.availability * 100:.1f}%"
    kpi_perf = f"{metrics.performance * 100:.1f}%"
    kpi_qual = f"{metrics.quality * 100:.1f}%"

    fig_timeline = create_oee_timeline_gantt(df_timeline)
    fig_waterfall = create_oee_waterfall(metrics)
    fig_pareto = create_pareto_chart(df_pareto)

    return (
        kpi_oee,
        kpi_avail,
        kpi_perf,
        kpi_qual,
        fig_timeline,
        fig_waterfall,
        fig_pareto,
    )


# Callback Reativo do Simulador What-If
@app.callback(
    [
        Output("sim-oee-value", "children"),
        Output("sim-oee-delta", "children"),
        Output("sim-time-saved", "children"),
        Output("sim-extra-parts", "children"),
        Output("sim-total-good-parts", "children"),
        Output("badge-setup-value", "children"),
        Output("badge-breakdown-value", "children"),
        Output("badge-scrap-value", "children"),
    ],
    [
        Input("oee-shift-filter", "value"),
        Input("slider-setup-reduction", "value"),
        Input("slider-breakdown-reduction", "value"),
        Input("slider-scrap-reduction", "value"),
    ],
)
def update_what_if_simulation(shift, setup_pct, breakdown_pct, scrap_pct):
    shift_arg = None if shift == "ALL" else shift
    proj = oee_engine.simulate_what_if(
        shift_filter=shift_arg,
        setup_reduction_pct=float(setup_pct),
        breakdown_reduction_pct=float(breakdown_pct),
        scrap_reduction_pct=float(scrap_pct),
    )

    oee_text = f"{proj.simulated_oee:.1f}%"
    delta_text = f"+{proj.delta_oee_pct:.1f}% vs. Real ({proj.baseline_oee:.1f}%)"
    time_text = f"{proj.saved_downtime_minutes:.0f}m"
    extra_parts_text = f"+{proj.additional_good_parts:,} un"
    total_text = f"Total Projetado: {proj.simulated_good_parts:,} peças boas"

    badge_setup = f"-{setup_pct}%"
    badge_breakdown = f"-{breakdown_pct}%"
    badge_scrap = f"-{scrap_pct}%"

    return (
        oee_text,
        delta_text,
        time_text,
        extra_parts_text,
        total_text,
        badge_setup,
        badge_breakdown,
        badge_scrap,
    )


# Callback de Exportação da Aba de OEE (CSV / Excel direto pelo Polars)
@app.callback(
    Output("download-oee-report", "data"),
    [
        Input("btn-export-oee-csv", "n_clicks"),
        Input("btn-export-oee-excel", "n_clicks"),
    ],
    Input("oee-shift-filter", "value"),
    prevent_initial_call=True,
)
def export_oee_report(n_clicks_csv, n_clicks_excel, selected_shift):
    button_id = ctx.triggered_id
    if not button_id:
        return None

    shift_arg = None if selected_shift == "ALL" else selected_shift
    df_pareto = oee_engine.get_downtime_pareto(shift_arg)
    metrics = oee_engine.calculate_oee(shift_arg)

    if button_id == "btn-export-oee-csv":
        csv_bytes = io.BytesIO()
        df_pareto.write_csv(csv_bytes)
        return dcc.send_bytes(csv_bytes.getvalue(), "relatorio_paradas_oee.csv")

    elif button_id == "btn-export-oee-excel":
        df_kpis = pl.DataFrame([
            {"Metrica": "Disponibilidade", "Valor": f"{metrics.availability*100:.2f}%"},
            {"Metrica": "Performance", "Valor": f"{metrics.performance*100:.2f}%"},
            {"Metrica": "Qualidade", "Valor": f"{metrics.quality*100:.2f}%"},
            {"Metrica": "OEE Global", "Valor": f"{metrics.oee*100:.2f}%"},
            {"Metrica": "Total Produzido", "Valor": str(metrics.total_produced)},
            {"Metrica": "Pecas Boas", "Valor": str(metrics.good_parts)},
            {"Metrica": "Refugos", "Valor": str(metrics.total_defective)},
        ])

        excel_bytes = io.BytesIO()
        # Exporta com abas separadas utilizando a engine nativa do Polars
        with pl.Config(tbl_rows=-1):
            df_kpis.write_excel(
                workbook=excel_bytes,
                worksheet="Resumo_OEE",
                table_style="Table Style Medium 9",
            )
            # Adiciona o pareto como segunda aba
            df_pareto.write_excel(
                workbook=excel_bytes,
                worksheet="Pareto_Paradas",
                table_style="Table Style Medium 2",
            )
        return dcc.send_bytes(excel_bytes.getvalue(), "relatorio_executivo_oee.xlsx")


# Callback para a Aba de CEP
@app.callback(
    [
        Output("kpi-cp", "children"),
        Output("kpi-cpk", "children"),
        Output("kpi-xbar", "children"),
        Output("kpi-sigma", "children"),
        Output("alert-nelson-rules", "children"),
        Output("alert-nelson-rules", "is_open"),
        Output("chart-hist-capability", "figure"),
        Output("chart-xbar", "figure"),
        Output("chart-r", "figure"),
    ],
    Input("main-tabs", "active_tab"),
)
def update_spc_tab(active_tab):
    if active_tab != "tab-spc":
        return "--", "--", "--", "--", "", False, {}, {}, {}

    df_subgroups = spc_engine.get_subgroup_summary()
    df_raw = spc_engine.get_raw_inspections()
    limits = spc_engine.calculate_limits_and_capability(df_subgroups)

    violations = spc_engine.evaluate_nelson_rules(
        df_subgroups["x_bar"].to_list(),
        limits.x_cl,
        limits.x_ucl,
        limits.x_lcl,
    )

    alert_messages = []
    if violations[1]:
        subgroups_r1 = [df_subgroups["subgroup_id"][i] for i in violations[1]]
        alert_messages.append(f"Regra 1 (Ponto além de 3σ): Subgrupos {subgroups_r1}.")
    if violations[2]:
        subgroups_r2 = [df_subgroups["subgroup_id"][i] for i in violations[2]]
        alert_messages.append(f"Regra 2 (9 pontos do mesmo lado da média): Subgrupos {subgroups_r2}.")
    if violations[3]:
        subgroups_r3 = [df_subgroups["subgroup_id"][i] for i in violations[3]]
        alert_messages.append(f"Regra 3 (6 pontos em tendência): Subgrupos {subgroups_r3}.")

    has_alerts = len(alert_messages) > 0
    alert_text = (
        " | ".join(alert_messages)
        if has_alerts
        else "Processo sob controle estatístico. Nenhuma causa especial identificada."
    )

    fig_hist = create_capability_histogram(df_raw, limits)
    fig_xbar = create_xbar_chart(df_subgroups, limits, violations)
    fig_r = create_r_chart(df_subgroups, limits)

    return (
        f"{limits.cp:.2f}",
        f"{limits.cpk:.2f}",
        f"{limits.x_cl:.4f} mm",
        f"{limits.sigma_est:.4f} mm",
        alert_text,
        has_alerts,
        fig_hist,
        fig_xbar,
        fig_r,
    )


# Callback de Exportação da Aba de CEP (CSV / Excel direto pelo Polars)
@app.callback(
    Output("download-spc-report", "data"),
    [
        Input("btn-export-spc-csv", "n_clicks"),
        Input("btn-export-spc-excel", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def export_spc_report(n_clicks_csv, n_clicks_excel):
    button_id = ctx.triggered_id
    if not button_id:
        return None

    df_spc = spc_engine.get_exportable_spc_report()
    df_raw = spc_engine.get_raw_inspections()

    if button_id == "btn-export-spc-csv":
        csv_bytes = io.BytesIO()
        df_spc.write_csv(csv_bytes)
        return dcc.send_bytes(csv_bytes.getvalue(), "relatorio_qualidade_cep.csv")

    elif button_id == "btn-export-spc-excel":
        excel_bytes = io.BytesIO()
        with pl.Config(tbl_rows=-1):
            df_spc.write_excel(
                workbook=excel_bytes,
                worksheet="Subgrupos_Limites_Regras",
                table_style="Table Style Medium 9",
            )
            df_raw.write_excel(
                workbook=excel_bytes,
                worksheet="Medicoes_Individuais",
                table_style="Table Style Medium 2",
            )
        return dcc.send_bytes(excel_bytes.getvalue(), "relatorio_engenharia_qualidade.xlsx")


if __name__ == "__main__":
    app.run(debug=True, port=8050)