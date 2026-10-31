# MySQL con MAMP en macOS y Windows, o LAMP en Linux

## 1. Qué función cumple cada herramienta

MAMP reúne un servidor web, MySQL y PHP para trabajar localmente. En esta práctica usamos su MySQL y su herramienta phpMyAdmin para preparar la base. Streamlit y FastAPI siguen ejecutándose con Python desde la carpeta actual. No copies el proyecto a `htdocs`: Apache no ejecuta una aplicación Streamlit.

En Linux utilizaremos LAMP, la combinación de Linux, Apache, MySQL y PHP. Las instrucciones de instalación de abajo corresponden a Ubuntu; en otra distribución utiliza sus paquetes equivalentes. Docker y Podman son alternativas para administrar contenedores; aquí solo se mencionan y no forman parte de la práctica.

Completa antes la instalación de Python del proyecto. Necesitas una base nueva de práctica, sin datos personales. El usuario de MySQL conecta la API con la base; los usuarios del chat se registran después desde el formulario. Son cuentas diferentes.

## 2. Preparar MAMP en macOS

1. Descarga MAMP desde [su sitio oficial](https://www.mamp.info/en/downloads/), elige macOS e instala la versión compatible con tu equipo. Abre MAMP; para la práctica no se requiere MAMP PRO.
2. Abre los ajustes de puertos, normalmente “Settings” y “Ports”. Anota el puerto **MySQL** que aparece. La configuración predeterminada documentada usa 8889 para MySQL y 8888 para el servidor web. Si tu instalación tiene otros valores, utilizarás los que muestra tu pantalla.
3. Pulsa “Start” o “Start Servers”, según tu versión, y espera a que los servicios indiquen que están encendidos. Si otro programa ocupa el puerto, identifica ese programa o configura un puerto libre; no detengas un servicio compartido.
4. Pulsa “WebStart” y abre “Tools” y “phpMyAdmin”. WebStart utiliza el puerto del servidor web, mientras que Python se conectará al puerto de MySQL. Confundir 8888 con 8889 provoca una conexión al servicio equivocado.
5. Si phpMyAdmin solicita autenticación, utiliza la cuenta administradora local de tu instalación de MAMP. No presupongas que conserva una contraseña predeterminada. Esa cuenta se usa para preparar la base, no se pondrá en la API.

Resultado esperado: puedes abrir phpMyAdmin y ver el servidor de bases de datos. Todavía no es necesario que existan tablas del proyecto. Referencias de los pasos y puertos: [interfaz de MAMP](https://documentation.mamp.info/en/MAMP-Mac/Reference/Interface/), [configuración de puertos](https://documentation.mamp.info/en/MAMP-Mac/Reference/Settings/Ports/) y [WebStart](https://documentation.mamp.info/en/MAMP-Mac/WebStart/).

## 3. Preparar MAMP en Windows

1. Descarga el instalador para Windows desde [MAMP](https://www.mamp.info/en/downloads/). Sigue el instalador y abre **MAMP**; no necesitas contratar PRO. Mantén el proyecto Python en tu carpeta de trabajo.
2. Abre “Preferences” y “Ports”, o el apartado equivalente de tu versión. Anota el puerto de MySQL. La documentación de MAMP para Windows indica 8889 para MySQL y 8888 para Apache como valores predeterminados; verifica los de tu instalación.
3. Pulsa “Launch Servers” o “Start Servers”. Espera la confirmación de que los servicios están activos. Si Windows solicita permisos de inicio para el programa instalado, revisa que correspondan a MAMP.
4. Abre “Open WebStart Page” y después “Tools” y “phpMyAdmin”. Si el navegador no abre la página, comprueba primero el estado de Apache y su puerto. No cambies todavía el código de Streamlit.
5. Accede con la cuenta administradora local si se solicita. Guarda el puerto MySQL para el paso 6 y continúa con la creación de la base.

Resultado esperado: phpMyAdmin muestra la conexión al servidor de MAMP. El puerto web no se utiliza en la URL de SQLAlchemy. Consulta [instalación oficial en Windows](https://documentation.mamp.info/en/MAMP-Windows/Installation/) y [primer arranque](https://documentation.mamp.info/en/MAMP-Windows/First-Steps/).

## 4. Crear la base y una cuenta para la aplicación

Este paso es común a macOS y Windows. En phpMyAdmin, abre la pestaña **SQL** del servidor. En el editor del proyecto abre `scripts/init_mysql.sql`. Sustituye `REEMPLAZAR_LOCALMENTE` por una contraseña nueva de práctica y ejecuta el contenido en esa pestaña SQL. La contraseña debe ser distinta de la administradora. Usa una copia local que no publiques; no incluyas credenciales en capturas.

Antes de ejecutar, identifica las operaciones del archivo: crear la base `chatpnl`, crear el usuario `chatpnl` para conexión local y conceder permisos solamente sobre esa base. No se concede acceso a las demás bases del equipo. La API creará sus tablas cuando arranque, por eso la cuenta necesita permiso CREATE en este ejemplo.

Resultado esperado: phpMyAdmin confirma las sentencias y aparece la base `chatpnl`. Si todavía no hay tablas, es normal: se crean al iniciar FastAPI. No uses la cuenta administradora para evitar un error de permisos.

Si el usuario `chatpnl` ya existía, `CREATE USER IF NOT EXISTS` no modifica su contraseña. Revisa la cuenta de práctica en “User accounts” o “Cuentas de usuario”; no cambies usuarios de otras materias. La contraseña que configures después en `.env` debe coincidir con esa cuenta.

## 5. Si usas Linux: preparar LAMP

En Ubuntu, abre una terminal y ejecuta las líneas siguientes. Estos comandos instalan servicios del sistema y solicitan la contraseña de tu cuenta con permisos de administración. Si LAMP ya está preparado por el profesor, comprueba su estado en lugar de reinstalarlo.

```sh
sudo apt update
sudo apt install apache2 mysql-server php libapache2-mod-php php-mysql
sudo systemctl start apache2 mysql
systemctl is-active apache2 mysql
sudo mysql
```

Resultado esperado: se muestra `active` para ambos servicios y el último comando abre el indicador `mysql>`. Apache y PHP completan LAMP; la aplicación de Python se ejecuta en sus propios procesos. No es necesario instalar phpMyAdmin en Linux para realizar esta práctica.

Abre el mismo `scripts/init_mysql.sql` en el editor, sustituye la contraseña en una copia privada y pega sus sentencias dentro de `mysql>`. Deben terminar sin errores. Después ejecuta:

```sql
SHOW DATABASES LIKE 'chatpnl';
SHOW VARIABLES LIKE 'port';
exit;
```

La primera consulta debe mostrar la base y la segunda indica el puerto real, habitualmente 3306. Anótalo para `.env`. No cambies el acceso del administrador por socket de Ubuntu para hacer funcionar la API: utiliza la cuenta de aplicación recién creada.

Referencias: [Apache en Ubuntu](https://ubuntu.com/server/docs/how-to/web-services/install-apache2/), [MySQL en Ubuntu](https://ubuntu.com/server/docs/how-to/databases/install-mysql/) y [PHP en Ubuntu](https://ubuntu.com/server/docs/programming-php/). En otras distribuciones, los nombres de paquetes, servicios y método de administración pueden variar; estas líneas de `apt` no son universales.

## 6. Conectar el proyecto con la base

Vuelve a la carpeta actual del proyecto, donde están `requirements.txt` y `.env.example`. Crea `.env` solamente si no existe: volver a copiar el ejemplo sobrescribe tus ajustes. Abre ese archivo en el editor después de copiarlo.

Windows PowerShell:
```powershell
Copy-Item .env.example .env
.\.venv\Scripts\python.exe scripts/new_secret.py
```

macOS y Linux:
```sh
cp .env.example .env
.venv/bin/python scripts/new_secret.py
```

El segundo comando imprime una clave aleatoria. Copia su salida completa solamente al campo `CHATPNL_JWT_SECRET` de `.env`. No la publiques. Esta clave firma los JWT y debe conservarse entre reinicios; cambiarla invalida tokens anteriores.

Completa la configuración local:

```dotenv
CHATPNL_DATABASE_URL=mysql+pymysql://chatpnl:REEMPLAZAR@127.0.0.1:8889/chatpnl?charset=utf8mb4
CHATPNL_JWT_SECRET=PEGAR_AQUI_LA_CLAVE_GENERADA
CHATPNL_API_URL=http://127.0.0.1:8000
CHATPNL_MODEL_PATH=
```

Reemplaza `REEMPLAZAR` por la contraseña de la cuenta MySQL `chatpnl`. El ejemplo utiliza 8889, habitual en MAMP; en Linux o en una instalación diferente escribe el puerto que verificaste. `127.0.0.1` fuerza conexión local TCP y evita depender de la ubicación del socket de MAMP. No uses `http://` en esta URL: `mysql+pymysql` identifica la base y su controlador de Python.

Si la contraseña tiene caracteres reservados de una URL, codifica solo esa parte; por ejemplo `@` se escribe `%40`. Para esta práctica puedes generar una contraseña larga con letras y números para simplificar la escritura. Guarda `.env` sin añadirlo a Git, al ZIP ni al reporte. Los valores escritos arriba son marcadores, no credenciales listas para usar.

## 7. Arrancar FastAPI y Streamlit

La aplicación integrada utiliza la misma API para registro, login, historial y respuestas. Trabaja desde la carpeta actual del proyecto. Primero enciende MySQL con MAMP o LAMP, después inicia estos dos procesos.

macOS y Linux, terminal 1:
```sh
.venv/bin/python -m uvicorn backend:create_app --factory --host 127.0.0.1 --port 8000
```

macOS y Linux, terminal 2:
```sh
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Windows PowerShell, terminal 1:
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend:create_app --factory --host 127.0.0.1 --port 8000
```

Windows PowerShell, terminal 2:
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Espera `Application startup complete` en la API. Abre `http://127.0.0.1:8501`, registra una cuenta de práctica, inicia sesión y pulsa Nueva conversación. Envía `cuántos libros puedo pedir` y comprueba la fuente. Después prueba `¿Cuál es el precio de una laptop?`: debe abstenerse sin fuentes.

En phpMyAdmin actualiza la base: deben aparecer `chatpnl_users`, `chatpnl_conversations`, `chatpnl_messages` y la nueva `chatpnl_turns`. Esta última guarda los vínculos del turno, su identificador de envío y la respuesta con referencias. No muestres hashes de contraseñas ni tokens en la evidencia.

Cierra sesión y vuelve a entrar: deben recuperarse los mensajes y las citas. Después detén únicamente FastAPI, reinícialo con el mismo comando y actualiza el historial. La conversación debe seguir guardada. `/health` por sí solo no acredita esa persistencia.

Si ya tenías la base de L06, conserva sus datos y su cuenta. Se añade la tabla de turnos al arrancar, sin cambiar las columnas de las tablas anteriores. Los mensajes antiguos sin fuentes se muestran como estaban. El archivo SQLite de eventos de la versión inicial del starter ya no se utiliza; no contenía un historial que importar.

El [recorrido de L10](../labs/10_chatpnl_starter/README.md) detalla renombrado, borrado con confirmación, aislamiento entre cuentas y reintentos. L06 sigue disponible como ejemplo independiente de autenticación, pero no necesitas abrirlo para utilizar la aplicación integrada.

## 8. Terminar y corregir problemas

Detén Streamlit y FastAPI con Ctrl+C en sus terminales. En macOS y Windows, pulsa “Stop” o “Stop Servers” en MAMP cuando hayas terminado de utilizarlo. Detener servicios no borra las cuentas ni las tablas. En Linux, si son servicios propios de práctica y ningún otro trabajo los necesita, puedes detenerlos con `sudo systemctl stop apache2 mysql`.

| Problema | Qué revisar |
|---|---|
| phpMyAdmin no abre | Estado y puerto del servidor web de MAMP. |
| FastAPI no conecta a MySQL | MySQL encendido, puerto de MySQL y URL de `.env`; no confundir 8888 con 8889. |
| `Access denied` | Cuenta `chatpnl`, contraseña, permisos sobre su base y acceso local; no sustituir por root. |
| No aparecen tablas | Confirma que FastAPI terminó el arranque con esa base configurada. |
| Sigue un puerto o secreto anterior | Reinicia la API después de cambiar `.env` y revisa variables ya definidas en la terminal. |
| HTTP 401 | Vuelve a iniciar sesión; un token vencido no indica que MySQL haya perdido datos. |

## Prueba adicional de integración

Para las pruebas automatizadas utiliza **otra base vacía**, por ejemplo `chatpnl_test`, y una cuenta con permisos únicamente sobre esa base. No uses la base del recorrido para esta prueba. Ajusta el puerto, usuario y contraseña del ejemplo localmente.

Windows PowerShell:
```powershell
$env:CHATPNL_TEST_MYSQL_URL='mysql+pymysql://USUARIO_PRUEBAS:CLAVE_LOCAL@127.0.0.1:8889/chatpnl_test'
.\.venv\Scripts\python.exe -m pytest -q -m mysql
Remove-Item Env:CHATPNL_TEST_MYSQL_URL
```

macOS y Linux:
```sh
export CHATPNL_TEST_MYSQL_URL='mysql+pymysql://USUARIO_PRUEBAS:CLAVE_LOCAL@127.0.0.1:8889/chatpnl_test'
.venv/bin/python -m pytest -q -m mysql
unset CHATPNL_TEST_MYSQL_URL
```

Resultado esperado con la base de pruebas preparada: pytest informa que la prueba MySQL pasó. Si falta la variable, la omite; una omisión no confirma MySQL. Las pruebas con SQLite comprueban lógica, pero no el servicio MySQL. La documentación de Windows y Linux se revisa por sus fuentes oficiales; no se afirma una ejecución en esos sistemas.
