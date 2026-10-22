"""
Módulo de Simulação e Ingestão de Telemetria Industrial:
Gera dados operacionais de chão de fábrica para 24 horas contínuas,
incluindo eventos de paragem enriquecidos com setores fabris,
classificação TPM (Planejada vs Não-Planejada) e medições dimensionais para CEP.
"""

from datetime import datetime, timedelta
import os
import random
import duckdb
import numpy as np


class FactorySimulator:
    def __init__(self, db_path: str = "data/telemetry.duckdb"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def init_database(self):
        """Recria o esquema de tabelas relacionais analíticas no DuckDB com schema limpo."""
        con = duckdb.connect(self.db_path)
        try:
            # Elimina tabelas antigas para evitar divergência de colunas (BinderException)
            con.execute("DROP TABLE IF EXISTS operational_events")
            con.execute("DROP TABLE IF EXISTS dimensional_inspections")

            # Tabela de eventos da linha de produção (Gantt, OEE e Downtime granular)
            con.execute(
                """
                CREATE TABLE operational_events (
                    event_id INTEGER PRIMARY KEY,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_sec FLOAT,
                    duration_min FLOAT,
                    category VARCHAR,
                    sub_reason VARCHAR,
                    sector VARCHAR,
                    stop_type VARCHAR,
                    asset_id VARCHAR,
                    shift VARCHAR,
                    pieces_produced INTEGER,
                    pieces_defective INTEGER
                )
                """
            )

            # Tabela de inspeções dimensionais para CEP
            con.execute(
                """
                CREATE TABLE dimensional_inspections (
                    sample_id INTEGER PRIMARY KEY,
                    subgroup_id INTEGER,
                    timestamp TIMESTAMP,
                    measured_value_mm FLOAT,
                    nominal_target FLOAT,
                    lsl FLOAT,
                    usl FLOAT
                )
                """
            )
            con.commit()
        finally:
            con.close()

    def generate_24h_telemetry(self):
        """Simula 24 horas ininterruptas de operação em 3 turnos estruturados."""
        con = duckdb.connect(self.db_path)
        try:
            base_time = datetime(2026, 10, 20, 6, 0, 0)
            current_time = base_time
            end_time = base_time + timedelta(hours=24)

            event_id = 1
            sample_id = 1
            subgroup_id = 1

            downtime_catalog = [
                {
                    "category": "SETUP_AJUSTE",
                    "sub_reason": "Troca de Molde e Matriz",
                    "sector": "Engenharia de Processo",
                    "stop_type": "PLANEJADA",
                    "min_sec": 900,
                    "max_sec": 2400,
                },
                {
                    "category": "FALHA_MECANICA",
                    "sub_reason": "Travamento de Atuador Hidráulico",
                    "sector": "Manutenção Mecânica",
                    "stop_type": "NÃO_PLANEJADA",
                    "min_sec": 600,
                    "max_sec": 1800,
                },
                {
                    "category": "MICROPARADA_SENSOR",
                    "sub_reason": "Falha de Óptica no Sensor Fotoelétrico",
                    "sector": "Automação & Elétrica",
                    "stop_type": "NÃO_PLANEJADA",
                    "min_sec": 60,
                    "max_sec": 300,
                },
                {
                    "category": "FALTA_MATERIAL",
                    "sub_reason": "Atraso no Abastecimento por AGV",
                    "sector": "Logística & Suprimentos",
                    "stop_type": "NÃO_PLANEJADA",
                    "min_sec": 300,
                    "max_sec": 1200,
                },
                {
                    "category": "INSPECAO_QUALIDADE",
                    "sub_reason": "Amostragem Bloqueada para Liberação de Lote",
                    "sector": "Garantia da Qualidade",
                    "stop_type": "PLANEJADA",
                    "min_sec": 300,
                    "max_sec": 900,
                },
            ]

            nominal_target = 25.000
            lsl = 24.850
            usl = 25.150

            current_subgroup_samples = []

            while current_time < end_time:
                hour = current_time.hour
                if 6 <= hour < 14:
                    shift = "Turno 1 (Manhã)"
                elif 14 <= hour < 22:
                    shift = "Turno 2 (Tarde)"
                else:
                    shift = "Turno 3 (Noite)"

                is_running = random.random() < 0.78

                if is_running:
                    run_duration_sec = random.randint(900, 2700)
                    if current_time + timedelta(seconds=run_duration_sec) > end_time:
                        run_duration_sec = int((end_time - current_time).total_seconds())

                    event_end = current_time + timedelta(seconds=run_duration_sec)
                    cycle_time = 4.0

                    total_pieces = int(run_duration_sec / cycle_time * random.uniform(0.92, 0.99))
                    defective_pieces = int(total_pieces * random.uniform(0.01, 0.03))

                    con.execute(
                        """
                        INSERT INTO operational_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event_id,
                            current_time,
                            event_end,
                            float(run_duration_sec),
                            round(run_duration_sec / 60.0, 2),
                            "PRODUÇÃO REGULAR (RUN)",
                            "Regime Estável",
                            "Operação Fabril",
                            "OPERACIONAL",
                            "LINHA-MONT-01",
                            shift,
                            total_pieces,
                            defective_pieces,
                        ),
                    )
                    event_id += 1

                    num_inspections = max(5, int(run_duration_sec / 300))
                    for _ in range(num_inspections):
                        val = float(np.random.normal(loc=nominal_target, scale=0.035))
                        current_subgroup_samples.append(val)

                        con.execute(
                            """
                            INSERT INTO dimensional_inspections VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                sample_id,
                                subgroup_id,
                                current_time,
                                round(val, 4),
                                nominal_target,
                                lsl,
                                usl,
                            ),
                        )
                        sample_id += 1

                        if len(current_subgroup_samples) >= 5:
                            subgroup_id += 1
                            current_subgroup_samples = []

                    current_time = event_end

                else:
                    dt_choice = random.choice(downtime_catalog)
                    stop_duration_sec = random.randint(dt_choice["min_sec"], dt_choice["max_sec"])

                    if current_time + timedelta(seconds=stop_duration_sec) > end_time:
                        stop_duration_sec = int((end_time - current_time).total_seconds())

                    event_end = current_time + timedelta(seconds=stop_duration_sec)

                    con.execute(
                        """
                        INSERT INTO operational_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event_id,
                            current_time,
                            event_end,
                            float(stop_duration_sec),
                            round(stop_duration_sec / 60.0, 2),
                            dt_choice["category"],
                            dt_choice["sub_reason"],
                            dt_choice["sector"],
                            dt_choice["stop_type"],
                            "LINHA-MONT-01",
                            shift,
                            0,
                            0,
                        ),
                    )
                    event_id += 1
                    current_time = event_end

            con.commit()
        finally:
            con.close()


if __name__ == "__main__":
    sim = FactorySimulator()
    sim.init_database()
    sim.generate_24h_telemetry()
    print("Base industrial gerada com sucesso e enriquecida com atributos de Downtime/TPM.")