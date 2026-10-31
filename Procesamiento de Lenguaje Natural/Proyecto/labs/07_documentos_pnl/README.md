# Laboratorio formativo Streamlit 07: Documentos y fragmentos

## 1. Comprender el recorrido

Extraer texto de un TXT o PDF y dividirlo en fragmentos sin perder procedencia. La entrada son bytes de un archivo; la salida es texto con página y posición. Fragmentar permite recuperar partes manejables del documento. No requiere API ni un modelo.

## 2. Preparar la carpeta y el entorno

Primero completa los pasos 1 y 2 de [GUIA_INSTALACION.md](../../docs/GUIA_INSTALACION.md). Si ya los hiciste, reutiliza `.venv`; no la vuelvas a crear. Abre la carpeta que contiene `requirements.txt` y `labs/`, no esta subcarpeta del laboratorio. Los comandos de abajo se ejecutan desde esa raíz y seleccionan directamente el Python del entorno, sin depender de su activación.

Antes de cambiar de laboratorio, detén la app anterior con Ctrl+C para liberar el puerto 8501. No necesitas haber resuelto los ejercicios de las prácticas anteriores para ejecutar esta demostración.

El paquete incluye `biblioteca_aurora.pdf` y `prestamos.txt` en la carpeta actual del proyecto. Elige uno desde el explorador que abre el cargador. La app admite hasta 2,000,000 bytes por archivo, PDF de hasta 100 páginas y TXT UTF-8.

## 3. Encender la aplicación

Usa una terminal en la raíz del proyecto.

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m streamlit run labs/07_documentos_pnl/app.py --server.address 127.0.0.1 --server.port 8501
```

macOS:
```sh
.venv/bin/python -m streamlit run labs/07_documentos_pnl/app.py --server.address 127.0.0.1 --server.port 8501
```

Resultado esperado: el proceso permanece encendido y muestra la dirección local. Abre `http://127.0.0.1:8501` en el navegador. Si solicita un correo opcional, puedes pulsar Enter sin escribirlo. No pegues estos comandos en la barra de direcciones.

## 4. Seguir los pasos y contrastar resultados

1. Pulsa el selector de “Documento” y abre `biblioteca_aurora.pdf` incluido en la carpeta actual. Mantén “Palabras por fragmento” en 90 y “Solapamiento en palabras” en 15.
2. Debe aparecer `Palabras: 83` y una tabla de dos fragmentos: uno de la página 1 con 41 palabras y otro de la página 2 con 42. No es OCR: el PDF de ejemplo ya contiene texto extraíble.
3. Lee las columnas: `id` identifica el fragmento; `source` es el archivo; `page` es la página desde 1; `text` es el contenido; `start_word` es la posición inicial desde 0 dentro de esa página. Con estos parámetros ambas posiciones iniciales son 0.
4. Cambia el tamaño a 20 y el solapamiento a 5. Deben aparecer seis fragmentos: tres de la primera página y tres de la segunda. Los inicios de la primera son 0, 15 y 30; de la segunda, 0, 15 y 30. Repetir palabras entre fragmentos ayuda a conservar contexto, pero aumenta el número de filas.
5. Sustituye el archivo por `prestamos.txt`. Restablece 90 y 15: deben aparecer 38 palabras y un fragmento de página 1. Para un TXT se usa página 1 como convención, no como una paginación original del editor.
6. Prepara un archivo de texto vacío en el editor, guárdalo como `vacio.txt` y súbelo. Debe rechazarse con “Archivo vacío o mayor de 2 MB”. La aplicación también rechaza PDF sin texto extraíble y TXT que no sea UTF-8. Renombrar un TXT como PDF no lo convierte en PDF.
7. Lee el recorrido `file.getvalue()`, `read_document`, `chunk_pages` y tabla en `app.py`. El nombre recibido se conserva como referencia; no se utiliza para escribir el archivo del usuario en disco.

## 5. Resolver los ejercicios del alumno

La demostración anterior permite comprobar la instalación y comprender el flujo. Los ejercicios siguientes quedan pendientes y no incluyen su solución. Trabaja sobre tu copia, conserva los comentarios útiles y explica tus decisiones.

1. Comparar tamaño y solapamiento.
2. Mostrar palabras por documento.
3. Filtrar fragmentos por página.

## 6. Registrar la evidencia y cerrar

Registra la entrada utilizada, los pasos realizados y la salida realmente observada. Incluye al menos un caso válido y un caso inválido o una condición de fallo del recorrido. Escribe qué esperabas y si coincidió; una captura sin explicación no acredita el funcionamiento. Usa datos ficticios y omite contraseñas, tokens y archivos privados.

Explica cómo conservar página y posición permite comprobar una cita. ¿Qué cambia al aumentar solapamiento sin cambiar el documento?

Pulsa Ctrl+C en la terminal de Streamlit. Para volver a abrir, usa los mismos comandos; no reinstales dependencias en cada sesión.

## Si algo no coincide

Si no ves texto de un PDF escaneado, requiere OCR previo; este laboratorio no lo incorpora. Una extensión correcta no garantiza contenido válido. Si salen más filas, revisa tamaño y solapamiento antes de asumir un error.
