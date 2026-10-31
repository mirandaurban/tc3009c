# Laboratorio formativo Streamlit 02: Chat básico
## 1. Comprender el recorrido

Construir el recorrido de un mensaje: entrada del usuario, almacenamiento en una lista y representación de la respuesta. La respuesta de esta demo la calcula una función local; no consulta documentos ni un modelo generativo. No requiere servicios externos.

## 2. Preparar la carpeta y el entorno

Primero completa los pasos 1 y 2 de [GUIA_INSTALACION.md](../../docs/GUIA_INSTALACION.md). Si ya los hiciste, reutiliza `.venv`; no la vuelvas a crear. Abre la carpeta que contiene `requirements.txt` y `labs/`, no esta subcarpeta del laboratorio. Los comandos de abajo se ejecutan desde esa raíz y seleccionan directamente el Python del entorno, sin depender de su activación.

Antes de cambiar de laboratorio, detén la app anterior con Ctrl+C para liberar el puerto 8501. No necesitas haber resuelto los ejercicios de las prácticas anteriores para ejecutar esta demostración.

Abre `labs/02_chat_basico/app.py` en el editor para leerlo mientras observas la aplicación. Conserva los comentarios `TODO_ESTUDIANTE`: indican el trabajo que aún debes realizar.

## 3. Encender la aplicación

Usa una terminal en la raíz del proyecto.

Si te falla algo no olvides ejecutar:
```sh
python -m pip install -e .
```

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m streamlit run labs/02_chat_basico/app.py --server.address 127.0.0.1 --server.port 8501
```

macOS:
```sh
.venv/bin/python -m streamlit run labs/02_chat_basico/app.py --server.address 127.0.0.1 --server.port 8501
```

Resultado esperado: el proceso permanece encendido y muestra la dirección local. Abre `http://127.0.0.1:8501` en el navegador. Si solicita un correo opcional, puedes pulsar Enter sin escribirlo. No pegues estos comandos en la barra de direcciones.

## 4. Seguir los pasos y contrastar resultados

1. Comprueba que se ve “ChatPNL · mi primer chat” y que todavía no hay mensajes. La barra de entrada está en la parte inferior.
2. Escribe `hola` y pulsa Enter. Deben aparecer dos mensajes: el tuyo y “Hola. Esta demostración conserva mensajes durante tu sesión.”
3. Envía `Me gusta estudiar`. La respuesta debe ser “Recibí 3 palabras. Soy una función local, no un modelo generativo.” Ahora hay cuatro mensajes: dos del usuario y dos de la función.
4. Intenta enviar una entrada vacía o formada por espacios. No debe añadirse un par de mensajes. El widget limita la escritura a 1,000 caracteres; una validación propia de longitud sigue siendo un ejercicio.
5. Pulsa “Limpiar conversación” en la barra lateral. Los mensajes deben desaparecer; aún no se agrega una bienvenida automática.
6. Lee `messages` en `app.py`: cada elemento conserva `role` y `content`. El bucle redibuja mensajes ya almacenados; no los vuelve a generar. Localiza dónde se añaden ambos mensajes antes de `st.rerun()`.

## 5. Resolver los ejercicios del alumno

La demostración anterior permite comprobar la instalación y comprender el flujo. Los ejercicios siguientes quedan pendientes y no incluyen su solución. Trabaja sobre tu copia, conserva los comentarios útiles y explica tus decisiones.

1. Añadir mensaje inicial al crear la sesión.
2. Rechazar entradas vacías y definir un límite menor.
3. Reiniciar conservando el mensaje de bienvenida.

## 6. Registrar la evidencia y cerrar

Registra la entrada utilizada, los pasos realizados y la salida realmente observada. Incluye al menos un caso válido y un caso inválido o una condición de fallo del recorrido. Escribe qué esperabas y si coincidió; una captura sin explicación no acredita el funcionamiento. Usa datos ficticios y omite contraseñas, tokens y archivos privados.

¿Qué diferencia hay entre añadir mensajes a la lista y volver a dibujarla? Identifica dónde se calcula la respuesta local.

Pulsa Ctrl+C en la terminal de Streamlit. Para volver a abrir, usa los mismos comandos; no reinstales dependencias en cada sesión.

## Si algo no coincide

Si no aparece respuesta, confirma que enviaste con Enter y que no había solo espacios. Una respuesta de conteo es el comportamiento de esta función, no un fallo de un modelo. Si vuelves a abrir una sesión nueva no esperes el chat anterior.
