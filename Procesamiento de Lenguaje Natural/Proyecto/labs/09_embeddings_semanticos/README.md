# Laboratorio formativo Streamlit 09: Embeddings semánticos

## 1. Comprender el recorrido

Comparar sobre la misma consulta un recuperador léxico y otro contextual. Un embedding es un vector numérico que representa texto; MiniLM produce esos vectores y no redacta respuestas. La app utiliza CPU y un modelo descargado previamente; no necesita una API externa.

## 2. Preparar la carpeta y el entorno

Primero completa los pasos 1 y 2 de [GUIA_INSTALACION.md](../../docs/GUIA_INSTALACION.md). Si ya los hiciste, reutiliza `.venv`; no la vuelvas a crear. Abre la carpeta que contiene `requirements.txt` y `labs/`, no esta subcarpeta del laboratorio. Los comandos de abajo se ejecutan desde esa raíz y seleccionan directamente el Python del entorno, sin depender de su activación.

Antes de cambiar de laboratorio, detén la app anterior con Ctrl+C para liberar el puerto 8501. No necesitas haber resuelto los ejercicios de las prácticas anteriores para ejecutar esta demostración.

L09 puede arrancar con la instalación básica para observar la advertencia, pero la comparación completa requiere preparar el modelo. Sigue [MODELO.md](../../docs/MODELO.md) para instalar las dependencias contextuales, descargar la revisión fijada a `models/minilm` y configurar su ruta absoluta. Esa guía incluye comandos separados para Windows y macOS. No descargues el modelo en cada ejecución.

## 3. Encender la aplicación

Usa una terminal en la raíz del proyecto.

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m streamlit run labs/09_embeddings_semanticos/app.py --server.address 127.0.0.1 --server.port 8501
```

macOS:
```sh
.venv/bin/python -m streamlit run labs/09_embeddings_semanticos/app.py --server.address 127.0.0.1 --server.port 8501
```

Resultado esperado: el proceso permanece encendido y muestra la dirección local. Abre `http://127.0.0.1:8501` en el navegador. Si solicita un correo opcional, puedes pulsar Enter sin escribirlo. No pegues estos comandos en la barra de direcciones.

## 4. Seguir los pasos y contrastar resultados

1. Abre la app sin un modelo configurado. TF-IDF debe seguir mostrando su tabla y el lado contextual debe indicar “Contextual pendiente”. Esta es una condición de preparación, no un resultado semántico ni un empate entre modelos.
2. Detén Streamlit. Sigue la preparación de MiniLM de MODELO.md y vuelve a abrir la app desde esa misma terminal. Espera la carga inicial: se utiliza el modelo local en CPU.
3. Con `quiero llevar libros a casa`, deben aparecer dos tablas, “TF-IDF” y “MiniLM multilingüe · CPU”, con hasta tres documentos cada una. Anota los identificadores y posiciones realmente observados; los modelos pueden ordenar distinto y no se exige que tengan el mismo primer resultado.
4. Prueba `cuántos libros puedo pedir` en ambos lados sin cambiar el corpus. Examina el texto de los documentos recuperados antes de decidir cuál responde mejor. No compares los cosenos de ambos espacios como si fueran probabilidades equivalentes.
5. Vacía la consulta: no debe calcularse un ranking nuevo. Restablece una consulta y comprueba que ambas columnas reaparecen. No publiques una comparación si una columna sigue pendiente.
6. Cierra el proceso y vuelve a abrirlo con las variables de modo sin conexión de MODELO.md. Si los archivos y dependencias están completos, deben aparecer de nuevo ambas tablas sin descargar pesos. La memoria de sesión conserva el encoder durante esa sesión; el modelo es público, pero los índices privados de un proyecto requieren aislamiento por propietario.

## 5. Resolver los ejercicios del alumno

La demostración anterior permite comprobar la instalación y comprender el flujo. Los ejercicios siguientes quedan pendientes y no incluyen su solución. Trabaja sobre tu copia, conserva los comentarios útiles y explica tus decisiones.

1. Comparar rankings sobre las mismas consultas.
2. Describir un desacuerdo con evidencia.
3. Calcular Recall@3 y MRR@5 usando los juicios.

## 6. Registrar la evidencia y cerrar

Registra la entrada utilizada, los pasos realizados y la salida realmente observada. Incluye al menos un caso válido y un caso inválido o una condición de fallo del recorrido. Escribe qué esperabas y si coincidió; una captura sin explicación no acredita el funcionamiento. Usa datos ficticios y omite contraseñas, tokens y archivos privados.

Explica qué información necesitas, además del ranking, para calcular Recall@3 o MRR@5. Describe un desacuerdo observado entre ambos métodos sin inventar resultados.

Pulsa Ctrl+C en la terminal de Streamlit. Para volver a abrir, usa los mismos comandos; no reinstales dependencias en cada sesión.

## Si algo no coincide

Si solo aparece TF-IDF, revisa que la ruta absoluta señale la carpeta completa del modelo, no un archivo aislado ni la carpeta padre. Reinicia Streamlit después de cambiar variables. No interpretes la advertencia como una medición de rendimiento.
