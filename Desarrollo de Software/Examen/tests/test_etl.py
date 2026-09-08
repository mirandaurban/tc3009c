import pytest
import pandas as pd
import sqlite3
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from src.etl import (
    load_config, extract, stage, validate, transform,
    deduplicar_citas, integrate, quality_gate, load,
    build_curated_database, homologar_specialty, homologar_clinic_code
)


class TestETL:
    """Pruebas del pipeline ETL"""

    def test_patient_age_at_visit(self, sample_config):
        """Prueba 1: patient_age_at_visit con entrada conocida"""
        config = load_config(sample_config)

        # Crear datos de prueba
        conn = sqlite3.connect(config.database_path)
        conn.execute("""
            INSERT INTO patients (patient_id, birth_date, sex, city, insurance, registered_at)
            VALUES ('P000001', '1990-01-15', 'F', 'Monterrey', 'basico', '2023-01-01')
        """)
        conn.execute("""
            INSERT INTO appointments (
                appointment_id, patient_id, clinic_code, specialty,
                scheduled_at, duration_min, status, amount_charged,
                payment_method, created_at
            ) VALUES (
                'A0000001', 'P000001', 'CL01', 'Medicina General',
                '2024-01-15 10:00:00', 30, 'completada', 500.0,
                'efectivo', '2024-01-10 08:00:00'
            )
        """)
        conn.commit()
        conn.close()

        watermark = "2024-01-01 00:00:00"
        patients_df, appointments_df, tarifas_df, catalogo = extract(config, watermark)

        batch_id = "test_batch"
        run_id = "test_run"
        patients_staged, appointments_staged, tarifas_staged = stage(
            patients_df, appointments_df, tarifas_df, batch_id, run_id
        )

        valid_patients, valid_appointments, valid_tarifas, quarantine = validate(
            patients_staged, appointments_staged, tarifas_staged, config
        )

        transformed_patients, transformed_appointments, transformed_tarifas = transform(
            valid_patients, valid_appointments, valid_tarifas, config
        )
        transformed_appointments = deduplicar_citas(transformed_appointments)

        fact_appointments, reconciliation = integrate(
            transformed_patients, transformed_appointments, transformed_tarifas, config
        )

        assert len(fact_appointments) == 1
        # 2024 - 1990 = 34
        assert fact_appointments.iloc[0]['patient_age_at_visit'] == 34

    def test_negative_amount_rejected(self, sample_config, sample_patients, sample_appointments):
        """Prueba 2: amount_charged negativo debe terminar en rechazo (D2)"""
        config = load_config(sample_config)

        patients = sample_patients.copy()
        appointments = sample_appointments.copy()
        appointments.loc[0, 'amount_charged'] = -100.0

        conn = sqlite3.connect(config.database_path)
        patients.to_sql('patients', conn, if_exists='replace', index=False)
        appointments.to_sql('appointments', conn, if_exists='replace', index=False)
        conn.close()

        watermark = "2024-01-01 00:00:00"
        patients_df, appointments_df, tarifas_df, catalogo = extract(config, watermark)

        batch_id = "test_batch"
        run_id = "test_run"
        patients_staged, appointments_staged, tarifas_staged = stage(
            patients_df, appointments_df, tarifas_df, batch_id, run_id
        )

        valid_patients, valid_appointments, valid_tarifas, quarantine = validate(
            patients_staged, appointments_staged, tarifas_staged, config
        )

        quarantine_appointments = quarantine[quarantine['source'] == 'appointments']
        assert len(quarantine_appointments) >= 1
        assert 'amount_charged_negative' in quarantine_appointments.iloc[0]['reject_reason']

    def test_quality_gate_threshold(self):
        """Prueba 3: quality gate se dispara con umbral bajo"""
        config = type('obj', (object,), {
            'completeness_min': 0.70,
            'duplicate_rate_max': 0.10,
            'null_foreign_key_max': 0.15,
            'invalid_amount_max': 0.05,
            'max_rule_violation_pct': 0.65
        })()

        reconciliation = {
            "rows_after": 100,
            "duplicated_appointment_id": 0,
            "unmatched_patient": 0,
            "unmatched_tarifa": 10,
            "no_show_count": 10
        }

        fact_df = pd.DataFrame()
        result = quality_gate(fact_df, reconciliation, config)

        assert result['status'] == 'FAIL'
        assert len(result['failures']) > 0
        assert any('unmatched_tarifa_rate' in f for f in result['failures'])

    def test_idempotency(self, sample_config):
        """Prueba 4: idempotencia - dos cargas seguidas = mismo conteo"""
        config = load_config(sample_config)
        build_curated_database(config)

        fact_data = pd.DataFrame({
            'appointment_id': ['A0000001', 'A0000002'],
            'patient_id': ['P000001', 'P000002'],
            'clinic_code': ['CL01', 'CL02'],
            'clinic_code_clean': ['CL01', 'CL02'],
            'specialty': ['Medicina General', 'Pediatria'],
            'specialty_clean': ['Medicina General', 'Pediatria'],
            'scheduled_at': ['2024-01-15 10:00:00', '2024-01-16 11:00:00'],
            'duration_min': [30, 30],
            'status': ['completada', 'completada'],
            'amount_charged': [500.0, 600.0],
            'amount_charged_clean': [500.0, 600.0],
            'payment_method': ['efectivo', 'tarjeta'],
            'created_at': ['2024-01-10 08:00:00', '2024-01-11 09:00:00'],
            'batch_id': ['test_batch', 'test_batch'],
            'source_system': ['test', 'test'],
            'ingested_at': ['2024-01-15 08:00:00', '2024-01-15 08:00:00'],
            'updated_at': ['2024-01-15 08:00:00', '2024-01-15 08:00:00']
        })

        quarantine_empty = pd.DataFrame()
        batch_id = "test_batch"

        inserted1, updated1 = load(config, fact_data, quarantine_empty, batch_id)
        inserted2, updated2 = load(config, fact_data, quarantine_empty, batch_id)

        assert inserted1 == 2
        assert updated1 == 0
        assert inserted2 == 0
        assert updated2 == 2

        conn = sqlite3.connect(config.output_database_path)
        count = conn.execute("SELECT COUNT(*) FROM fact_appointments").fetchone()[0]
        conn.close()
        assert count == 2

    def test_homologacion_specialty(self):
        """Prueba 5: homologacion de specialty (D5)"""
        alias_map = {
            "Medicina General": ["med gral", "MEDICINA_GENERAL", "medicina general", "MG", "med-general"],
            "Pediatria": ["pediatria", "PEDIATRIA", "PED", "ped"],
            "Traumatologia": ["traumatologia", "TRAUMA", "TRA", "trauma"]
        }

        test_cases = [
            ("MEDICINA_GENERAL", "Medicina General"),
            ("med gral", "Medicina General"),
            ("PEDIATRIA", "Pediatria"),
            ("ped", "Pediatria"),
            ("TRAUMA", "Traumatologia"),
            ("trauma", "Traumatologia"),
        ]

        for input_val, expected in test_cases:
            result = homologar_specialty(input_val, alias_map)
            assert result == expected, f"Fallo: {input_val} -> {result}, esperado {expected}"

    def test_homologacion_clinic_code(self):
        """Prueba 6: clinic_code sucio se normaliza (D6)"""
        catalogo = {
            "clinicas": [
                {
                    "clinic_code": "CL01",
                    "nombre": "SaludNorte Centro",
                    "ciudad": "Monterrey",
                    "zona": "norte",
                    "aliases": ["CL-01", "cl01", "Clinica Centro"]
                },
                {
                    "clinic_code": "CL03",
                    "nombre": "Centro Medico Central",
                    "ciudad": "CDMX",
                    "zona": "centro",
                    "aliases": ["CL-03", "cl03", "CMC"]
                }
            ]
        }

        test_cases = [
            (" 'CL01' ", "CL01"),
            ("'CL03'", "CL03"),
            ("cl01", "CL01"),
            ("CL-01", "CL01"),
            ("Clinica Centro", "CL01"),
        ]

        for input_val, expected in test_cases:
            result = homologar_clinic_code(input_val, catalogo)
            assert result == expected, f"Fallo: {input_val} -> {result}, esperado {expected}"

    def test_revenue_gap_calculation(self, sample_config):
        """Prueba 7: revenue_gap calculado contra la tarifa vigente correcta"""
        config = load_config(sample_config)

        patients = pd.DataFrame({
            'patient_id': ['P000001'],
            'birth_date': ['1990-01-15'],
            'sex': ['F'],
            'city': ['Monterrey'],
            'insurance': ['basico'],
            'registered_at': ['2023-01-01']
        })

        appointments = pd.DataFrame({
            'appointment_id': ['A0000001'],
            'patient_id': ['P000001'],
            'clinic_code': ['CL01'],
            'clinic_code_clean': ['CL01'],
            'specialty': ['Medicina General'],
            'specialty_clean': ['Medicina General'],
            'scheduled_at': ['2024-01-15 10:00:00'],
            'duration_min': [30],
            'status': ['completada'],
            'amount_charged': [500.0],
            'amount_charged_clean': [500.0],
            'payment_method': ['efectivo'],
            'created_at': ['2024-01-10 08:00:00'],
            'batch_id': ['test'],
            'source_system': ['test'],
            'ingested_at': ['2024-01-15 08:00:00'],
            'updated_at': ['2024-01-15 08:00:00'],
            'is_no_show': [0],
            'is_peak_hour': [0]
        })

        tarifas = pd.DataFrame({
            'clinic_code': ['CL01'],
            'specialty': ['Medicina General'],
            'tarifa_base': [500],
            'moneda': ['MXN'],
            'vigencia_desde': ['2024-01-01']
        })

        fact, reconciliation = integrate(patients, appointments, tarifas, config)

        assert len(fact) == 1
        assert fact.iloc[0]['tarifa_base'] == 500.0
        assert fact.iloc[0]['revenue_gap'] == 0.0