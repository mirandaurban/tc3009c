# Instalación y primer arranque

## 1. Elegir una carpeta de trabajo

Usa Python 3.11 de 64 bits. Este proyecto está preparado para CPU; no necesitas GPU ni una cuenta de API. Necesitas internet para instalar dependencias y, en L09, descargar el modelo una vez. Un editor como VS Code sirve para modificar archivos; escribir un comando en el editor no lo ejecuta: los comandos siguientes van en una terminal.

Descomprime por completo el paquete de laboratorios y abre la carpeta del proyecto que contiene `requirements.txt`, `pyproject.toml`, `labs/`, `docs/` y `scripts/`. No ejecutes archivos dentro de la vista del ZIP. Si quedó una carpeta dentro de otra con el mismo nombre, entra en la que contiene `requirements.txt`.

Todas las instrucciones parten de esa carpeta actual. El código y los ejemplos ya vienen incluidos; no necesitas buscar carpetas externas ni copiar archivos de otro proyecto. Para subir documentos en L07, el paquete incluye `biblioteca_aurora.pdf` y `prestamos.txt` junto a los archivos iniciales.

En VS Code: Archivo, Abrir carpeta; selecciona la carpeta anterior y después Terminal, Nueva terminal. En Windows selecciona **PowerShell** como terminal; en macOS usa Terminal con zsh o bash; en Linux abre tu terminal. Comprueba la ubicación con los comandos siguientes. Las comillas permiten rutas con espacios. Sustituye la ruta si guardaste el proyecto en otro sitio.

Windows PowerShell, ejemplo con el ZIP extraído en Descargas:
```powershell
Set-Location "$HOME\Downloads\chatpnl-streamlit-labs"
Get-Location
Get-ChildItem requirements.txt, pyproject.toml, labs
py -3.11 --version
```

macOS, ejemplo con el ZIP extraído en Descargas:
```sh
cd "$HOME/Downloads/chatpnl-streamlit-labs"
pwd
ls requirements.txt pyproject.toml labs
python3.11 --version
```

Resultado esperado: aparecen los archivos y una versión `Python 3.11.x`. Si el comando de Python no existe, instala Python 3.11 desde [python.org](https://www.python.org/downloads/), cierra y vuelve a abrir la terminal y repite la comprobación. En Windows habilita el lanzador `py` en el instalador. No continúes si no aparece la versión requerida.

## 2. Crear el entorno del proyecto una sola vez

Un entorno virtual guarda las bibliotecas de este proyecto sin mezclarlas con las de otras materias. `.venv` es una carpeta creada por Python, no un archivo que debas escribir. Ejecuta únicamente el bloque de tu sistema desde la raíz comprobada en el paso 1.

Windows PowerShell:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe scripts/check_install.py
```

macOS:
```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e .
.venv/bin/python scripts/check_install.py
```

`-m pip` instala usando el Python indicado. `-r requirements.txt` lee la lista de bibliotecas. `-e .` conecta el paquete local `chatpnl_labs` con este entorno; el punto significa la carpeta actual. No omitas esa segunda instalación. La primera instalación puede tardar varios minutos; espera a que vuelva el indicador de la terminal antes de ejecutar la siguiente línea.

Resultado esperado: el comprobador imprime versiones de Streamlit, FastAPI y las demás bibliotecas, seguido de `Fragmentos: 4`. No debe terminar con un error. Conserva la última parte de la salida, sin contraseñas. Si falla una descarga, corrige la conexión y repite la línea que falló; no vuelvas a crear el entorno.

Todos los laboratorios usan rutas explícitas a este Python para evitar dudas sobre qué entorno está activo. Por eso no hace falta activar `.venv` ni cambiar la política de PowerShell. Si prefieres activarlo, Windows usa `.\.venv\Scripts\Activate.ps1` y macOS `source .venv/bin/activate`; después `python` debe apuntar al mismo entorno. Los comandos de las guías funcionan también sin esa activación.

## 3. Abrir la primera aplicación

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m streamlit run labs/01_streamlit_basico/app.py --server.address 127.0.0.1 --server.port 8501
```

macOS:
```sh
.venv/bin/python -m streamlit run labs/01_streamlit_basico/app.py --server.address 127.0.0.1 --server.port 8501
```

La terminal queda ocupada porque mantiene un servidor encendido: no es un bloqueo. Si aparece la pregunta opcional de correo de Streamlit, puedes dejarla vacía y pulsar Enter. Abre `http://127.0.0.1:8501` en el navegador si no se abre automáticamente. Debes ver “Un perfil para explorar Streamlit”. Sigue ahora el [recorrido de L01](../labs/01_streamlit_basico/README.md).

Al terminar, vuelve a esa terminal y pulsa Ctrl+C. Cerrar la pestaña del navegador no detiene el servidor. Para pasar al siguiente laboratorio, detén el anterior y ejecuta su comando. Así siempre usarás el puerto 8501.

## 4. Entender las dos terminales de L05, L06 y L10

El navegador muestra Streamlit en el puerto 8501. Streamlit envía solicitudes HTTP a FastAPI en el puerto 8000. Son dos procesos: cada uno necesita una terminal, ambas abiertas en la misma raíz del proyecto. No escribas el segundo comando dentro de la terminal ocupada por el primero.

Cada README incluye los dos comandos por sistema. Arranca primero la API y espera `Application startup complete`; después arranca Streamlit. Comprueba la API en `http://127.0.0.1:8000/health` y su documentación en `http://127.0.0.1:8000/docs`. El resultado de `/health` es `{"status":"ok"}`. En L06 eso solo confirma que responde el proceso; crear y volver a leer una conversación confirma el acceso a la base de datos.

L05 y L06 conservan sus APIs de ejemplo; L10 reúne acceso, chat e historial en la API integrada. Estos ejemplos comparten puerto. Detén la API anterior con Ctrl+C antes de cambiar de laboratorio. Para terminar, detén primero Streamlit y después FastAPI. L06 requiere además [preparar MySQL con MAMP o LAMP](MYSQL.md); L09 requiere [preparar MiniLM](MODELO.md).

## 5. Corregir errores de preparación

| Síntoma | Comprobación y acción |
|---|---|
| No se encuentra `.venv` o `requirements.txt` | Comprueba la carpeta con el paso 1. No ejecutes desde `labs/01.../`. |
| `No module named chatpnl_labs` | Ejecuta `-m pip install -e .` con el Python de `.venv`, desde la raíz. |
| `No module named streamlit` | Repite la instalación de `requirements.txt` con ese mismo Python. |
| Puerto ocupado | Detén el proceso que abriste antes con Ctrl+C. No cierres procesos ajenos. |
| Conexión rechazada por la aplicación | Revisa que FastAPI esté encendido y corresponda al laboratorio. |
| HTTP 404 | Comprueba el módulo de API: usar la API de otro laboratorio deja rutas inexistentes. |
| HTTP 422 | La API recibió la solicitud, pero los datos no cumplen su esquema; revisa el campo enviado. |
| No aparece un modelo contextual | Sigue MODELO.md; la instalación básica permite TF-IDF, pero no prepara los pesos. |

Para comprobar dependencias y las pruebas básicas, desde la raíz:

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q -m "not mysql"
```

macOS:
```sh
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q -m "not mysql"
```

`pip check` debe indicar que no hay requisitos incompatibles y pytest terminar sin fallos. La prueba MySQL se ejecuta por separado sobre una base de pruebas, según MYSQL.md. Estas comprobaciones no resuelven los ejercicios pendientes.

Los recorridos de referencia se ejecutaron en macOS. Los comandos PowerShell se revisaron por sintaxis y rutas; no se afirma una ejecución en Windows. Las versiones fijadas de bibliotecas están en `requirements.txt`; no uses un archivo de bloqueo exclusivo de macOS como requisito universal para Windows.

## Si utilizas Linux

Con Python 3.11 ya disponible, los comandos de creación de entorno e instalación son los mismos que los de macOS: `python3.11 -m venv .venv` y después `.venv/bin/python` para instalar y ejecutar. Comprueba primero `python3.11 --version`; si tu distribución utiliza otra versión predeterminada, prepara 3.11 antes de continuar. No reemplaces a ciegas el Python del sistema. En los laboratorios usa los bloques macOS, cuyas rutas `.venv/bin/python` también corresponden a Linux. Para MySQL sigue la sección LAMP de MYSQL.md. Las instrucciones se han revisado; no se afirma una ejecución en Linux.

## Aplicación integrada: acceso y chat en la misma pantalla

Para ejecutarla directamente, completa la preparación de entorno de esta guía y configura MAMP/MySQL según MYSQL.md. Después usa `backend:create_app` en la terminal de API y `app.py` en la de Streamlit, con los comandos por sistema del README principal. El recorrido de L10 incluye registro, inicio de sesión, chat, fuentes persistidas, selección, renombrado, borrado y recuperación del historial. No necesitas cambiar entre L06 y L10 para usar autenticación y chat.
