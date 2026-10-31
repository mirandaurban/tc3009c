# Laboratorio formativo Streamlit 05: Integración con FastAPI

## 1. Comprender el recorrido

Observar el intercambio entre un formulario, una solicitud HTTP y una API. Streamlit recoge texto; FastAPI recibe JSON y devuelve un eco o un conteo. JSON representa datos mediante campos y valores. Necesitas dos terminales, sin MySQL.

## 2. Preparar la carpeta y el entorno

Primero completa los pasos 1 y 2 de [GUIA_INSTALACION.md](../../docs/GUIA_INSTALACION.md). Si ya los hiciste, reutiliza `.venv`; no la vuelvas a crear. Abre la carpeta que contiene `requirements.txt` y `labs/`, no esta subcarpeta del laboratorio. Los comandos de abajo se ejecutan desde esa raíz y seleccionan directamente el Python del entorno, sin depender de su activación.

Antes de cambiar de laboratorio, detén la app anterior con Ctrl+C para liberar el puerto 8501. No necesitas haber resuelto los ejercicios de las prácticas anteriores para ejecutar esta demostración.

Abre `labs/05_integracion_fastapi/app.py` en el editor para leerlo mientras observas la aplicación. Conserva los comentarios `TODO_ESTUDIANTE`: indican el trabajo que aún debes realizar.

## 3. Encender la aplicación

### Terminal 1: FastAPI

Abre una terminal en la raíz y ejecuta el bloque de tu sistema. Déjala abierta hasta terminar.

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m uvicorn chatpnl_labs.simple_api:app --host 127.0.0.1 --port 8000
```

macOS:
```sh
.venv/bin/python -m uvicorn chatpnl_labs.simple_api:app --host 127.0.0.1 --port 8000
```

Resultado esperado: `Application startup complete`. La API escucha en `http://127.0.0.1:8000`; el navegador de la interfaz usará otro puerto.

### Terminal 2: Streamlit

Abre otra terminal en la misma raíz.

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m streamlit run labs/05_integracion_fastapi/app.py --server.address 127.0.0.1 --server.port 8501
```

macOS:
```sh
.venv/bin/python -m streamlit run labs/05_integracion_fastapi/app.py --server.address 127.0.0.1 --server.port 8501
```

Resultado esperado: el proceso permanece encendido y muestra la dirección local. Abre `http://127.0.0.1:8501` en el navegador. Si solicita un correo opcional, puedes pulsar Enter sin escribirlo. No pegues estos comandos en la barra de direcciones.

Si falla algo ejecutar:
```sh
python3.11 -m venv .venv

.venv/bin/python -m pip install -r requirements.txt

.venv/bin/python -m pip install -e .

.venv/bin/python -m uvicorn chatpnl_labs.simple_api:app --host 127.0.0.1 --port 8000
.venv/bin/python -m streamlit run labs/05_integracion_fastapi/app.py
```

## 4. Seguir los pasos y contrastar resultados

1. Antes de abrir Streamlit, visita `http://127.0.0.1:8000/health`. Debes ver `{"status":"ok"}`. En `/docs` deben figurar `/api/v1/echo` y `/api/v1/analyze`; si ves rutas de otro laboratorio, detén esa API.
2. En Streamlit escribe `Hola mundo`, selecciona `echo` y pulsa “Enviar a FastAPI”. Debe verse `{"text":"Hola mundo"}`. El cliente envía una solicitud POST con el campo `text`.
3. Mantén `Hola mundo`, selecciona `analyze` y envía. Deben aparecer `words: 2` y `characters: 10`; el espacio cuenta como carácter, pero separa las palabras.
4. Vacía el campo y envía. Debe aparecer un error con HTTP 422 porque el esquema no permite texto vacío. Esto es distinto de una falla de conexión: la API sí recibió los datos.
5. Detén solo FastAPI con Ctrl+C y vuelve a enviar texto válido desde Streamlit. Debe mostrarse un error de conexión, sin que la página termine con una excepción. El cliente tiene un tiempo límite de espera.
6. Vuelve a ejecutar el comando de la terminal 1 y espera el arranque. Envía `Hola mundo` con `analyze`: debe recuperarse el resultado 2 y 10. Lee `request_json` y el manejo de `ServiceError` para seguir solicitud, respuesta y error.

## 5. Resolver los ejercicios del alumno

La demostración anterior permite comprobar la instalación y comprender el flujo. Los ejercicios siguientes quedan pendientes y no incluyen su solución. Trabaja sobre tu copia, conserva los comentarios útiles y explica tus decisiones.

1. Crear endpoint de minúsculas con esquema.
2. Mostrar un caso 422 y corregirlo.
3. Detener backend, observar error y recuperarlo.

## 6. Registrar la evidencia y cerrar

Registra la entrada utilizada, los pasos realizados y la salida realmente observada. Incluye al menos un caso válido y un caso inválido o una condición de fallo del recorrido. Escribe qué esperabas y si coincidió; una captura sin explicación no acredita el funcionamiento. Usa datos ficticios y omite contraseñas, tokens y archivos privados.

Explica la diferencia entre un 422 y una conexión rechazada. Identifica entrada, solicitud JSON, operación y salida para `analyze`.

Pulsa Ctrl+C en la terminal de Streamlit. Después pulsa Ctrl+C en la terminal de FastAPI. Para volver a abrir, usa los mismos comandos; no reinstales dependencias en cada sesión.

## Si algo no coincide

Conexión rechazada: revisa la terminal 1. HTTP 404: puede estar corriendo la API de otro laboratorio. HTTP 422: revisa el texto, no reinstales FastAPI. “Address already in use”: detén tu proceso anterior.
