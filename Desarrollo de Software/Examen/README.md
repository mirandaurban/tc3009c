# Examen Parcial — De Laboratorio a Pipeline de Datos Productivo

**TC3009C.602 — Miranda Urban Solano A01752391**

---

## Caso del examen

**Red de clínicas "SaludNorte".** Operan 5 sucursales y 8 especialidades.
El área de operación necesita una tabla curada de citas médicas para medir
ingreso real por especialidad y sucursal, y la tasa de inasistencia
(_no-show_). Hoy no puede: la información de pacientes y citas vive en una base
operativa, las tarifas llegan en un CSV que mantiene Finanzas a mano, y el
catálogo de sucursales viene en un JSON con nombres escritos de varias formas.

Objetivo del pipeline: producir la tabla `appointments_curated`, más
`appointments_rejects` y `etl_runs`.

Copia ese párrafo en tu `README.md` y agrega **tu propia frase** de qué decisión
de negocio permite tomar la tabla curada.

---

# Sistema de Generación de Datos - Citas Médicas

## Descripción

Generador de datos sintéticos para un sistema de citas médicas.

## Requisitos

- Python 3.10+
- pip (gestor de paquetes)

## Instalación

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd Examen

# 2. Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
```
