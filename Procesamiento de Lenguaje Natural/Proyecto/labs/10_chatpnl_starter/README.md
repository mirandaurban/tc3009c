# Laboratorio formativo Streamlit 10: aplicación integrada ChatPNL

## 1. Comprender el recorrido

La entrada es una cuenta de práctica y una pregunta sobre la biblioteca ficticia Aurora. FastAPI comprueba el JWT y que la conversación pertenezca a esa cuenta antes de recuperar evidencia. La salida es un pasaje con fuentes o una abstención. La pregunta, la respuesta y las referencias se guardan juntas en MySQL.

La interfaz muestra siempre los mensajes recuperados de la API. Una nueva sesión del navegador puede perder su token, pero al volver a iniciar sesión se recupera el historial desde la base. Las cuatro fuentes de consulta son públicas; los mensajes de cada cuenta son privados. La carga de documentos propios todavía es un ejercicio pendiente.

## 2. Preparar la carpeta y el entorno

Extrae el paquete completo y abre la carpeta actual que contiene `app.py`, `backend.py` y `requirements.txt`. Completa los pasos 1 y 2 de [GUIA_INSTALACION.md](../../docs/GUIA_INSTALACION.md); reutiliza `.venv` si ya está preparada.

Sigue [MYSQL.md](../../docs/MYSQL.md): MAMP en macOS/Windows o LAMP en Linux. Crea la base de práctica, su usuario y `.env`; verifica el puerto MySQL y genera la clave JWT. MAMP suele utilizar 8889; utiliza el puerto real de tu instalación. No copies el proyecto a la carpeta web de MAMP.

Si ya utilizaste L06 con la misma base, conserva la cuenta MySQL, el secreto y los usuarios registrados. Al arrancar se añade la tabla `chatpnl_turns` para guardar los turnos y sus fuentes; no se borran las tablas anteriores ni se exige volver a crear la base. Los mensajes antiguos que no tenían respuesta ni fuente se conservan como estaban.

Detén las APIs y aplicaciones de los otros laboratorios con Ctrl+C antes de comenzar. La aplicación integrada usa una sola API para cuentas, chat e historial.

## 3. Encender la aplicación

### Terminal 1: API

Con MySQL encendido, ejecuta desde la carpeta actual:

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend:create_app --factory --host 127.0.0.1 --port 8000
```

macOS y Linux:
```sh
.venv/bin/python -m uvicorn backend:create_app --factory --host 127.0.0.1 --port 8000
```

Resultado esperado: `Application startup complete`. Abre `http://127.0.0.1:8000/health`: debe mostrar `{"status":"ok"}`. En `/docs` deben aparecer `/auth/register`, `/auth/login`, `/conversations` y `/conversations/{cid}/query`.

### Terminal 2: Streamlit

Abre otra terminal en la misma carpeta y deja la primera encendida.

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

macOS y Linux:
```sh
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Preguntas que se pueden hacer:

¿Cuántos libros puedo pedir prestados?

¿Cuánto dura el préstamo?

¿Qué necesito para solicitar un préstamo?

¿Cuál es el horario de la biblioteca?

Resultado esperado: se muestra la dirección local. Abre `http://127.0.0.1:8501`; debe verse “ChatPNL” y el formulario de acceso. Si Streamlit pregunta un correo opcional, puedes dejarlo vacío. `app.py` reutiliza la interfaz de este laboratorio y `backend.py` expone su API, sin duplicar el código.

## 4. Seguir los pasos y contrastar resultados

1. Selecciona **Registrar usuario**. Escribe un nombre ficticio nuevo de al menos tres caracteres, en minúsculas, con números o guion bajo, y una contraseña de práctica de al menos diez caracteres. Pulsa **Enviar**: debe confirmar la creación.
2. Selecciona **Iniciar sesión**, vuelve a escribir ambos campos y envía. El formulario se limpia después del envío. Debe aparecer tu usuario en la barra lateral y el botón **Nueva conversación**.
3. Pulsa **Nueva conversación**. Se crea una conversación privada en MySQL y aparece la entrada del chat. En **Nuevo título**, escribe `Consulta A` y pulsa **Renombrar**. Debe conservarse seleccionada esa conversación.
4. Envía `cuántos libros puedo pedir`. Deben aparecer tu pregunta, un pasaje que contiene “hasta tres libros por persona” y una fuente `prestamos.txt`, página 1, identificador `prestamos.txt:p1:w0`.
5. Envía `¿Cuál es el precio de una laptop?`. Debe contestar “No encuentro evidencia suficiente en este corpus.” sin referencias. La abstención también queda en el historial.
6. Pulsa **Nueva conversación**, renómbrala como `Consulta B` y envía otra pregunta. Vuelve a A desde el selector: deben reaparecer sus cuatro mensajes y la fuente de la primera respuesta. Cambia entre A y B para comprobar que no se mezclan.
7. Pulsa **Cerrar sesión**. Debe volver el formulario, sin mensajes privados en pantalla. Entra con la misma cuenta: las conversaciones, mensajes y fuentes deben seguir disponibles. Se guardan en MySQL, no en una lista temporal del navegador.
8. Detén únicamente la API con Ctrl+C, vuelve a ejecutar su comando y pulsa **Actualizar historial** o vuelve a entrar si fuera necesario. La conversación debe conservarse. La interfaz informa un error mientras la API no esté disponible.
9. Registra una segunda cuenta ficticia. Al iniciar sesión con ella no deben aparecer las conversaciones de la primera. Vuelve a la primera para confirmar que su historial permanece. La API también rechaza leer, consultar, renombrar o borrar un identificador ajeno.
10. Para borrar una conversación de práctica, selecciónala, marca **Confirmo eliminar esta conversación** y pulsa **Eliminar conversación**. Debe desaparecer junto con sus mensajes y referencias. Cambiar de cuenta no elimina ningún historial.

Cada turno tiene un identificador de envío. Si la conexión falla después de guardar, **Reintentar envío** utiliza el mismo identificador y recupera la respuesta ya guardada, sin duplicar mensajes ni volver a calcularla. **Descartar reintento** abandona el reintento local; no borra un mensaje que ya hubiera quedado confirmado en MySQL. Revisa el historial antes de repetir manualmente la pregunta como un envío nuevo.

Si el JWT vence, la aplicación elimina la copia de sesión y vuelve al formulario. Iniciar sesión otra vez recupera el historial. Cerrar sesión elimina la copia local del token, pero el JWT emitido conserva su validez hasta vencer a los 15 minutos.

## 5. Resolver los ejercicios del alumno

El acceso, chat e historial ya están integrados. Permanecen estos ejercicios, sin sus soluciones privadas:

1. Incorporar documentos propios y fragmentos con permisos por propietario desde L07.
2. Integrar las intenciones y entidades del dominio.
3. Comparar recuperación clásica y contextual sobre los mismos datos.
4. Preparar desarrollo propio, congelar decisiones y evaluar con una prueba nueva reservada; verificar suficiencia de las citas.
5. Ampliar las pruebas de privacidad y registrar evidencia de fallos y recuperación para tu implementación.

Los comentarios `TODO_ESTUDIANTE` conservan únicamente el trabajo aún pendiente. Ejecutar esta base no completa todos los requisitos de la tarea final.

## 6. Registrar evidencia y cerrar

Conserva evidencia de una respuesta con fuente, una abstención sin cita, recuperación tras cerrar sesión y reiniciar API, aislamiento entre dos cuentas y borrado confirmado. Explica entrada, operación y salida. Usa datos ficticios y omite contraseñas, tokens y el contenido de `.env`.

En phpMyAdmin deben existir `chatpnl_users`, `chatpnl_conversations`, `chatpnl_messages` y `chatpnl_turns`; esta última vincula cada par pregunta/respuesta con las referencias guardadas y el identificador de envío. No edites hashes ni claves para preparar una captura.

Al terminar pulsa Ctrl+C en la terminal de Streamlit y después en la API. Detén MAMP o tu servicio LAMP propio cuando ya no lo necesites. Detener los procesos conserva las tablas. Para otro día reutiliza el entorno e inicia MySQL, API e interfaz en ese orden.

## Si algo no coincide

| Síntoma | Comprobación |
|---|---|
| API no arranca | MySQL encendido, usuario y puerto correctos, `.env` en la carpeta actual y clave JWT completa. |
| Formulario funciona pero chat da 404 | Comprueba que ejecutaste `backend:create_app`, la API integrada. |
| No hay entrada de chat | Inicia sesión y pulsa Nueva conversación. |
| HTTP 401 | Vuelve a iniciar sesión; no cambies el usuario MySQL para corregir un JWT vencido. |
| HTTP 409 al registrar | El usuario ya existe; inicia sesión o utiliza otro nombre ficticio. |
| Envío sin confirmar | Recupera la conexión y usa Reintentar envío con el mismo identificador. |
| Historial antiguo sin fuentes | Los mensajes previos a esta integración se conservan tal como se guardaron. |

La política de respuesta conserva el umbral 0.08 y su respaldo completo, sin recalibrar con pruebas publicadas. Las cuatro pruebas anteriores siguen retiradas. Consulta [el protocolo de evaluación](../../evaluacion_pnl/README.md) para preparar tus propios experimentos.
