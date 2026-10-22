"""
Motor Analítico de Downtime & Confiabilidade Industrial (TPM):
Processa métricas de paradas operacionais via DuckDB e Polars,
calculando MTBF, MTTR, Disponibilidade Técnica, Pareto Multissetorial
e decomposição entre paradas Planejadas vs. Não-Planejadas.
"""

from dataclasses import dataclass
from typing import Optional
import duckdb
import polars as pl


@dataclass(frozen=True)
class DowntimeMetrics:
    total_downtime_minutes: float
    planned_downtime_minutes: float
    unplanned_downtime_minutes: float
    failures_count: int
    mtbf_minutes: float
    mttr_minutes: float
    technical_availability: float


class DowntimeEngine:
    def __init__(self, db_path: str = "data/telemetry.duckdb"):
        self.db_path = db_path

    def _query_to_polars(self, query: str, params: list = None) -> pl.DataFrame:
        con = duckdb.connect(self.db_path, read_only=True)
        try:
            if params:
                for p in params:
                    query = query.replace("?", f"'{p}'", 1)
            return con.sql(query).pl()
        finally:
            con.close()

    def calculate_tpm_kpis(self, shift_filter: Optional[str] = None) -> DowntimeMetrics:
        """
        Calcula os indicadores fundamentais de TPM: MTBF, MTTR,
        Disponibilidade Técnica e tempos segregados de parada.
        """
        shift_clause = "WHERE shift = ?" if shift_filter else ""
        params = [shift_filter] if shift_filter else []

        query = f"""
            SELECT 
                category,
                stop_type,
                duration_min,
                duration_sec
            FROM operational_events
            {shift_clause}
        """
        df = self._query_to_polars(query, params)

        if df.is_empty():
            return DowntimeMetrics(0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0)

        # Tempo de regime operacional (RUN)
        df_run = df.filter(pl.col("category") == "PRODUÇÃO REGULAR (RUN)")
        operating_time_min = float(df_run["duration_min"].sum()) if not df_run.is_empty() else 0.0

        # Paradas não-planejadas (Falhas corretivas e imprevistos)
        df_unplanned = df.filter(pl.col("stop_type") == "NÃO_PLANEJADA")
        unplanned_min = float(df_unplanned["duration_min"].sum()) if not df_unplanned.is_empty() else 0.0
        failures_count = len(df_unplanned)

        # Paradas planejadas (Setups, inspeções programadas)
        df_planned = df.filter(pl.col("stop_type") == "PLANEJADA")
        planned_min = float(df_planned["duration_min"].sum()) if not df_planned.is_empty() else 0.0

        total_downtime_min = unplanned_min + planned_min

        # Cálculo do MTBF e MTTR
        if failures_count > 0:
            mtbf = operating_time_min / failures_count
            mttr = unplanned_min / failures_count
            tech_avail = mtbf / (mtbf + mttr) if (mtbf + mttr) > 0 else 0.0
        else:
            mtbf = operating_time_min
            mttr = 0.0
            tech_avail = 1.0

        return DowntimeMetrics(
            total_downtime_minutes=round(total_downtime_min, 1),
            planned_downtime_minutes=round(planned_min, 1),
            unplanned_downtime_minutes=round(unplanned_min, 1),
            failures_count=failures_count,
            mtbf_minutes=round(mtbf, 1),
            mttr_minutes=round(mttr, 1),
            technical_availability=round(tech_avail, 4),
        )

    def get_pareto_by_sector(self, shift_filter: Optional[str] = None) -> pl.DataFrame:
        """
        Gera a estratificação de Pareto por setor fabril responsável,
        com minutos parados, frequência e percentual acumulado.
        """
        shift_filter_sql = "AND shift = ?" if shift_filter else ""
        params = [shift_filter] if shift_filter else []

        query = f"""
            SELECT 
                sector,
                ROUND(SUM(duration_min), 1) as duration_minutes,
                COUNT(*) as occurrence_count
            FROM operational_events
            WHERE category != 'PRODUÇÃO REGULAR (RUN)'
            {shift_filter_sql}
            GROUP BY sector
            ORDER BY duration_minutes DESC
        """
        df = self._query_to_polars(query, params)

        if df.is_empty():
            return df

        total_minutes = df["duration_minutes"].sum()
        if total_minutes > 0:
            df = df.with_columns(
                (
                    pl.col("duration_minutes").cum_sum() / total_minutes * 100.0
                ).round(1).alias("cumulative_pct")
            )
        else:
            df = df.with_columns(pl.lit(0.0).alias("cumulative_pct"))

        return df

    def get_stop_type_breakdown(self, shift_filter: Optional[str] = None) -> pl.DataFrame:
        """
        Retorna o somatório de tempo por tipo de evento (PLANEJADA vs NÃO_PLANEJADA).
        """
        shift_filter_sql = "AND shift = ?" if shift_filter else ""
        params = [shift_filter] if shift_filter else []

        query = f"""
            SELECT 
                stop_type,
                ROUND(SUM(duration_min), 1) as total_minutes,
                COUNT(*) as count
            FROM operational_events
            WHERE category != 'PRODUÇÃO REGULAR (RUN)'
            {shift_filter_sql}
            GROUP BY stop_type
            ORDER BY total_minutes DESC
        """
        return self._query_to_polars(query, params)

    def get_detailed_downtime_log(self, shift_filter: Optional[str] = None) -> pl.DataFrame:
        """
        Retorna a relação cronológica tabular de cada ocorrência de parada
        para visualização em tabela e exportação de auditoria.
        """
        shift_filter_sql = "AND shift = ?" if shift_filter else ""
        params = [shift_filter] if shift_filter else []

        query = f"""
            SELECT 
                event_id,
                start_time,
                end_time,
                duration_min,
                category,
                sub_reason,
                sector,
                stop_type,
                shift
            FROM operational_events
            WHERE category != 'PRODUÇÃO REGULAR (RUN)'
            {shift_filter_sql}
            ORDER BY start_time DESC
        """
        return self._query_to_polars(query, params)