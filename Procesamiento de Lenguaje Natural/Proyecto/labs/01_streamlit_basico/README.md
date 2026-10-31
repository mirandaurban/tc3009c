# Laboratorio formativo Streamlit 01: Introducción a Streamlit

Esta práctica pertenece a la ruta complementaria ChatPNL; no sustituye ni renumera el laboratorio oficial 01 de `evaluaciones/`.

## 1. Comprender el recorrido

Comprender cómo una interacción vuelve a ejecutar el archivo y cómo `session_state` conserva datos dentro de una sesión. La entrada es un alias con preferencias; la salida es un perfil visible y un contador. No requiere API ni base de datos.

## 2. Preparar la carpeta y el entorno

Primero completa los pasos 1 y 2 de [GUIA_INSTALACION.md](../../docs/GUIA_INSTALACION.md). Si ya los hiciste, reutiliza `.venv`; no la vuelvas a crear. Abre la carpeta que contiene `requirements.txt` y `labs/`, no esta subcarpeta del laboratorio. Los comandos de abajo se ejecutan desde esa raíz y seleccionan directamente el Python del entorno, sin depender de su activación.

Antes de cambiar de laboratorio, detén la app anterior con Ctrl+C para liberar el puerto 8501. No necesitas haber resuelto los ejercicios de las prácticas anteriores para ejecutar esta demostración.

Abre `labs/01_streamlit_basico/app.py` en el editor para leerlo mientras observas la aplicación. Conserva los comentarios `TODO_ESTUDIANTE`: indican el trabajo que aún debes realizar.

## 3. Encender la aplicación

Usa una terminal en la raíz del proyecto.

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m streamlit run labs/01_streamlit_basico/app.py --server.address 127.0.0.1 --server.port 8501
```

macOS:
```sh
.venv/bin/python -m streamlit run labs/01_streamlit_basico/app.py --server.address 127.0.0.1 --server.port 8501
```

Resultado esperado: el proceso permanece encendido y muestra la dirección local. Abre `http://127.0.0.1:8501` en el navegador. Si solicita un correo opcional, puedes pulsar Enter sin escribirlo. No pegues estos comandos en la barra de direcciones.

## 4. Seguir los pasos y contrastar resultados

1. Al abrir, comprueba el título “Un perfil para explorar Streamlit”, las preferencias de la barra lateral, “Aún no hay perfil” y `Clics: 0`.
2. Deja el alias vacío y pulsa “Guardar perfil”. Debe aparecer “El alias es obligatorio”; no se crea un perfil válido.
3. Elige “Programación” en “Tema” y 5 en “Horas de estudio”. Escribe `alumno_demo` en el alias y pulsa “Guardar perfil”. En “Datos enviados” deben aparecer alias, tema y horas con esos valores. El formulario envía el alias al pulsar su botón.
4. Pulsa dos veces “Contar clic”. El contador debe marcar 2 y el perfil enviado debe seguir visible. Una variable local se reconstruiría en cada ejecución; el diccionario de sesión conserva este estado.
5. Cambia el tema a “Investigación” sin volver a guardar. El perfil mostrado debe mantener el tema previamente enviado. Pulsa “Guardar perfil” para actualizarlo. Desmarca “Mostrar explicación”: se oculta la explicación de la derecha, sin borrar el perfil.
6. Abre `app.py` y localiza el formulario, las dos columnas y las claves `profile_data` y `clicks`. Sigue el valor desde el widget hasta la salida; después identifica el comentario `TODO_ESTUDIANTE`.

## 5. Resolver los ejercicios del alumno

La demostración anterior permite comprobar la instalación y comprender el flujo. Los ejercicios siguientes quedan pendientes y no incluyen su solución. Trabaja sobre tu copia, conserva los comentarios útiles y explica tus decisiones.

1. Crear formulario de perfil con carrera.
2. Validar todos los campos obligatorios.
3. Distribuir resultados en columnas.

## 6. Registrar la evidencia y cerrar

Registra la entrada utilizada, los pasos realizados y la salida realmente observada. Incluye al menos un caso válido y un caso inválido o una condición de fallo del recorrido. Escribe qué esperabas y si coincidió; una captura sin explicación no acredita el funcionamiento. Usa datos ficticios y omite contraseñas, tokens y archivos privados.

¿Qué cambio reejecutó el archivo y qué dato solo cambió al enviar el formulario? Explica por qué el contador necesita estado.

Pulsa Ctrl+C en la terminal de Streamlit. Para volver a abrir, usa los mismos comandos; no reinstales dependencias en cada sesión.

## Si algo no coincide

Alias vacío: pulsa Guardar con un alias de práctica. Perfil sin actualizar: cambiar una preferencia no sustituye el envío del formulario. Al editar código evita claves de widgets repetidas.
