"""Portal de ejecucion para los 3 ejemplos ETL de la Clase 5.

Sirve una pagina con las 3 tarjetas (una por ejemplo), cada una con su
propio diagrama de pipeline. Al presionar "Ejecutar" corre el
`run_etl.sh` del ejemplo como subproceso y transmite su salida linea por
linea al navegador via Server-Sent Events, para que el diagrama se vaya
iluminando etapa por etapa conforme el log real las va mencionando.

No transforma ni interpreta los datos: solo orquesta y muestra lo que los
scripts de cada ejemplo ya hacen.
"""

import os
import subprocess
from pathlib import Path

from flask import Flask, Response, jsonify, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
CLASE_DIR = BASE_DIR.parent

EXAMPLES = {
    "basico": {
        "title": "Ejemplo 1 — ETL básico",
        "folder": "ejemplo_1_etl_basico",
        "script": "run_etl.sh",
        "pattern": "ETL",
        "tech": "Python + pandas, un solo script",
        "description": (
            "Extract -> Transform -> Load en un solo paso. Sin staging, sin "
            "contrato de datos, sin cuarentena, sin auditoria. Es el punto de "
            "partida ingenuo para contrastar con los otros dos ejemplos."
        ),
        "stages": ["EXTRACT", "TRANSFORM", "LOAD"],
    },
    "completo": {
        "title": "Ejemplo 2 — ETL completo",
        "folder": "ejemplo_2_etl_completo",
        "script": "run_etl.sh",
        "pattern": "ETL",
        "tech": "Python + pandas + SQLite, UPSERT transaccional",
        "description": (
            "El proceso completo de la clase: extraccion incremental por "
            "watermark, staging con batch_id, cuarentena, integracion con "
            "reconciliation, quality gate, carga idempotente y auditoria."
        ),
        "stages": [
            "DEFINE", "EXTRACT", "STAGE", "VALIDATE", "TRANSFORM",
            "INTEGRATE", "QUALITY GATE", "LOAD", "AUDIT",
        ],
    },
    "duckdb": {
        "title": "Ejemplo 3 — ETL con DuckDB (dataset real)",
        "folder": "ejemplo_3_etl_duckdb",
        "script": "run_etl.sh",
        "pattern": "ELT",
        "tech": "DuckDB + SQL, patron ELT",
        "description": (
            "Telco Customer Churn (IBM), dataset real con datos sucios "
            "autenticos: TotalCharges llega en blanco para clientes nuevos y "
            "varias columnas traen comillas simples literales embebidas en "
            "el texto."
        ),
        "stages": [
            "EXTRACT/STAGE", "VALIDATE", "TRANSFORM",
            "INTEGRATE", "QUALITY GATE", "LOAD", "AUDIT",
        ],
    },
}

app = Flask(__name__, static_folder="static", static_url_path="")


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/examples")
def api_examples():
    return jsonify(EXAMPLES)


@app.get("/run/<example_id>")
def run_example(example_id):
    example = EXAMPLES.get(example_id)
    if example is None:
        return jsonify({"error": "ejemplo desconocido"}), 404

    example_dir = CLASE_DIR / example["folder"]

    def stream():
        env = {**os.environ, "PYTHONUNBUFFERED": "1"}
        process = subprocess.Popen(
            ["bash", example["script"]],
            cwd=example_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        for line in process.stdout:
            yield f"data: {line.rstrip()}\n\n"
        process.wait()
        status = "ok" if process.returncode == 0 else "error"
        yield f"event: done\ndata: {status}\n\n"

    return Response(stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, threaded=True)
