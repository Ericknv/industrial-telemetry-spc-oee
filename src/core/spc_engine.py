"""
Motor de Cálculo de CEP (Controle Estatístico de Processo):
Calcula médias e amplitudes por subgrupo, limites de controle (X-barra e R),
executa o rastreio das Regras de Nelson, calcula os índices Cp e Cpk e gera relatórios consolidados.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import duckdb
import numpy as np
import polars as pl


# Constantes estatísticas tabeladas para n = 2 até 10
SPC_CONSTANTS = {
    2: {"A2": 1.880, "D3": 0.000, "D4": 3.267, "d2": 1.128},
    3: {"A2": 1.023, "D3": 0.000, "D4": 2.574, "d2": 1.693},
    4: {"A2": 0.729, "D3": 0.000, "D4": 2.282, "d2": 2.059},
    5: {"A2": 0.577, "D3": 0.000, "D4": 2.114, "d2": 2.326},
    6: {"A2": 0.483, "D3": 0.000, "D4": 2.004, "d2": 2.534},
    7: {"A2": 0.419, "D3": 0.076, "D4": 1.924, "d2": 2.704},
    8: {"A2": 0.373, "D3": 0.136, "D4": 1.864, "d2": 2.847},
    9: {"A2": 0.337, "D3": 0.184, "D4": 1.816, "d2": 2.970},
    10: {"A2": 0.308, "D3": 0.223, "D4": 1.777, "d2": 3.078},
}


@dataclass(frozen=True)
class SPCLimits:
    x_cl: float
    x_ucl: float
    x_lcl: float
    r_cl: float
    r_ucl: float
    r_lcl: float
    sigma_est: float
    cp: float
    cpk: float


class SPCEngine:
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

    def get_subgroup_summary(self) -> pl.DataFrame:
        """Agrupa medições por subgrupo calculando média, amplitude e limites de projeto."""
        query = """
            SELECT 
                subgroup_id,
                COUNT(*) as n_size,
                AVG(measured_value_mm) as x_bar,
                MAX(measured_value_mm) - MIN(measured_value_mm) as r_range,
                MIN(lsl) as lsl,
                MIN(usl) as usl,
                MIN(nominal_target) as target
            FROM dimensional_inspections
            GROUP BY subgroup_id
            ORDER BY subgroup_id ASC
        """
        return self._query_to_polars(query)

    def calculate_limits_and_capability(self, df_subgroups: pl.DataFrame) -> SPCLimits:
        """Calcula os limites das cartas e os indicadores de capabilidade Cp e Cpk."""
        if df_subgroups.is_empty():
            return SPCLimits(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        n = int(df_subgroups["n_size"][0])
        constants = SPC_CONSTANTS.get(n, SPC_CONSTANTS[5])

        x_double_bar = float(df_subgroups["x_bar"].mean())
        r_bar = float(df_subgroups["r_range"].mean())

        # Limites da Carta X-barra
        x_ucl = x_double_bar + constants["A2"] * r_bar
        x_lcl = x_double_bar - constants["A2"] * r_bar

        # Limites da Carta R
        r_ucl = constants["D4"] * r_bar
        r_lcl = constants["D3"] * r_bar

        # Estimativa de sigma e Capabilidade
        sigma_est = r_bar / constants["d2"] if constants["d2"] > 0 else 0.0
        usl = float(df_subgroups["usl"][0])
        lsl = float(df_subgroups["lsl"][0])

        if sigma_est > 0:
            cp = (usl - lsl) / (6 * sigma_est)
            cpu = (usl - x_double_bar) / (3 * sigma_est)
            cpl = (x_double_bar - lsl) / (3 * sigma_est)
            cpk = min(cpu, cpl)
        else:
            cp = 0.0
            cpk = 0.0

        return SPCLimits(
            x_cl=round(x_double_bar, 4),
            x_ucl=round(x_ucl, 4),
            x_lcl=round(x_lcl, 4),
            r_cl=round(r_bar, 4),
            r_ucl=round(r_ucl, 4),
            r_lcl=round(r_lcl, 4),
            sigma_est=round(sigma_est, 5),
            cp=round(cp, 2),
            cpk=round(cpk, 2),
        )

    @staticmethod
    def evaluate_nelson_rules(
        means: List[float], cl: float, ucl: float, lcl: float
    ) -> Dict[int, List[int]]:
        """
        Avalia as 4 primeiras regras de Nelson sobre as médias dos subgrupos:
        - Regra 1: Ponto além de 3 sigmas.
        - Regra 2: 9 pontos seguidos do mesmo lado da linha central.
        - Regra 3: 6 pontos seguidos sempre a subir ou sempre a descer.
        - Regra 4: 14 pontos alternados para cima e para baixo.
        """
        violations: Dict[int, List[int]] = {1: [], 2: [], 3: [], 4: []}
        k = len(means)

        for i, val in enumerate(means):
            if val > ucl or val < lcl:
                violations[1].append(i)

        for i in range(k - 8):
            window = means[i : i + 9]
            if all(v > cl for v in window) or all(v < cl for v in window):
                violations[2].extend(range(i, i + 9))

        for i in range(k - 5):
            window = means[i : i + 6]
            increasing = all(window[j] < window[j + 1] for j in range(5))
            decreasing = all(window[j] > window[j + 1] for j in range(5))
            if increasing or decreasing:
                violations[3].extend(range(i, i + 6))

        for i in range(k - 13):
            window = means[i : i + 14]
            diffs = [window[j + 1] - window[j] for j in range(13)]
            alternating = all(diffs[j] * diffs[j + 1] < 0 for j in range(12))
            if alternating:
                violations[4].extend(range(i, i + 14))

        for rule in violations:
            violations[rule] = sorted(list(set(violations[rule])))

        return violations

    def get_raw_inspections(self) -> pl.DataFrame:
        """Retorna todas as medições individuais para análise de distribuição e histograma."""
        query = """
            SELECT 
                sample_id,
                subgroup_id,
                measured_value_mm,
                lsl,
                usl,
                nominal_target
            FROM dimensional_inspections
            ORDER BY sample_id ASC
        """
        return self._query_to_polars(query)

    def get_exportable_spc_report(self) -> pl.DataFrame:
        """Gera DataFrame tabular pronto para exportação com status estatístico por subgrupo."""
        df_subgroups = self.get_subgroup_summary()
        if df_subgroups.is_empty():
            return df_subgroups

        limits = self.calculate_limits_and_capability(df_subgroups)
        violations = self.evaluate_nelson_rules(
            df_subgroups["x_bar"].to_list(),
            limits.x_cl,
            limits.x_ucl,
            limits.x_lcl,
        )

        anomalous_indices = set()
        for rule, idxs in violations.items():
            anomalous_indices.update(idxs)

        status_col = [
            "VIOLAÇÃO_REGRA_NELSON" if i in anomalous_indices else "SOB_CONTROLE"
            for i in range(len(df_subgroups))
        ]

        return df_subgroups.with_columns(
            pl.lit(limits.x_cl).alias("x_double_bar"),
            pl.lit(limits.x_ucl).alias("ucl_xbar"),
            pl.lit(limits.x_lcl).alias("lcl_xbar"),
            pl.lit(limits.r_cl).alias("r_bar"),
            pl.lit(limits.r_ucl).alias("ucl_r"),
            pl.lit(limits.r_lcl).alias("lcl_r"),
            pl.lit(limits.cp).alias("indice_cp"),
            pl.lit(limits.cpk).alias("indice_cpk"),
            pl.Series("status_processo", status_col),
        )