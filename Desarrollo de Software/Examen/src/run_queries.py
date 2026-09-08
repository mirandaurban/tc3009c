"""
Ejecuta las consultas analíticas sobre la base de datos curada.
Guarda resultados en JSON y Markdown, además de imprimir en terminal.
"""

import json
import sqlite3
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
SQL_DIR = PROJECT_ROOT / "sql"
OUTPUT_DIR = PROJECT_ROOT / "docs"

SQL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class QueryRunner:
    """
    Ejecuta consultas SQL y formatea resultados
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.results = {}
        
        if not db_path.exists():
            print(f"ERROR: Base de datos no encontrada: {db_path}")
            sys.exit(1)
    
    def extract_queries(self, sql_content: str) -> Dict[str, str]:
        """
        Extrae las consultas del archivo SQL usando el formato numerado
        """
        
        queries = {}
        
        lines = sql_content.split('\n')
        
        current_query = []
        in_query = False
        current_num = 0
        query_started = False
        
        for i, line in enumerate(lines):
            # Detectar inicio de consulta numerada
            match = re.match(r'^--\s*(\d+)\.', line)
            if match:
                if in_query and current_query:
                    query_text = '\n'.join(current_query).strip()
                    if query_text:
                        name = f"{current_num}_{self._get_query_name(current_num)}"
                        queries[name] = query_text
                        print(f"  Guardada consulta {current_num}: {len(query_text)} caracteres")
                
                # Iniciar nueva consulta
                current_num = int(match.group(1))
                current_query = []
                in_query = True
                query_started = False
                continue
            
            # Si estamos dentro de una consulta
            if in_query:
                if re.match(r'^--\s*\d+\.', line):
                    continue
                
                if line.strip() == '' and query_started:
                    if i + 1 < len(lines) and (lines[i+1].strip() == '' or lines[i+1].strip().startswith('--')):
                        continue
                
                # Si la línea contiene SQL (SELECT, WITH, etc.) o es parte de la consulta
                if line.strip().upper().startswith(('SELECT', 'WITH', 'FROM', 'WHERE', 
                                                    'GROUP', 'ORDER', 'HAVING', 'LIMIT',
                                                    'UNION', 'JOIN', 'LEFT', 'RIGHT',
                                                    'INNER', 'CROSS', 'COUNT', 'SUM',
                                                    'AVG', 'ROUND', 'CAST', 'CASE',
                                                    'WHEN', 'THEN', 'ELSE', 'END')):
                    query_started = True
                
                # Agregar línea a la consulta actual (excepto comentarios de interpretación)
                if query_started:
                    # Si es un comentario que no es SQL, saltarlo
                    if line.strip().startswith('--') and not re.match(r'^--\s*\d+\.', line):
                        if not any(keyword in line.upper() for keyword in ['SELECT', 'WITH', 'FROM', 'WHERE']):
                            continue
                    current_query.append(line)
                elif line.strip() and not line.strip().startswith('--'):
                    # Si no es comentario y no es SQL, podría ser parte de la consulta
                    query_started = True
                    current_query.append(line)
        
        # Guardar la última consulta
        if in_query and current_query:
            query_text = '\n'.join(current_query).strip()
            if query_text:
                name = f"{current_num}_{self._get_query_name(current_num)}"
                queries[name] = query_text
                print(f"  Guardada consulta {current_num}: {len(query_text)} caracteres")
        
        return queries
    
    def _get_query_name(self, num: int) -> str:
        """
        Obtiene el nombre de la consulta según su número
        """
        names = {
            1: "ingreso_ticket_por_especialidad",
            2: "no_show_por_sucursal",
            3: "ingreso_mensual_variacion",
            4: "top_10_pacientes",
            5: "distribucion_rechazos"
        }
        return names.get(num, f"consulta_{num}")
    
    def clean_query(self, query: str) -> str:
        """
        Limpia la consulta eliminando comentarios no SQL
        """
        lines = query.split('\n')
        clean_lines = []
        for line in lines:
            # Si es un comentario que no contiene SQL, saltarlo
            if line.strip().startswith('--'):
                if not any(keyword in line.upper() for keyword in ['SELECT', 'WITH', 'FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'LIMIT']):
                    continue
            clean_lines.append(line)
        return '\n'.join(clean_lines).strip()
    
    def run_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta SQL y retorna resultados como lista de diccionarios
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            return result
        except sqlite3.OperationalError as e:
            print(f"    Error ejecutando consulta: {e}")
            print(f"    Query: {query[:200]}...")
            return []
        finally:
            conn.close()
    
    def execute_all(self):
        """
        Ejecuta todas las consultas del archivo consultas.sql
        """
        
        queries_file = SQL_DIR / "consultas.sql"
        
        if not queries_file.exists():
            print(f"ERROR: No se encuentra {queries_file}")
            sys.exit(1)
        
        print("\nLeyendo archivo SQL...")
        with open(queries_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        print(f"Archivo leído: {len(content)} caracteres")
        
        print("\nExtrayendo consultas...")
        queries = self.extract_queries(content)
        
        if not queries:
            print("ERROR: No se extrajo ninguna consulta")
            print("Verifica que el archivo SQL tenga el formato: -- 1. ...")
            return
        
        # Ejecutar cada consulta
        print(f"\nEjecutando {len(queries)} consultas...")
        for name, query in queries.items():
            print(f"\n--- {name} ---")
            
            clean = self.clean_query(query)
            
            if not clean:
                print("  (consulta vacía)")
                continue
            
            print(f"  Query: {clean[:100]}...")
            
            result = self.run_query(clean)
            self.results[name] = {
                "query": clean,
                "results": result,
                "row_count": len(result)
            }
            
            print(f"  Filas: {len(result)}")
            
            if result:
                self.print_results(name, result)
            else:
                print("  (sin resultados)")
    
    def print_results(self, name: str, results: List[Dict[str, Any]]):
        """
        Imprime resultados en terminal
        """
        
        if not results:
            return
        
        columns = list(results[0].keys())
        
        col_widths = {}
        for col in columns:
            max_len = len(str(col))
            for row in results[:10]:
                val = row.get(col)
                if val is not None:
                    max_len = max(max_len, len(str(val)))
            col_widths[col] = min(max_len + 2, 40)
        
        header = " | ".join([f"{col:>{col_widths[col]}}" for col in columns])
        print(f"  {header}")
        print(f"  {'-' * len(header)}")
        
        for row in results[:10]:
            row_str = " | ".join([
                str(row.get(col, ""))[:col_widths[col]-1].rjust(col_widths[col])
                for col in columns
            ])
            print(f"  {row_str}")
        
        if len(results) > 10:
            print(f"  ... y {len(results) - 10} filas mas")
    
    def save_markdown(self, output_path: Path = None):
        
        if output_path is None:
            output_path = OUTPUT_DIR / "resultados_consultas.md"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Resultados de Consultas Analiticas\n\n")
            f.write(f"Fecha de ejecucion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Base de datos: {self.db_path}\n\n")
            
            for name, data in self.results.items():
                results = data["results"]
                
                display_name = self._format_name(name)
                f.write(f"## {display_name}\n\n")
                
                if not results:
                    f.write("(Sin resultados)\n\n")
                    continue
                
                # Crear tabla Markdown
                columns = list(results[0].keys())
                
                f.write("| " + " | ".join(columns) + " |\n")
                f.write("| " + " | ".join(["---"] * len(columns)) + " |\n")
                
                for row in results:
                    row_str = " | ".join([
                        str(row.get(col, "")).replace("|", "\\|")
                        for col in columns
                    ])
                    f.write(f"| {row_str} |\n")
                
                f.write(f"\n*Total: {len(results)} filas*\n\n")
                f.write("---\n\n")
        
        print(f"\nResultados guardados en Markdown: {output_path}")
        return output_path
    
    def save_json(self, output_path: Path = None):        
        if output_path is None:
            output_path = OUTPUT_DIR / "resultados_consultas.json"
        
        json_data = {
            "timestamp": datetime.now().isoformat(),
            "database": str(self.db_path),
            "queries": {}
        }
        
        for name, data in self.results.items():
            rows = []
            for row in data["results"]:
                clean_row = {}
                for key, value in row.items():
                    if isinstance(value, (int, float, str, bool, type(None))):
                        clean_row[key] = value
                    else:
                        clean_row[key] = str(value)
                rows.append(clean_row)
            
            json_data["queries"][name] = {
                "row_count": len(rows),
                "rows": rows
            }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"Resultados guardados en JSON: {output_path}")
        return output_path
    
    def _format_name(self, name: str) -> str:
        """
        Formatea el nombre de la consulta para legibilidad
        """
        mapping = {
            "1_ingreso_ticket_por_especialidad": "Consulta 1: Ingreso y ticket por especialidad",
            "2_no_show_por_sucursal": "Consulta 2: Tasa de no-show por sucursal",
            "3_ingreso_mensual_variacion": "Consulta 3: Ingreso mensual y variacion",
            "4_top_10_pacientes": "Consulta 4: Top 10 pacientes",
            "5_distribucion_rechazos": "Consulta 5: Distribucion de rechazos"
        }
        return mapping.get(name, name)


def main():
    """Funcion principal"""

    
    # Buscar base de datos curada
    db_path = DATA_DIR / "clinica_curated.db"
    
    if not db_path.exists():
        print(f"ERROR: No se encontro base de datos curada en: {db_path}")
        sys.exit(1)
    
    print(f"\nBase de datos: {db_path}")
    print(f"Tamaño: {db_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Ejecutar consultas
    runner = QueryRunner(db_path)
    runner.execute_all()
    
    if runner.results:
        runner.save_markdown()
        runner.save_json()
    else:
        print("No hay resultados para guardar")


if __name__ == "__main__":
    main()