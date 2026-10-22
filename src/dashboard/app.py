"""
Aplicação Principal Plotly Dash:
Painel Integrado de Telemetria Operacional, OEE, Simulador What-If,
Controle Estatístico de Processo (CEP), Confiabilidade & Downtime (TPM)
e Exportação de Relatórios Executivos (CSV/Excel).
Layout Panorâmico Horizontal em Alto Contraste.
"""

import io
from dash import Dash, Input, Output, ctx, dcc, html
import dash_bootstrap_components as dbc
import polars as pl

from src.core.downtime_engine import DowntimeEngine
from src.core.oee_engine import OEEEngine
from src.core.spc_engine import SPCEngine
from src.dashboard.components.charts import (
    create_capability_histogram,
    create_oee_timeline_gantt,
    create_oee_waterfall,
    create_pareto_chart,
    create_r_chart,
    create_sector_pareto_chart,
    create_stop_type_donut,
    create_xbar_chart,
)
from src.dashboard.layouts.tab_downtime import render_tab_downtime
from src.dashboard.layouts.tab_oee import render_tab_oee
from src.dashboard.layouts.tab_spc import render_tab_spc

# Motores de cálculo analítico
oee_engine = OEEEngine()
spc_engine = SPCEngine()
downtime_engine = DowntimeEngine()

# Instância da aplicação Dash
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
    title="Industrial Telemetry | OEE, TPM & SPC",
)

# Layout Raiz Horizontal Panorâmico
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
                                    "Monitoramento Operacional Contínuo: OEE, Gestão de Downtime (TPM) e Controle Estatístico de Processo",
                                    style={"color": "#94a3b8", "marginBottom": "20px", "fontSize": "1.02rem"},
                                ),
                            ],
                            width=12,
                        )
                    ]
                ),
                # Navegação em Abas (OEE, Confiabilidade/Downtime e CEP)
                dbc.Tabs(
                    [
                        dbc.Tab(
                            label="Desempenho Operacional (OEE)",
                            tab_id="tab-oee",
                        ),
                        dbc.Tab(
                            label="Confiabilidade & Downtime (TPM)",
                            tab_id="tab-downtime",
                        ),
                        dbc.Tab(
                            label="Engenharia da Qualidade (CEP)",
                            tab_id="tab-spc",
                        ),
                    ],
                    id="main-tabs",
                    active_tab="tab-oee",
                    className="nav-tabs mb-4",
                ),
                # Conteúdo dinâmico da aba ativa
                html.Div(id="tab-content"),
            ],
            fluid=True,
            className="px-4 py-2",
        )
    ],
    style={"backgroundColor": "#0f172a", "minHeight": "100vh"},
)


# ========================================================
# ROTEAMENTO DE ABAS
# ========================================================
@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab"),
)
def switch_tabs(active_tab):
    if active_tab == "tab-oee":
        return render_tab_oee()
    elif active_tab == "tab-downtime":
        return render_tab_downtime()
    elif active_tab == "tab-spc":
        return render_tab_spc()
    return html.Div("Selecione uma aba válida.")


# ========================================================
# CALLBACKS DA ABA DE OEE
# ========================================================
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
        with pl.Config(tbl_rows=-1):
            df_kpis.write_excel(
                workbook=excel_bytes,
                worksheet="Resumo_OEE",
                table_style="Table Style Medium 9",
            )
            df_pareto.write_excel(
                workbook=excel_bytes,
                worksheet="Pareto_Paradas",
                table_style="Table Style Medium 2",
            )
        return dcc.send_bytes(excel_bytes.getvalue(), "relatorio_executivo_oee.xlsx")


# ========================================================
# CALLBACKS DA NOVA ABA: DOWNTIME & CONFIABILIDADE (TPM)
# ========================================================
@app.callback(
    [
        Output("kpi-mtbf", "children"),
        Output("kpi-mttr", "children"),
        Output("kpi-tech-avail", "children"),
        Output("kpi-failures-count", "children"),
        Output("chart-pareto-sector", "figure"),
        Output("chart-donut-stop-type", "figure"),
        Output("table-downtime-events-container", "children"),
    ],
    Input("downtime-shift-filter", "value"),
)
def update_downtime_tab(selected_shift):
    shift_arg = None if selected_shift == "ALL" else selected_shift

    tpm_kpis = downtime_engine.calculate_tpm_kpis(shift_arg)
    df_sector = downtime_engine.get_pareto_by_sector(shift_arg)
    df_stop_types = downtime_engine.get_stop_type_breakdown(shift_arg)
    df_events = downtime_engine.get_detailed_downtime_log(shift_arg)

    kpi_mtbf = f"{tpm_kpis.mtbf_minutes:.1f} min"
    kpi_mttr = f"{tpm_kpis.mttr_minutes:.1f} min"
    kpi_avail = f"{tpm_kpis.technical_availability * 100:.1f}%"
    kpi_failures = f"{tpm_kpis.failures_count} falhas"

    fig_sector = create_sector_pareto_chart(df_sector)
    fig_donut = create_stop_type_donut(df_stop_types)

    # Construção da tabela executiva com as ocorrências
    if df_events.is_empty():
        table_component = html.P("Nenhum evento registrado no turno.", className="text-muted")
    else:
        # Exibe os 10 eventos mais recentes
        recent_events = df_events.head(10).to_dicts()
        table_rows = []
        for ev in recent_events:
            badge_color = "danger" if ev["stop_type"] == "NÃO_PLANEJADA" else "warning"
            table_rows.append(
                html.Tr(
                    [
                        html.Td(ev["start_time"].strftime("%H:%M:%S")),
                        html.Td(ev["end_time"].strftime("%H:%M:%S")),
                        html.Td(f"{ev['duration_min']:.1f} min", className="fw-bold text-info"),
                        html.Td(
                            dbc.Badge(
                                ev["stop_type"],
                                color=badge_color,
                                className="px-2 py-1",
                            )
                        ),
                        html.Td(ev["sector"], className="fw-bold"),
                        html.Td(ev["sub_reason"]),
                        html.Td(ev["shift"], className="text-muted"),
                    ]
                )
            )

        table_component = dbc.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Início"),
                            html.Th("Fim"),
                            html.Th("Duração"),
                            html.Th("Classificação"),
                            html.Th("Setor Responsável"),
                            html.Th("Motivo Operacional"),
                            html.Th("Turno"),
                        ],
                        style={"color": "#94a3b8", "borderBottom": "2px solid #334155"},
                    )
                ),
                html.Tbody(table_rows),
            ],
            responsive=True,
            hover=True,
            className="mb-0",
            style={"color": "#f8fafc", "fontSize": "0.9rem"},
        )

    return (
        kpi_mtbf,
        kpi_mttr,
        kpi_avail,
        kpi_failures,
        fig_sector,
        fig_donut,
        table_component,
    )


@app.callback(
    Output("download-downtime-report", "data"),
    [
        Input("btn-export-downtime-csv", "n_clicks"),
        Input("btn-export-downtime-excel", "n_clicks"),
    ],
    Input("downtime-shift-filter", "value"),
    prevent_initial_call=True,
)
def export_downtime_report(n_clicks_csv, n_clicks_excel, selected_shift):
    button_id = ctx.triggered_id
    if not button_id:
        return None

    shift_arg = None if selected_shift == "ALL" else selected_shift
    df_events = downtime_engine.get_detailed_downtime_log(shift_arg)
    df_sector = downtime_engine.get_pareto_by_sector(shift_arg)
    tpm_kpis = downtime_engine.calculate_tpm_kpis(shift_arg)

    if button_id == "btn-export-downtime-csv":
        csv_bytes = io.BytesIO()
        df_events.write_csv(csv_bytes)
        return dcc.send_bytes(csv_bytes.getvalue(), "relatorio_downtime_paradas.csv")

    elif button_id == "btn-export-downtime-excel":
        df_tpm = pl.DataFrame([
            {"Metrica": "MTBF (minutos)", "Valor": f"{tpm_kpis.mtbf_minutes:.1f}"},
            {"Metrica": "MTTR (minutos)", "Valor": f"{tpm_kpis.mttr_minutes:.1f}"},
            {"Metrica": "Disponibilidade Tecnica", "Valor": f"{tpm_kpis.technical_availability*100:.2f}%"},
            {"Metrica": "Contagem de Falhas Nao-Planejadas", "Valor": str(tpm_kpis.failures_count)},
            {"Metrica": "Total Minutos Parados", "Valor": f"{tpm_kpis.total_downtime_minutes:.1f}"},
        ])

        excel_bytes = io.BytesIO()
        with pl.Config(tbl_rows=-1):
            df_tpm.write_excel(
                workbook=excel_bytes,
                worksheet="Resumo_TPM",
                table_style="Table Style Medium 9",
            )
            df_sector.write_excel(
                workbook=excel_bytes,
                worksheet="Pareto_Setores",
                table_style="Table Style Medium 2",
            )
            df_events.write_excel(
                workbook=excel_bytes,
                worksheet="Historico_Paradas",
                table_style="Table Style Medium 4",
            )
        return dcc.send_bytes(excel_bytes.getvalue(), "relatorio_auditoria_downtime.xlsx")


# ========================================================
# CALLBACKS DA ABA DE CEP
# ========================================================
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