# Laboratorio formativo Streamlit 03: Historial de conversaciones

## 1. Comprender el recorrido

Distinguir el identificador de una conversación, su título y sus mensajes. La entrada es una pregunta o una acción de navegación; la salida es el historial de la conversación seleccionada. Un UUID identifica cada conversación aunque cambie su título. No requiere base de datos.

## 2. Preparar la carpeta y el entorno

Primero completa los pasos 1 y 2 de [GUIA_INSTALACION.md](../../docs/GUIA_INSTALACION.md). Si ya los hiciste, reutiliza `.venv`; no la vuelvas a crear. Abre la carpeta que contiene `requirements.txt` y `labs/`, no esta subcarpeta del laboratorio. Los comandos de abajo se ejecutan desde esa raíz y seleccionan directamente el Python del entorno, sin depender de su activación.

Antes de cambiar de laboratorio, detén la app anterior con Ctrl+C para liberar el puerto 8501. No necesitas haber resuelto los ejercicios de las prácticas anteriores para ejecutar esta demostración.

Abre `labs/03_historial_conversaciones/app.py` en el editor para leerlo mientras observas la aplicación. Conserva los comentarios `TODO_ESTUDIANTE`: indican el trabajo que aún debes realizar.

## 3. Encender la aplicación

Usa una terminal en la raíz del proyecto.

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m streamlit run labs/03_historial_conversaciones/app.py --server.address 127.0.0.1 --server.port 8501
```

macOS:
```sh
.venv/bin/python -m streamlit run labs/03_historial_conversaciones/app.py --server.address 127.0.0.1 --server.port 8501
```

Resultado esperado: el proceso permanece encendido y muestra la dirección local. Abre `http://127.0.0.1:8501` en el navegador. Si solicita un correo opcional, puedes pulsar Enter sin escribirlo. No pegues estos comandos en la barra de direcciones.

## 4. Seguir los pasos y contrastar resultados

1. Se crea una conversación vacía. En “Nuevo título” escribe `Consulta A` y pulsa “Renombrar”. El título principal y el selector deben mostrarlo.
2. Envía `hola`. Debe aparecer el par de mensajes del chat local.
3. Pulsa “Nueva conversación”. Debe quedar seleccionada una conversación vacía y la anterior debe continuar en el selector. Renombra la nueva como `Consulta B` y envía `Me gusta estudiar`.
4. En “Conversaciones”, selecciona `Consulta A`. Debe verse su saludo, sin el mensaje de B. Regresa a B y comprueba que conserva su propio par de mensajes. El selector añade entre paréntesis los primeros ocho caracteres del UUID para distinguir conversaciones aunque compartan título. Un título legible no sustituye al UUID interno.
5. Con B seleccionada pulsa “Eliminar conversación”. Debe desaparecer del selector y quedar A. La demo elimina de inmediato: pedir confirmación es un ejercicio pendiente.
6. Elimina A. Debe crearse una conversación vacía para que la app no quede sin selección. Este historial vive en `session_state`; perder la sesión o reiniciar el servidor puede borrarlo. No demuestra persistencia en MySQL.

## 5. Resolver los ejercicios del alumno

La demostración anterior permite comprobar la instalación y comprender el flujo. Los ejercicios siguientes quedan pendientes y no incluyen su solución. Trabaja sobre tu copia, conserva los comentarios útiles y explica tus decisiones.

1. Generar título a partir del primer mensaje.
2. Buscar conversaciones por texto.
3. Solicitar confirmación antes de eliminar.

## 6. Registrar la evidencia y cerrar

Registra la entrada utilizada, los pasos realizados y la salida realmente observada. Incluye al menos un caso válido y un caso inválido o una condición de fallo del recorrido. Escribe qué esperabas y si coincidió; una captura sin explicación no acredita el funcionamiento. Usa datos ficticios y omite contraseñas, tokens y archivos privados.

¿Por qué puede cambiar el título sin cambiar el UUID? ¿Qué falta para conservar los mensajes después de terminar la sesión?

Pulsa Ctrl+C en la terminal de Streamlit. Para volver a abrir, usa los mismos comandos; no reinstales dependencias en cada sesión.

## Si algo no coincide

Si ambas conversaciones tienen el mismo nombre, renómbralas para poder distinguirlas. Eliminar la última crea otra vacía. No interpretes una sesión de navegador como almacenamiento duradero.
