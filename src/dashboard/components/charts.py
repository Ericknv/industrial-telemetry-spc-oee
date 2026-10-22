"""
Módulo de Visualização Gráfica (Plotly):
Gera figuras analíticas interativas de OEE, Confiabilidade (Downtime/TPM)
e Controle Estatístico de Processo (CEP) no Design System Slate de Alto Contraste.
"""

from typing import Dict, List
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import polars as pl

from src.core.oee_engine import OEEMetrics
from src.core.spc_engine import SPCLimits

# Paleta Industrial Slate Unificada
DARK_BG = "#0f172a"        # Fundo interno da plotagem
PAPER_BG = "#1e293b"       # Fundo dos cartões e contêineres
TEXT_COLOR = "#f8fafc"     # Texto principal nítido
MUTED_TEXT = "#94a3b8"     # Legendas e rótulos secundários
GRID_COLOR = "#334155"     # Linhas de grade sutis
ACCENT_CYAN = "#38bdf8"    # Ciano de telemetria
SUCCESS_GREEN = "#10b981"  # Verde operacional
WARNING_AMBER = "#f59e0b"  # Amarelo de atenção
ALERT_RED = "#ef4444"      # Vermelho de paradas e falhas


def create_oee_waterfall(metrics: OEEMetrics) -> go.Figure:
    """Gráfico em cascata decompondo perdas de disponibilidade, performance e refugo."""
    planned_min = metrics.planned_time_sec / 60.0
    downtime_min = (metrics.planned_time_sec - metrics.operating_time_sec) / 60.0
    speed_loss_min = (metrics.operating_time_sec - metrics.net_operating_time_sec) / 60.0
    quality_loss_min = (metrics.net_operating_time_sec - metrics.valuable_operating_time_sec) / 60.0
    valuable_min = metrics.valuable_operating_time_sec / 60.0

    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "total"],
            x=[
                "Tempo Planejado",
                "Paradas (Disp.)",
                "Velocidade (Perf.)",
                "Refugos (Qual.)",
                "Tempo Efetivo",
            ],
            textposition="outside",
            text=[
                f"{planned_min:.0f}m",
                f"-{downtime_min:.0f}m",
                f"-{speed_loss_min:.0f}m",
                f"-{quality_loss_min:.0f}m",
                f"{valuable_min:.0f}m",
            ],
            y=[
                planned_min,
                -downtime_min,
                -speed_loss_min,
                -quality_loss_min,
                valuable_min,
            ],
            decreasing={"marker": {"color": ALERT_RED}},
            increasing={"marker": {"color": SUCCESS_GREEN}},
            totals={"marker": {"color": ACCENT_CYAN}},
        )
    )

    fig.update_layout(
        title=dict(
            text="<b>DECOMPOSIÇÃO DE PERDAS OPERACIONAIS (TEMPO)</b>",
            font=dict(size=13, color=TEXT_COLOR),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family="Segoe UI, sans-serif"),
        margin=dict(l=40, r=40, t=55, b=40),
        yaxis=dict(title="Minutos", gridcolor=GRID_COLOR),
        xaxis=dict(gridcolor=GRID_COLOR),
    )
    return fig


def create_pareto_chart(df_pareto: pl.DataFrame) -> go.Figure:
    """Diagrama de Pareto com barras ordenadas e curva percentual acumulada."""
    if df_pareto.is_empty():
        return go.Figure()

    reasons = df_pareto["stop_reason"].to_list()
    durations = df_pareto["duration_minutes"].to_list()
    cum_pct = df_pareto["cumulative_pct"].to_list()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=reasons,
            y=durations,
            name="Tempo Parado (min)",
            marker_color=ACCENT_CYAN,
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=reasons,
            y=cum_pct,
            name="% Acumulado",
            mode="lines+markers",
            line=dict(color=WARNING_AMBER, width=2.5),
            marker=dict(size=7),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title=dict(
            text="<b>DIAGRAMA DE PARETO: CAUSAS DE PARADA DE LINHA</b>",
            font=dict(size=13, color=TEXT_COLOR),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family="Segoe UI, sans-serif"),
        margin=dict(l=40, r=40, t=55, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor=GRID_COLOR),
    )

    fig.update_yaxes(title_text="Minutos Parados", gridcolor=GRID_COLOR, secondary_y=False)
    fig.update_yaxes(
        title_text="% Acumulado",
        range=[0, 105],
        gridcolor=GRID_COLOR,
        secondary_y=True,
    )
    return fig


def create_oee_timeline_gantt(df_timeline: pl.DataFrame) -> go.Figure:
    """Linha do tempo contínua em raias operacionais (Swimlanes)."""
    if df_timeline.is_empty():
        return go.Figure()

    color_map = {
        "PRODUÇÃO REGULAR (RUN)": SUCCESS_GREEN,
        "SETUP_AJUSTE": WARNING_AMBER,
        "FALHA_MECANICA": ALERT_RED,
        "FALTA_MATERIAL": "#c084fc",
        "MICROPARADA_SENSOR": ACCENT_CYAN,
        "INSPECAO_QUALIDADE": "#38bdf8",
    }

    standard_categories = [
        "INSPECAO_QUALIDADE",
        "MICROPARADA_SENSOR",
        "FALHA_MECANICA",
        "FALTA_MATERIAL",
        "SETUP_AJUSTE",
        "PRODUÇÃO REGULAR (RUN)",
    ]

    fig = go.Figure()

    for cat in standard_categories:
        sub_df = df_timeline.filter(pl.col("category") == cat)
        color = color_map.get(cat, MUTED_TEXT)

        if sub_df.is_empty():
            fig.add_trace(
                go.Bar(
                    base=[df_timeline["start_time"][0]],
                    x=[0],
                    y=[cat],
                    orientation="h",
                    marker=dict(color="rgba(0,0,0,0)"),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            continue

        starts = sub_df["start_time"].to_list()
        ends = sub_df["end_time"].to_list()
        mins = sub_df["duration_min"].to_list()
        durs_sec = sub_df["duration_sec"].to_list()

        for i in range(len(starts)):
            dur_visual_sec = max(durs_sec[i], 180.0) if cat != "PRODUÇÃO REGULAR (RUN)" else durs_sec[i]
            dur_ms = dur_visual_sec * 1000.0
            st = starts[i]
            et = ends[i]

            fig.add_trace(
                go.Bar(
                    base=st,
                    x=[dur_ms],
                    y=[cat],
                    orientation="h",
                    marker=dict(
                        color=color,
                        line=dict(color="#f8fafc" if cat != "PRODUÇÃO REGULAR (RUN)" else "#0f172a", width=0.8),
                    ),
                    name=cat,
                    showlegend=(i == 0),
                    legendgroup=cat,
                    hovertemplate=(
                        f"<b>{cat}</b><br>"
                        + f"Início: {st.strftime('%H:%M:%S')}<br>"
                        + f"Fim: {et.strftime('%H:%M:%S')}<br>"
                        + f"Duração Real: <b>{mins[i]:.1f} min</b><extra></extra>"
                    ),
                )
            )

    fig.update_layout(
        title=dict(
            text="<b>LINHA DO TEMPO DE OPERAÇÃO FABRIL (SWIMLANES)</b>",
            x=0.01,
            y=0.98,
            font=dict(size=13, color=TEXT_COLOR),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family="Segoe UI, sans-serif"),
        margin=dict(l=200, r=40, t=75, b=45),
        barmode="overlay",
        bargap=0.35,
        height=380,
        xaxis=dict(
            title="Horário de Produção",
            type="date",
            gridcolor=GRID_COLOR,
            showgrid=True,
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            tickfont=dict(size=11, color=TEXT_COLOR),
            categoryorder="array",
            categoryarray=standard_categories,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0.01,
            font=dict(size=10.5),
        ),
    )
    return fig


# ========================================================
# NOVOS COMPONENTES GRÁFICOS: DOWNTIME & CONFIABILIDADE (TPM)
# ========================================================

def create_sector_pareto_chart(df_sector_pareto: pl.DataFrame) -> go.Figure:
    """Diagrama de Pareto estratificado por setor fabril responsável pelas paradas."""
    if df_sector_pareto.is_empty():
        return go.Figure()

    sectors = df_sector_pareto["sector"].to_list()
    durations = df_sector_pareto["duration_minutes"].to_list()
    cum_pct = df_sector_pareto["cumulative_pct"].to_list()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=sectors,
            y=durations,
            name="Tempo de Parada (min)",
            marker=dict(
                color=ALERT_RED,
                line=dict(color=PAPER_BG, width=1.5),
            ),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=sectors,
            y=cum_pct,
            name="% Acumulado de Perdas",
            mode="lines+markers",
            line=dict(color=WARNING_AMBER, width=2.5),
            marker=dict(size=8, color=WARNING_AMBER),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title=dict(
            text="<b>ESTRATIFICAÇÃO DE DOWNTIME POR SETOR RESPONSÁVEL</b>",
            font=dict(size=13, color=TEXT_COLOR),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family="Segoe UI, sans-serif"),
        margin=dict(l=40, r=40, t=55, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor=GRID_COLOR),
    )

    fig.update_yaxes(title_text="Minutos Parados", gridcolor=GRID_COLOR, secondary_y=False)
    fig.update_yaxes(
        title_text="% Acumulado",
        range=[0, 105],
        gridcolor=GRID_COLOR,
        secondary_y=True,
    )
    return fig


def create_stop_type_donut(df_stop_types: pl.DataFrame) -> go.Figure:
    """Gráfico de rosca (Donut) categorizando Paradas Planejadas vs. Não-Planejadas."""
    if df_stop_types.is_empty():
        return go.Figure()

    types = df_stop_types["stop_type"].to_list()
    minutes = df_stop_types["total_minutes"].to_list()

    colors = [
        WARNING_AMBER if t == "PLANEJADA" else ALERT_RED
        for t in types
    ]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=types,
                values=minutes,
                hole=0.6,
                marker=dict(colors=colors, line=dict(color=PAPER_BG, width=2)),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Tempo: %{value:.1f} min<br>Proporção: %{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text="<b>CLASSIFICAÇÃO DE PARADAS (TPM)</b>",
            font=dict(size=13, color=TEXT_COLOR),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family="Segoe UI, sans-serif"),
        margin=dict(l=30, r=30, t=55, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
    )
    return fig


# ========================================================
# COMPONENTES GRÁFICOS: ENGENHARIA DA QUALIDADE (CEP)
# ========================================================

def create_xbar_chart(
    df_subgroups: pl.DataFrame, limits: SPCLimits, violations: Dict[int, List[int]]
) -> go.Figure:
    """Carta X-barra com limites de controle e destaque para violações de Nelson."""
    subgroups = df_subgroups["subgroup_id"].to_list()
    means = df_subgroups["x_bar"].to_list()

    anomalous_indices = set()
    for rule, idxs in violations.items():
        anomalous_indices.update(idxs)

    point_colors = [
        ALERT_RED if i in anomalous_indices else ACCENT_CYAN
        for i in range(len(subgroups))
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=subgroups,
            y=means,
            mode="lines+markers",
            name="Média Amostral (X̄)",
            line=dict(color=MUTED_TEXT, width=1.5),
            marker=dict(color=point_colors, size=8),
        )
    )

    fig.add_hline(
        y=limits.x_ucl,
        line_dash="dash",
        line_color=ALERT_RED,
        annotation_text=f"UCL: {limits.x_ucl}",
    )
    fig.add_hline(
        y=limits.x_cl,
        line_color=SUCCESS_GREEN,
        annotation_text=f"CL (X̿): {limits.x_cl}",
    )
    fig.add_hline(
        y=limits.x_lcl,
        line_dash="dash",
        line_color=ALERT_RED,
        annotation_text=f"LCL: {limits.x_lcl}",
    )

    fig.update_layout(
        title=dict(
            text="<b>CARTA DE CONTROLE DE MÉDIAS (X̄)</b>",
            font=dict(size=13, color=TEXT_COLOR),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family="Segoe UI, sans-serif"),
        margin=dict(l=40, r=40, t=55, b=40),
        xaxis=dict(title="Subgrupo Racional (k)", gridcolor=GRID_COLOR),
        yaxis=dict(title="Dimensão (mm)", gridcolor=GRID_COLOR),
    )
    return fig


def create_r_chart(df_subgroups: pl.DataFrame, limits: SPCLimits) -> go.Figure:
    """Carta R (Amplitude) para monitoramento da variabilidade intra-subgrupo."""
    subgroups = df_subgroups["subgroup_id"].to_list()
    ranges = df_subgroups["r_range"].to_list()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=subgroups,
            y=ranges,
            mode="lines+markers",
            name="Amplitude (R)",
            line=dict(color=ACCENT_CYAN, width=1.5),
            marker=dict(size=7),
        )
    )

    fig.add_hline(
        y=limits.r_ucl,
        line_dash="dash",
        line_color=ALERT_RED,
        annotation_text=f"UCL: {limits.r_ucl}",
    )
    fig.add_hline(
        y=limits.r_cl,
        line_color=SUCCESS_GREEN,
        annotation_text=f"CL (R̄): {limits.r_cl}",
    )
    fig.add_hline(y=limits.r_lcl, line_dash="dash", line_color=ALERT_RED)

    fig.update_layout(
        title=dict(
            text="<b>CARTA DE CONTROLE DE AMPLITUDE (R)</b>",
            font=dict(size=13, color=TEXT_COLOR),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family="Segoe UI, sans-serif"),
        margin=dict(l=40, r=40, t=55, b=40),
        xaxis=dict(title="Subgrupo Racional (k)", gridcolor=GRID_COLOR),
        yaxis=dict(title="Amplitude (mm)", gridcolor=GRID_COLOR),
    )
    return fig


def create_capability_histogram(
    df_raw_samples: pl.DataFrame, limits: SPCLimits
) -> go.Figure:
    """Histograma com curva normal ajustada e limites LSL/USL."""
    if df_raw_samples.is_empty():
        return go.Figure()

    values = df_raw_samples["measured_value_mm"].to_numpy()
    lsl = float(df_raw_samples["lsl"][0])
    usl = float(df_raw_samples["usl"][0])
    target = float(df_raw_samples["nominal_target"][0])

    mu = float(np.mean(values))
    sigma = float(np.std(values, ddof=1))

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=values,
            histnorm="probability density",
            name="Medições Reais",
            marker=dict(
                color=ACCENT_CYAN,
                opacity=0.65,
                line=dict(color=TEXT_COLOR, width=0.5),
            ),
            nbinsx=25,
        )
    )

    x_range = np.linspace(min(min(values), lsl - 0.01), max(max(values), usl + 0.01), 200)
    if sigma > 0:
        pdf = (1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_range - mu) / sigma) ** 2)
        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=pdf,
                mode="lines",
                name="Curva Gaussiana Teórica",
                line=dict(color=WARNING_AMBER, width=2.5),
            )
        )

    fig.add_vline(
        x=lsl,
        line_dash="dash",
        line_color=ALERT_RED,
        line_width=2,
        annotation_text=f"LSL: {lsl:.3f}",
        annotation_position="top left",
        annotation_font=dict(color=ALERT_RED, size=11),
    )
    fig.add_vline(
        x=target,
        line_dash="dot",
        line_color=SUCCESS_GREEN,
        line_width=1.5,
        annotation_text=f"Nominal: {target:.3f}",
        annotation_position="top",
        annotation_font=dict(color=SUCCESS_GREEN, size=11),
    )
    fig.add_vline(
        x=usl,
        line_dash="dash",
        line_color=ALERT_RED,
        line_width=2,
        annotation_text=f"USL: {usl:.3f}",
        annotation_position="top right",
        annotation_font=dict(color=ALERT_RED, size=11),
    )

    fig.update_layout(
        title=dict(
            text=f"<b>DISTRIBUIÇÃO DIMENSIONAL E CAPACIDADE (Cp: {limits.cp:.2f} | Cpk: {limits.cpk:.2f})</b>",
            font=dict(size=13, color=TEXT_COLOR),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=DARK_BG,
        font=dict(color=TEXT_COLOR, family="Segoe UI, sans-serif"),
        margin=dict(l=40, r=40, t=55, b=40),
        xaxis=dict(title="Dimensão Medida (mm)", gridcolor=GRID_COLOR),
        yaxis=dict(title="Densidade de Probabilidade", gridcolor=GRID_COLOR),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig