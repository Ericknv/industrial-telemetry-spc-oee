"""
Módulo de Simulação Industrial:
Gera telemetria de linha de montagem (OEE) e medições metrológicas (CEP)
com injeção controlada de desvios e causas especiais de variação.
"""

from datetime import datetime, timedelta
import duckdb
import numpy as np
import polars as pl


def generate_production_data(
    start_time: datetime, total_hours: int = 24, nominal_cycle_time: float = 12.0
) -> pl.DataFrame:
    """Gera registos de eventos operacionais da linha para cálculo de OEE."""
    np.random.seed(42)

    records = []
    current_time = start_time
    end_time = start_time + timedelta(hours=total_hours)

    stop_reasons = [
        "NENHUMA",
        "SETUP_AJUSTE",
        "FALHA_MECANICA",
        "FALTA_MATERIAL",
        "MICROPARADA_SENSOR",
    ]

    while current_time < end_time:
        hour = current_time.hour
        if 6 <= hour < 14:
            shift = "Turno 1 (Manhã)"
        elif 14 <= hour < 22:
            shift = "Turno 2 (Tarde)"
        else:
            shift = "Turno 3 (Noite)"

        # 85% do tempo de operação em regime normal
        is_running = np.random.rand() > 0.15

        if is_running:
            status = "RUN"
            reason = "NENHUMA"
            duration_sec = 60.0  # bloco de amostragem de 1 minuto
            actual_cycle = float(
                np.clip(np.random.normal(nominal_cycle_time, 0.8), 10.0, 20.0)
            )
            produced = int(duration_sec // actual_cycle)
            defective = int(np.random.binomial(produced, 0.02))
        else:
            status = "STOP"
            duration_sec = 60.0
            actual_cycle = 0.0
            produced = 0
            defective = 0
            reason = np.random.choice(
                stop_reasons[1:], p=[0.35, 0.25, 0.15, 0.25]
            )

        records.append(
            {
                "timestamp": current_time,
                "line_id": "LINHA_01",
                "shift": shift,
                "status": status,
                "stop_reason": reason,
                "ideal_cycle_time_sec": nominal_cycle_time,
                "actual_cycle_time_sec": actual_cycle,
                "duration_seconds": duration_sec,
                "parts_produced": produced,
                "parts_defective": defective,
            }
        )

        current_time += timedelta(seconds=duration_sec)

    return pl.DataFrame(records)


def generate_spc_inspection_data(
    start_time: datetime, num_subgroups: int = 30, sample_size: int = 5
) -> pl.DataFrame:
    """
    Gera medições de cotas críticas agrupadas em subgrupos racionais (n=5).
    Injeta instabilidade estatística a partir do subgrupo 19.
    """
    np.random.seed(101)

    records = []
    current_time = start_time
    sample_counter = 1

    target_nominal = 25.000
    usl = 25.060
    lsl = 24.940

    for subgroup_id in range(1, num_subgroups + 1):
        if subgroup_id <= 18:
            # Fase 1: Processo centrado e estável
            mean = target_nominal
            sigma = 0.015
        elif 19 <= subgroup_id <= 24:
            # Fase 2: Tendência de subida (desgaste de ferramenta)
            mean = target_nominal + (subgroup_id - 18) * 0.008
            sigma = 0.015
        else:
            # Fase 3: Dispersão ampliada (folga mecânica)
            mean = target_nominal
            sigma = 0.038

        measurements = np.random.normal(mean, sigma, sample_size)

        for val in measurements:
            records.append(
                {
                    "timestamp": current_time,
                    "sample_id": sample_counter,
                    "subgroup_id": subgroup_id,
                    "subgroup_size": sample_size,
                    "feature_name": "diametro_eixo_principal",
                    "measured_value_mm": round(float(val), 4),
                    "nominal_target": target_nominal,
                    "lsl": lsl,
                    "usl": usl,
                }
            )
            sample_counter += 1

        current_time += timedelta(minutes=30)

    return pl.DataFrame(records)


def init_database(db_path: str = "data/telemetry.duckdb"):
    """Gera os conjuntos de dados e persiste as tabelas no DuckDB."""
    print("A gerar dados de manufatura...")
    base_time = datetime(2026, 10, 20, 6, 0, 0)

    df_production = generate_production_data(
        base_time, total_hours=24, nominal_cycle_time=12.0
    )
    df_spc = generate_spc_inspection_data(
        base_time, num_subgroups=30, sample_size=5
    )

    con = duckdb.connect(db_path)
    con.execute(
        "CREATE OR REPLACE TABLE production_events AS SELECT * FROM df_production"
    )
    con.execute(
        "CREATE OR REPLACE TABLE dimensional_inspections AS SELECT * FROM df_spc"
    )
    con.close()

    print(f"Base de dados DuckDB criada com sucesso em: {db_path}")


if __name__ == "__main__":
    init_database()