# Laboratorio formativo Streamlit 08: Búsqueda con TF-IDF

## 1. Comprender el recorrido

Comparar una pregunta con los fragmentos de cuatro documentos públicos ficticios. TF-IDF representa palabras y su relevancia; el coseno ordena similitud léxica. El ranking propone candidatos y una comprobación de evidencia decide si hay respaldo suficiente para responder. No requiere API ni modelo contextual.

## 2. Preparar la carpeta y el entorno

Primero completa los pasos 1 y 2 de [GUIA_INSTALACION.md](../../docs/GUIA_INSTALACION.md). Si ya los hiciste, reutiliza `.venv`; no la vuelvas a crear. Abre la carpeta que contiene `requirements.txt` y `labs/`, no esta subcarpeta del laboratorio. Los comandos de abajo se ejecutan desde esa raíz y seleccionan directamente el Python del entorno, sin depender de su activación.

Antes de cambiar de laboratorio, detén la app anterior con Ctrl+C para liberar el puerto 8501. No necesitas haber resuelto los ejercicios de las prácticas anteriores para ejecutar esta demostración.

Abre `labs/08_busqueda_tfidf/app.py` en el editor para leerlo mientras observas la aplicación. Conserva los comentarios `TODO_ESTUDIANTE`: indican el trabajo que aún debes realizar.

## 3. Encender la aplicación

Usa una terminal en la raíz del proyecto.

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m streamlit run labs/08_busqueda_tfidf/app.py --server.address 127.0.0.1 --server.port 8501
```

macOS:
```sh
.venv/bin/python -m streamlit run labs/08_busqueda_tfidf/app.py --server.address 127.0.0.1 --server.port 8501
```

Resultado esperado: el proceso permanece encendido y muestra la dirección local. Abre `http://127.0.0.1:8501` en el navegador. Si solicita un correo opcional, puedes pulsar Enter sin escribirlo. No pegues estos comandos en la barra de direcciones.

## 4. Seguir los pasos y contrastar resultados

1. Mantén “Consulta” en `cuántos libros puedo pedir`, “Top-k” en 3 y “Umbral didáctico de abstención” en 0.08. Debes ver un ranking y un JSON de respuesta.
2. El JSON debe incluir `abstained: false`, el pasaje que dice “hasta tres libros por persona” y una referencia a `prestamos.txt`, página 1. El documento aceptado puede estar en segundo lugar: similitud alta no significa respaldo completo. En esta consulta la respuesta selecciona el candidato respaldado dentro de los tres revisados.
3. Examina `evidence`: `missing_terms` debe quedar vacío para el candidato aceptado; `selected_rank` identifica su posición. `score` es similitud, no una probabilidad ni un porcentaje de aciertos.
4. Prueba `¿Cuál es el precio de una laptop?`. Debe verse “No encuentro evidencia suficiente en este corpus.”, `abstained: true` y `references: []`, aunque el ranking siga mostrando candidatos. Un ranking siempre puede ordenar documentos aun cuando ninguno responda.
5. Vacía la consulta. La app deja de presentar resultados de recuperación; no envía una consulta vacía. Restablece la primera pregunta y conserva el umbral 0.08 para reproducir el recorrido.
6. Mueve “Top-k” entre 1, 3 y 4 y observa cuántas filas muestra la tabla. Este control cambia el ranking visible; la función de respuesta conserva su propia revisión de hasta tres candidatos. No interpretes el slider como un cambio automático de la política de respuesta.

## 5. Resolver los ejercicios del alumno

La demostración anterior permite comprobar la instalación y comprender el flujo. Los ejercicios siguientes quedan pendientes y no incluyen su solución. Trabaja sobre tu copia, conserva los comentarios útiles y explica tus decisiones.

1. Comparar k=1,3,4.
2. Comparar unigramas y bigramas.
3. Evaluar consultas fuera de alcance y ajustar umbral con dev.

## 6. Registrar la evidencia y cerrar

Registra la entrada utilizada, los pasos realizados y la salida realmente observada. Incluye al menos un caso válido y un caso inválido o una condición de fallo del recorrido. Escribe qué esperabas y si coincidió; una captura sin explicación no acredita el funcionamiento. Usa datos ficticios y omite contraseñas, tokens y archivos privados.

Explica por qué se rechazó el primer candidato en la consulta de libros y por qué un ranking no certifica una respuesta.

Pulsa Ctrl+C en la terminal de Streamlit. Para volver a abrir, usa los mismos comandos; no reinstales dependencias en cada sesión.

## Si algo no coincide

Obtener un primer documento con score positivo no obliga a responder. Lee `missing_terms` y la fuente. Deja el umbral en 0.08 para este recorrido; no lo bajes para forzar que una consulta sin evidencia reciba respuesta.

La política de referencia está congelada: umbral 0.08 elegido con desarrollo, sin selección sobre prueba. Las cuatro pruebas anteriores están retiradas. El test final didáctico ya publicado sirve para reproducir resultados, no para volver a ajustar decisiones. Para tu proyecto, prepara desarrollo propio y una prueba nueva reservada, congela antes de abrirla y sigue [el protocolo de evaluación](../../evaluacion_pnl/README.md).
