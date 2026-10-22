"""
Motor de Cálculo de OEE (Overall Equipment Effectiveness):
Processa eventos de telemetria industrial via DuckDB e Polars
para apurar Disponibilidade, Performance, Qualidade, Pareto, Linha do Tempo e Simulação What-If.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, Optional
import duckdb
import polars as pl


@dataclass(frozen=True)
class OEEMetrics:
    availability: float
    performance: float
    quality: float
    oee: float
    planned_time_sec: float
    operating_time_sec: float
    net_operating_time_sec: float
    valuable_operating_time_sec: float
    total_produced: int
    total_defective: int
    good_parts: int


@dataclass(frozen=True)
class WhatIfProjection:
    baseline_oee: float
    simulated_oee: float
    delta_oee_pct: float
    baseline_good_parts: int
    simulated_good_parts: int
    additional_good_parts: int
    saved_downtime_minutes: float


class OEEEngine:
    def __init__(self, db_path: str = "data/telemetry.duckdb"):
        self.db_path = db_path

    def _query_to_polars(self, query: str, params: list = None) -> pl.DataFrame:
        """Executa a consulta SQL no DuckDB e converte para Polars de forma robusta."""
        con = duckdb.connect(self.db_path, read_only=True)
        try:
            if params:
                for p in params:
                    query = query.replace("?", f"'{p}'", 1)
            return con.sql(query).pl()
        finally:
            con.close()

    def calculate_oee(self, shift_filter: Optional[str] = None) -> OEEMetrics:
        """Calcula os índices de OEE globais ou filtrados por turno específico."""
        query = "SELECT * FROM production_events"
        params = []
        if shift_filter:
            query += " WHERE shift = ?"
            params.append(shift_filter)

        df = self._query_to_polars(query, params)

        if df.is_empty():
            return OEEMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0)

        # 1. Disponibilidade
        total_planned_sec = df["duration_seconds"].sum()
        downtime_sec = df.filter(pl.col("status") == "STOP")["duration_seconds"].sum()
        operating_time_sec = total_planned_sec - downtime_sec

        availability = (
            (operating_time_sec / total_planned_sec)
            if total_planned_sec > 0
            else 0.0
        )

        # 2. Performance
        total_produced = int(df["parts_produced"].sum())
        ideal_cycle_sec = df["ideal_cycle_time_sec"][0]
        net_operating_time_sec = total_produced * ideal_cycle_sec

        performance = (
            (net_operating_time_sec / operating_time_sec)
            if operating_time_sec > 0
            else 0.0
        )
        performance = min(performance, 1.0)

        # 3. Qualidade
        total_defective = int(df["parts_defective"].sum())
        good_parts = total_produced - total_defective

        quality = (
            (good_parts / total_produced) if total_produced > 0 else 0.0
        )

        # 4. OEE Global e Tempo Operacional Efetivo
        oee = availability * performance * quality
        valuable_operating_time_sec = good_parts * ideal_cycle_sec

        return OEEMetrics(
            availability=round(availability, 4),
            performance=round(performance, 4),
            quality=round(quality, 4),
            oee=round(oee, 4),
            planned_time_sec=float(total_planned_sec),
            operating_time_sec=float(operating_time_sec),
            net_operating_time_sec=float(net_operating_time_sec),
            valuable_operating_time_sec=float(valuable_operating_time_sec),
            total_produced=total_produced,
            total_defective=total_defective,
            good_parts=good_parts,
        )

    def get_downtime_pareto(
        self, shift_filter: Optional[str] = None
    ) -> pl.DataFrame:
        """Retorna o ranking de paradas agregadas para geração de Diagrama de Pareto."""
        where_clause = "WHERE status = 'STOP'"
        params = []
        if shift_filter:
            where_clause += " AND shift = ?"
            params.append(shift_filter)

        query = f"""
            SELECT 
                stop_reason,
                SUM(duration_seconds) / 60.0 AS duration_minutes,
                COUNT(*) AS occurrences
            FROM production_events
            {where_clause}
            GROUP BY stop_reason
            ORDER BY duration_minutes DESC
        """

        df = self._query_to_polars(query, params)

        if df.is_empty():
            return df

        total_minutes = df["duration_minutes"].sum()
        return df.with_columns(
            (pl.col("duration_minutes") / total_minutes * 100.0).alias("pct_share"),
            (pl.col("duration_minutes").cum_sum() / total_minutes * 100.0).alias("cumulative_pct"),
        )

    def get_timeline_events(
        self, shift_filter: Optional[str] = None
    ) -> pl.DataFrame:
        """
        Retorna blocos contínuos consolidados de operação e paradas para o Gantt.
        Funde minutos consecutivos de mesmo estado para criar blocos sólidos legíveis.
        """
        where_clause = ""
        params = []
        if shift_filter:
            where_clause = "WHERE shift = ?"
            params.append(shift_filter)

        query = f"""
            SELECT 
                timestamp,
                shift,
                status,
                stop_reason,
                duration_seconds
            FROM production_events
            {where_clause}
            ORDER BY timestamp ASC
        """
        df = self._query_to_polars(query, params)

        if df.is_empty():
            return df

        records = df.to_dicts()
        merged_blocks = []
        
        current_block = None
        for row in records:
            cat = "PRODUÇÃO REGULAR (RUN)" if row["status"] == "RUN" else row["stop_reason"]
            start_t = row["timestamp"]
            dur = float(row["duration_seconds"])
            
            if current_block is None:
                current_block = {
                    "category": cat,
                    "status": row["status"],
                    "start_time": start_t,
                    "duration_sec": dur,
                }
            elif current_block["category"] == cat:
                current_block["duration_sec"] += dur
            else:
                current_block["end_time"] = current_block["start_time"] + timedelta(seconds=current_block["duration_sec"])
                merged_blocks.append(current_block)
                current_block = {
                    "category": cat,
                    "status": row["status"],
                    "start_time": start_t,
                    "duration_sec": dur,
                }

        if current_block is not None:
            current_block["end_time"] = current_block["start_time"] + timedelta(seconds=current_block["duration_sec"])
            merged_blocks.append(current_block)

        return pl.DataFrame(merged_blocks).with_columns(
            (pl.col("duration_sec") / 60.0).alias("duration_min")
        )

    def simulate_what_if(
        self,
        shift_filter: Optional[str],
        setup_reduction_pct: float,
        breakdown_reduction_pct: float,
        scrap_reduction_pct: float,
    ) -> WhatIfProjection:
        """
        Simulador de Sensibilidade Operacional (What-If):
        Aplica cenários de redução de perdas sobre a base real e calcula
        os novos indicadores de OEE e o ganho líquido de volume.
        """
        baseline = self.calculate_oee(shift_filter)
        if baseline.planned_time_sec == 0:
            return WhatIfProjection(0.0, 0.0, 0.0, 0, 0, 0, 0.0)

        # Consulta os tempos de parada por motivo para aplicar as reduções
        where_clause = "WHERE status = 'STOP'"
        params = []
        if shift_filter:
            where_clause += " AND shift = ?"
            params.append(shift_filter)

        query = f"""
            SELECT stop_reason, SUM(duration_seconds) as total_sec
            FROM production_events
            {where_clause}
            GROUP BY stop_reason
        """
        df_stops = self._query_to_polars(query, params)

        saved_sec = 0.0
        for row in df_stops.to_dicts():
            reason = row["stop_reason"]
            sec = float(row["total_sec"])
            if reason == "SETUP_AJUSTE":
                saved_sec += sec * (setup_reduction_pct / 100.0)
            elif reason == "FALHA_MECANICA":
                saved_sec += sec * (breakdown_reduction_pct / 100.0)

        # Recalcula Disponibilidade
        new_operating_sec = baseline.operating_time_sec + saved_sec
        new_avail = min(new_operating_sec / baseline.planned_time_sec, 1.0)

        # Recalcula Produção com o tempo ganho operando na taxa de performance atual
        ideal_cycle = 4.0
        extra_parts = int((saved_sec * baseline.performance) / ideal_cycle)
        new_total_produced = baseline.total_produced + extra_parts

        # Recalcula Refugos com a redução proposta
        simulated_scrap = baseline.total_defective * (1.0 - scrap_reduction_pct / 100.0)
        new_defective = int(simulated_scrap)
        new_good_parts = max(new_total_produced - new_defective, 0)

        # Recalcula Qualidade e Performance mantida
        new_quality = (new_good_parts / new_total_produced) if new_total_produced > 0 else 0.0
        new_perf = baseline.performance

        new_oee = new_avail * new_perf * new_quality
        delta_pct = (new_oee - baseline.oee) * 100.0

        return WhatIfProjection(
            baseline_oee=round(baseline.oee * 100.0, 1),
            simulated_oee=round(new_oee * 100.0, 1),
            delta_oee_pct=round(delta_pct, 1),
            baseline_good_parts=baseline.good_parts,
            simulated_good_parts=new_good_parts,
            additional_good_parts=new_good_parts - baseline.good_parts,
            saved_downtime_minutes=round(saved_sec / 60.0, 1),
        )