import pytest
import re
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from src.contracts import (
    VALID_SPECIALTIES,
    VALID_CLINIC_CODES,
    VALID_CITIES,
    VALID_INSURANCE,
    VALID_STATUSES,
    VALID_PAYMENT_METHODS,
    VALID_DURATIONS,
    VALID_CURRENCIES,
    PATIENTS_CONTRACT,
    APPOINTMENTS_CONTRACT,
    TARIFAS_CONTRACT
)


class TestContracts:
    """
    Pruebas de los contratos de datos
    """
    
    def test_patient_id_regex(self):
        """Verifica que patient_id cumple con el formato P + 6 digitos"""
        pattern = r"^P\d{6}$"
        
        valid_ids = ['P000001', 'P123456', 'P999999']
        invalid_ids = ['P00001', 'A000001', 'P000001a', 'P0000000']
        
        for pid in valid_ids:
            assert re.match(pattern, pid) is not None
        
        for pid in invalid_ids:
            assert re.match(pattern, pid) is None
    
    def test_appointment_id_regex(self):
        """Verifica que appointment_id cumple con el formato A + 7 digitos"""
        pattern = r"^A\d{7}$"
        
        valid_ids = ['A0000001', 'A1234567', 'A9999999']
        invalid_ids = ['A000001', 'B1234567', 'A0000001a', 'A00000001']
        
        for aid in valid_ids:
            assert re.match(pattern, aid) is not None
        
        for aid in invalid_ids:
            assert re.match(pattern, aid) is None
    
    def test_valid_specialties(self):
        """Verifica que las especialidades validas estan definidas con acentos"""
        # Usar las mismas especialidades que en contracts.py (con acentos)
        expected = [
            "Medicina General", "Pediatría", "Traumatología", "Cardiología",
            "Dermatología", "Ginecología", "Odontología", "Oftalmología"
        ]
        assert set(VALID_SPECIALTIES) == set(expected)
        assert len(VALID_SPECIALTIES) == 8
    
    def test_valid_clinic_codes(self):
        """Verifica que los codigos de clinica validos estan definidos"""
        expected = ["CL01", "CL02", "CL03", "CL04", "CL05"]
        assert set(VALID_CLINIC_CODES) == set(expected)
        assert len(VALID_CLINIC_CODES) == 5
    
    def test_patients_contract_structure(self):
        """Verifica la estructura del contrato de pacientes"""
        assert PATIENTS_CONTRACT.name == "patients"
        assert PATIENTS_CONTRACT.primary_key == ["patient_id"]
        assert len(PATIENTS_CONTRACT.columns) == 6
        
        column_names = [col.name for col in PATIENTS_CONTRACT.columns]
        expected = ['patient_id', 'birth_date', 'sex', 'city', 'insurance', 'registered_at']
        assert column_names == expected
    
    def test_appointments_contract_structure(self):
        """Verifica la estructura del contrato de citas"""
        assert APPOINTMENTS_CONTRACT.name == "appointments"
        assert APPOINTMENTS_CONTRACT.primary_key == ["appointment_id"]
        assert len(APPOINTMENTS_CONTRACT.columns) == 10
        
        column_names = [col.name for col in APPOINTMENTS_CONTRACT.columns]
        expected = [
            'appointment_id', 'patient_id', 'clinic_code', 'specialty',
            'scheduled_at', 'duration_min', 'status', 'amount_charged',
            'payment_method', 'created_at'
        ]
        assert column_names == expected
    
    def test_tarifas_contract_structure(self):
        """Verifica la estructura del contrato de tarifas"""
        assert TARIFAS_CONTRACT.name == "tarifas_especialidad"
        assert TARIFAS_CONTRACT.primary_key == ["clinic_code", "specialty"]
        assert len(TARIFAS_CONTRACT.columns) == 5
        
        column_names = [col.name for col in TARIFAS_CONTRACT.columns]
        expected = ['clinic_code', 'specialty', 'tarifa_base', 'moneda', 'vigencia_desde']
        assert column_names == expected
    
    def test_column_nullability(self):
        """Verifica que la nulabilidad de las columnas es correcta"""
        # Patients - todas no nulas
        for col in PATIENTS_CONTRACT.columns:
            assert col.nullable == False
        
        # Appointments - algunas nulas
        nullable_cols = ['specialty', 'amount_charged']
        for col in APPOINTMENTS_CONTRACT.columns:
            if col.name in nullable_cols:
                assert col.nullable == True
            else:
                assert col.nullable == False
        
        # Tarifas - todas no nulas
        for col in TARIFAS_CONTRACT.columns:
            assert col.nullable == False