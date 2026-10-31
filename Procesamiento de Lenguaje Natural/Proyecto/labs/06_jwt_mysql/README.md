# Laboratorio formativo Streamlit 06: JWT y MySQL

## 1. Comprender el recorrido

Seguir el registro, la verificación de contraseña y el acceso a conversaciones privadas. FastAPI guarda usuarios en MySQL y entrega un JWT al iniciar sesión. JWT es un token firmado con vencimiento; no es una contraseña cifrada. Necesitas MySQL y dos procesos de Python.

## 2. Preparar la carpeta y el entorno

Primero completa los pasos 1 y 2 de [GUIA_INSTALACION.md](../../docs/GUIA_INSTALACION.md). Si ya los hiciste, reutiliza `.venv`; no la vuelvas a crear. Abre la carpeta que contiene `requirements.txt` y `labs/`, no esta subcarpeta del laboratorio. Los comandos de abajo se ejecutan desde esa raíz y seleccionan directamente el Python del entorno, sin depender de su activación.

Antes de cambiar de laboratorio, detén la app anterior con Ctrl+C para liberar el puerto 8501. No necesitas haber resuelto los ejercicios de las prácticas anteriores para ejecutar esta demostración.

Antes de arrancar, completa [MYSQL.md](../../docs/MYSQL.md): crea una base de práctica, configura `.env` y comprueba que MySQL está disponible. No arranques la API con `REEMPLAZAR` ni con una clave JWT vacía. En macOS y Windows utiliza MAMP; en Linux, LAMP. Verifica el puerto de MySQL en tu instalación: MAMP suele usar 8889 y LAMP suele usar 3306. No lo confundas con el puerto web de Apache.

## 3. Encender la aplicación

### Terminal 1: FastAPI

Abre una terminal en la raíz y ejecuta el bloque de tu sistema. Déjala abierta hasta terminar.

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m uvicorn chatpnl_labs.auth_api:create_app --factory --host 127.0.0.1 --port 8000
```

macOS:
```sh
.venv/bin/python -m uvicorn chatpnl_labs.auth_api:create_app --factory --host 127.0.0.1 --port 8000
```

Resultado esperado: `Application startup complete`. La API escucha en `http://127.0.0.1:8000`; el navegador de la interfaz usará otro puerto.

### Terminal 2: Streamlit

Abre otra terminal en la misma raíz.

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m streamlit run labs/06_jwt_mysql/app.py --server.address 127.0.0.1 --server.port 8501
```

macOS:
```sh
.venv/bin/python -m streamlit run labs/06_jwt_mysql/app.py --server.address 127.0.0.1 --server.port 8501
```

Resultado esperado: el proceso permanece encendido y muestra la dirección local. Abre `http://127.0.0.1:8501` en el navegador. Si solicita un correo opcional, puedes pulsar Enter sin escribirlo. No pegues estos comandos en la barra de direcciones.

Si se presentan errores:

cp -n .env.example .env
.venv/bin/python -c "import secrets; print(secrets.token_hex(32))"

Abre .env en tu editor y completa:
CHATPNL_DATABASE_URL=mysql+pymysql://chatpnl:root@127.0.0.1:8889/chatpnl?charset=utf8mb4
CHATPNL_JWT_SECRET=2276714daa4ef9e2bc3296844e5fde48a4ad403a1cac6290ebae9dbd8664f51b
CHATPNL_API_URL=http://127.0.0.1:8000

.venv/bin/python -m streamlit run labs/06_jwt_mysql/app.py --server.address 127.0.0.1 --server.port 8501

.venv/bin/python -m uvicorn chatpnl_labs.simple_api:app --host 127.0.0.1 --port 8000

## 4. Seguir los pasos y contrastar resultados

1. En `/docs` deben aparecer `/auth/register`, `/auth/login`, `/auth/me` y `/conversations`. En Streamlit elige “Registrar usuario”. Usa un usuario ficticio nuevo, por ejemplo `alumno_a_20`, y una contraseña de práctica propia de al menos 10 caracteres. No uses datos ni contraseñas de otras cuentas.
2. Pulsa “Enviar”. Debe aparecer “Usuario creado. Ahora inicia sesión.” Repetir exactamente el mismo usuario debe dar HTTP 409; una contraseña demasiado corta debe dar 422. El formulario se limpia después del envío: vuelve a escribir ambos campos cuando corresponda.
3. Selecciona “Iniciar sesión”, introduce la cuenta recién creada y envía. Deben aparecer “Identidad confirmada por FastAPI” y los campos públicos de `/auth/me`, sin la contraseña ni su hash. No copies el token en capturas.
4. En “Título de conversación privada de práctica” escribe `Consulta A` y pulsa “Crear conversación”. Debe aparecer en la lista con su identificador y título. Esa operación comprueba una escritura y lectura reales de MySQL.
5. Cierra sesión, registra un segundo usuario ficticio nuevo e inicia sesión con él. Su lista debe estar vacía; crea `Consulta B`. Vuelve al usuario A: debe ver A y no B. La prueba de leer directamente el identificador ajeno queda como ejercicio para comprobar la autorización de la API, además del filtrado de la interfaz.
6. Detén y vuelve a arrancar únicamente FastAPI, conservando MySQL y `.env`. Vuelve a entrar como A si hace falta: `Consulta A` debe seguir guardada. Esto distingue persistencia de una lista temporal de Streamlit.
7. Cierra sesión al terminar. La app elimina su copia local del JWT, pero el token emitido sigue siendo válido hasta su vencimiento de 15 minutos. No afirmes revocación por cerrar sesión. Una contraseña incorrecta en un nuevo intento de entrada debe producir HTTP 401.

## 5. Resolver los ejercicios del alumno

La demostración anterior permite comprobar la instalación y comprender el flujo. Los ejercicios siguientes quedan pendientes y no incluyen su solución. Trabaja sobre tu copia, conserva los comentarios útiles y explica tus decisiones.

1. Diseñar otra vista de /auth/me.
2. Probar expiración y ofrecer reingreso.
3. Demostrar rechazo sin token y entre dos usuarios.

## 6. Registrar la evidencia y cerrar

Registra la entrada utilizada, los pasos realizados y la salida realmente observada. Incluye al menos un caso válido y un caso inválido o una condición de fallo del recorrido. Escribe qué esperabas y si coincidió; una captura sin explicación no acredita el funcionamiento. Usa datos ficticios y omite contraseñas, tokens y archivos privados.

Distingue contraseña, hash y token. Explica cómo verificaste persistencia y separación de propietarios, y qué prueba directa de autorización aún falta.

Pulsa Ctrl+C en la terminal de Streamlit. Después pulsa Ctrl+C en la terminal de FastAPI. Detén los servicios de práctica desde MAMP o según el procedimiento LAMP de MYSQL.md; las cuentas y tablas se conservan. Para volver a abrir, usa los mismos comandos; no reinstales dependencias en cada sesión.

## Si algo no coincide

“Access denied” de MySQL: verifica usuario, contraseña, host y puerto en `.env`; no pegues la URL en un reporte. Fallo al arrancar JWT: comprueba la clave de al menos 32 bytes. HTTP 409: utiliza un usuario nuevo. HTTP 401: vuelve a iniciar sesión; comprueba que la contraseña de práctica coincide.
