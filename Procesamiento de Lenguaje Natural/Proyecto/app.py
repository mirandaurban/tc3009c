"""Entrada de la aplicación integrada; reutiliza la interfaz del laboratorio 10."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).parent/'labs/10_chatpnl_starter/app.py'),run_name="__main__")
