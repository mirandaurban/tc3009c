import json
from pathlib import Path

# Mapea cada experimento a su archivo JSON
archivos = {
    1: "benchmark_result_50k.json",
    2: "benchmark_result_2m.json",
    3: "benchmark_result_5m.json",
    4: "benchmark_result_10m.json",
    5: "benchmark_result_20m.json",
    6: "benchmark_result_35m.json",
    7: "benchmark_result_50m.json",
}

# Texto fijo que no viene en el JSON 
cpu_estado = {
    1: ("Monohilo (~100%)", "Multihilo (Overhead)", ""),
    2: ("Monohilo (~100%)", "Multihilo (Parcial)", ""),
    3: ("Monohilo (~100%)", "Multihilo (Parcial)", ""),
    4: ("Monohilo (~100%)", "Multihilo (Cálculo)", ""),
    5: ("Monohilo (~100%)", "Multihilo (>300%)", ""),
    6: ("Monohilo (~100%)", "Multihilo (>400%)", ""),
    7: ("OOM / Saturación", "Spill to Disk", ""),
}

def fmt_num(n):
    return f"{n:,}"

def mem(v):
    return f"{v:.1f}" if v is not None else "-"

header = "| Exp | Modo / Motor | Filas (rows) | Tamaño CSV | Hora Inicio | Hora Fin | Duración Total (s) | Memoria Pico (MB) | Uso CPU Est. (%) | Ganador / Estado |"
sep    = "|---|---|---|---|---|---|---|---|---|---|"

filas = [header, sep]

for exp, path in archivos.items():
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = fmt_num(data["rows"])
    size = f"{data['csv_size_mb']:.1f} MB"
    p, s = data["pandas"], data["spark"]
    cpu_p, cpu_s, ganador = cpu_estado[exp]

    filas.append(
        f"| Exp {exp} | Pandas (Tradicional) | {rows} | {size} | {p['start_time']} | {p['end_time']} | {p['reported_total_s']} | {mem(p.get('peak_memory_mb'))} | {cpu_p} | {ganador} |"
    )
    filas.append(
        f"|  | PySpark (Distribuido) |  |  | {s['start_time']} | {s['end_time']} | {s['reported_total_s']} | {mem(s.get('peak_memory_mb'))} | {cpu_s} |  |"
    )

Path("resultados.md").write_text("\n".join(filas), encoding="utf-8")
print("\n".join(filas))