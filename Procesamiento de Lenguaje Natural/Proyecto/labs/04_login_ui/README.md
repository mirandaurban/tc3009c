# Laboratorio formativo Streamlit 04: Formularios de acceso

## 1. Comprender el recorrido

Entender la estructura de una pantalla de registro y entrada antes de conectar autenticación real. La entrada es un alias ficticio y una confirmación; la salida es una vista condicional. Esta demo no valida identidades, no registra cuentas y no solicita contraseñas.

## 2. Preparar la carpeta y el entorno

Primero completa los pasos 1 y 2 de [GUIA_INSTALACION.md](../../docs/GUIA_INSTALACION.md). Si ya los hiciste, reutiliza `.venv`; no la vuelvas a crear. Abre la carpeta que contiene `requirements.txt` y `labs/`, no esta subcarpeta del laboratorio. Los comandos de abajo se ejecutan desde esa raíz y seleccionan directamente el Python del entorno, sin depender de su activación.

Antes de cambiar de laboratorio, detén la app anterior con Ctrl+C para liberar el puerto 8501. No necesitas haber resuelto los ejercicios de las prácticas anteriores para ejecutar esta demostración.

Abre `labs/04_login_ui/app.py` en el editor para leerlo mientras observas la aplicación. Conserva los comentarios `TODO_ESTUDIANTE`: indican el trabajo que aún debes realizar.

## 3. Encender la aplicación

Usa una terminal en la raíz del proyecto.

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe -m streamlit run labs/04_login_ui/app.py --server.address 127.0.0.1 --server.port 8501
```

macOS:
```sh
.venv/bin/python -m streamlit run labs/04_login_ui/app.py --server.address 127.0.0.1 --server.port 8501
```

Resultado esperado: el proceso permanece encendido y muestra la dirección local. Abre `http://127.0.0.1:8501` en el navegador. Si solicita un correo opcional, puedes pulsar Enter sin escribirlo. No pegues estos comandos en la barra de direcciones.

## 4. Seguir los pasos y contrastar resultados

1. Lee el aviso “SIMULACIÓN NO SEGURA”. Usa exclusivamente un alias inventado; la pantalla no debe pedir contraseña.
2. En “Registro de demostración”, escribe `ab`, deja sin marcar la confirmación y pulsa “Continuar”. Debe aparecer “Escribe al menos tres caracteres y confirma la simulación”. El aviso permanente también seguirá visible.
3. Escribe `alumno_demo`, marca “Comprendo que solo simula la interfaz” y pulsa “Continuar”. Debe mostrarse “Vista privada simulada para alumno_demo”.
4. Pulsa “Cerrar sesión”. Debe volver el formulario. Cambia “Vista” a “Entrada de demostración” y repite con otro alias de tres o más caracteres y la confirmación marcada.
5. Observa que ambos modos aceptan un alias nuevo sin consultar cuentas. Explica por qué el nombre “Entrada” no convierte esta vista en autenticación. Ocultar un panel tampoco autoriza una solicitud de API.
6. Localiza `demo_user` y su eliminación en `app.py`. La autenticación real se introduce en L06; los ejercicios aquí cambian únicamente la interfaz de demostración.

## 5. Resolver los ejercicios del alumno

La demostración anterior permite comprobar la instalación y comprender el flujo. Los ejercicios siguientes quedan pendientes y no incluyen su solución. Trabaja sobre tu copia, conserva los comentarios útiles y explica tus decisiones.

1. Validar alias alfanumérico.
2. Dar mensajes específicos por cada error.
3. Proteger visualmente otra sección de demostración.

## 6. Registrar la evidencia y cerrar

Registra la entrada utilizada, los pasos realizados y la salida realmente observada. Incluye al menos un caso válido y un caso inválido o una condición de fallo del recorrido. Escribe qué esperabas y si coincidió; una captura sin explicación no acredita el funcionamiento. Usa datos ficticios y omite contraseñas, tokens y archivos privados.

¿Qué comprobación tendría que hacer un servidor antes de entregar datos privados? Explica por qué una sección oculta en Streamlit no basta.

Pulsa Ctrl+C en la terminal de Streamlit. Para volver a abrir, usa los mismos comandos; no reinstales dependencias en cada sesión.

## Si algo no coincide

Una entrada rechazada puede deberse al alias corto o a la casilla sin marcar. La demo todavía no diferencia ambos mensajes; esa mejora es tu ejercicio. Un alias aceptado no acredita identidad.
