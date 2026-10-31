# ChatPNL · laboratorios de Streamlit
Material de Felipe Castillo Rendón para Procesamiento de Lenguaje Natural. Ruta práctica complementaria. Python 3.11, CPU, sin APIs comerciales. Trabajo en parejas con defensa individual. Los diez laboratorios formativos Streamlit son distintos de los laboratorios oficiales de `evaluaciones/`.

La ruta se cubre en **cinco semanas de contenido**, con revisión, entrega y defensa en la sexta. Consulta [CALENDARIO.md](docs/CALENDARIO.md) para ver los bloques semanales, el núcleo de cada práctica y la pausa de Semana Tec.

## Ejecutar la aplicación integrada

La aplicación reúne registro e inicio de sesión, chat con fuentes e historial privado en MySQL. Usa MAMP en macOS y Windows, o LAMP en Linux. Los diez laboratorios siguen disponibles para estudiar cada componente.

1. Extrae el paquete completo y abre la carpeta actual que contiene `requirements.txt`, `app.py` y `backend.py`.
2. Crea el entorno e instala las dependencias según [GUIA_INSTALACION.md](docs/GUIA_INSTALACION.md).
3. Enciende MySQL y prepara la base, la cuenta de aplicación y `.env` según [MYSQL.md](docs/MYSQL.md).
4. Abre dos terminales en esa misma carpeta. En la primera arranca la API y en la segunda la interfaz.

macOS y Linux, terminal 1:
```sh
.venv/bin/python -m uvicorn backend:create_app --factory --host 127.0.0.1 --port 8000
```

macOS y Linux, terminal 2:
```sh
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Windows PowerShell, terminal 1:
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend:create_app --factory --host 127.0.0.1 --port 8000
```

Windows PowerShell, terminal 2:
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Abre `http://127.0.0.1:8501`, registra una cuenta de práctica, inicia sesión y pulsa **Nueva conversación**. Envía `cuántos libros puedo pedir`: debe aparecer un pasaje con fuente. Prueba `¿Cuál es el precio de una laptop?`: debe abstenerse sin cita. Cierra sesión y vuelve a entrar: los mensajes y las fuentes deben recuperarse desde MySQL.

El [recorrido completo de la aplicación](labs/10_chatpnl_starter/README.md) explica selección, renombrado, borrado con confirmación, reintentos, persistencia y prueba entre dos cuentas. La API y la interfaz son dos procesos de una misma aplicación; no debes alternar entre los laboratorios 06 y 10 para iniciar sesión y chatear. Usa únicamente la API indicada arriba durante ese recorrido.

El corpus de consulta contiene cuatro documentos ficticios compartidos. Los historiales son privados por usuario. Incorporar documentos propios con permisos, intenciones, entidades y comparación de modelos sigue formando parte de los ejercicios pendientes.
## Materiales

- `docs/GUIA_INSTALACION.md`: macOS/Windows y pasos exactos.
- `docs/MYSQL.md`: dependencias locales opcionales según laboratorio.

La presentación editable y su PDF acompañan el material de práctica.

## Pruebas y experimentación

Los comandos de comprobación por sistema están en [la guía de instalación](docs/GUIA_INSTALACION.md#5-corregir-errores-de-preparación). 