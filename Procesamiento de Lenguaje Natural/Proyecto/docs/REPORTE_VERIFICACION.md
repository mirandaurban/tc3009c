# Verificación vigente de ChatPNL

## Presentación
52 diapositivas editables y PDF de 52 páginas, exportado localmente con Microsoft PowerPoint. Preparación en ocho pasos: comprobar Python, crear carpeta, crear/activar entorno, instalar, crear app.py, ejecutar y abrir el repositorio. Paleta #0039A6, blanco y negro según los lineamientos oficiales de marca Tec: https://bamboo.tec.mx/latest/foundations/lineamientos-de-marca-tec-l7luyCtI . Sin recuadros decorativos, iconos, notas ni comentarios del presentador. Texto visible: 6399 palabras. Portada con tema, materia, institución y Felipe Castillo Rendón. No hay páginas vacías, texto fuera de página ni invasión del pie en las comprobaciones. Revisión visual de contacto y muestras a resolución de lectura.

## Funcionamiento y experimentación
105 pruebas aprobadas, ninguna fallida ni omitida, con el motor MySQL de MAMP en una instancia temporal aislada. Python 3.11, macOS Apple Silicon, CPU. Se comprobaron imports y dependencias. NLTK 3.9.1 no requiere descargar corpus para el stemmer; requirements.txt y el lock se actualizaron.

Desarrollo de abstención: 60 casos (45/15), umbral 0.08 y política congelada antes de redactar otra prueba. Prueba final nueva de 20 casos (15/5): 15 respuestas válidas y 5 abstenciones correctas, 0 falsas abstenciones y 0 emisiones sin evidencia. Las cuatro pruebas anteriores permanecen retiradas. Regresión posterior de los tres fallos antiguos: los tres resueltos y cinco negativas aún rechazadas; no se usa para seleccionar parámetros.

La política intermedia dio 9/15 falsas abstenciones en un test retirado. El historial se conserva; el ajuste siguiente se realizó con desarrollo ampliado y la prueba final se redactó después de otra congelación. No se oculta ese ciclo ni se reutiliza como prueba independiente.

Clasificación de la demostración, test de 10 casos: F1 macro TF-IDF 0.394286, contextual 1.000000. Recuperación en los 15 respondibles nuevos: TF-IDF Recall@3 1.000000, MRR@5 1.000000; contextual Recall@3 1.000000, MRR@5 0.966667. Encoder ejecutado en CPU sin conexión usando el snapshot local. Datos y protocolo detallados en evaluacion_pnl/README.md.

## Límites
El corpus didáctico es pequeño y no satisface los mínimos de la TFG. La prueba nueva fue redactada por el mismo autor, sin auditoría externa, y ahora es pública. La normalización no prueba implicación lógica ni garantiza el comportamiento fuera de dominio. Para otro ciclo, reservar otra prueba. Windows y Linux tienen instrucciones revisadas, sin certificación de ejecución en esos sistemas. MySQL y APIs requieren servicios locales. El encoder debe prepararse antes; OCR no está implementado. El starter conserva TODO_ESTUDIANTE y no es una plataforma de producción. Las evaluaciones oficiales no cambian.


## Revisión paso a paso de los diez laboratorios
Los diez README incluyen comandos Windows PowerShell/macOS, recorridos numerados con resultados observables, fallos y cierre. Las guías de instalación, MySQL y modelo explican la preparación desde la carpeta de trabajo. Se aprobaron 20 comprobaciones de arranque y recorrido en macOS, incluidas APIs reales, MySQL aislado y MiniLM local sin conexión. Windows y Linux tienen revisión de instrucciones, sin ejecución certificada. La selección de conversaciones de L03 se corrigió y su regresión se amplió; los ejercicios del alumno siguen pendientes. El paquete se inspecciona también por contenido para excluir copias de funciones privadas. La política de abstención y sus particiones conservaron sus hashes; esta revisión no recalibró ni abrió otra prueba para seleccionar decisiones.


## Preparación local de MySQL
La práctica utiliza MAMP en macOS y Windows, y LAMP en Linux. Se explica cómo iniciar servicios, identificar el puerto MySQL, crear una base y cuenta de aplicación, completar .env y comprobar persistencia. Docker y Podman solo se mencionan como alternativas. La documentación parte de la carpeta actual del proyecto y los archivos PDF/TXT del recorrido acompañan los archivos iniciales del paquete.

Se comprobó el motor MySQL 8.0.35 incluido en MAMP para macOS mediante una instancia temporal independiente: creación de la base con el script incluido, conexión TCP desde la API, registro, lectura de identidad, aislamiento entre usuarios y persistencia después de reiniciar FastAPI. Las pruebas automatizadas específicas de MySQL pasaron. El panel MAMP y phpMyAdmin no se automatizaron; Windows y Linux mantienen revisión documental.


## Aplicación integrada de acceso, chat e historial
La entrada app.py reúne registro/login, selección de conversaciones y chat; backend.py expone una sola API. MySQL guarda preguntas, respuestas, abstenciones y fuentes en una transacción. La tabla adicional chatpnl_turns conserva los vínculos y el identificador de envío sin cambiar columnas ni borrar cuentas de L06.

Se comprobaron cierre y nuevo inicio de sesión, recuperación después de reiniciar la API y el motor MySQL, aislamiento entre dos cuentas, borrado confirmado y reintentos sin duplicados. Dos envíos simultáneos con el mismo identificador devuelven un solo par de mensajes. La interfaz se ejercitó con AppTest contra HTTP real; se simuló la pérdida del acuse después de una confirmación real para comprobar el reintento.

La batería completa pasó 105 pruebas, incluidas tres de MySQL. El paquete extraído se verifica por separado con las 102 pruebas sin servicio MySQL. Los resultados de abstención y modelos descritos arriba pertenecen al experimento congelado; esta integración no cambió la política ni recalibró con pruebas publicadas o retiradas. Documentos propios, intenciones, entidades y comparación integrada siguen como ejercicios pendientes.

## Ruta vigente de cinco semanas

Los diez laboratorios se cubren en cinco semanas de contenido, con revisión, entrega y defensa en la sexta. El calendario y los diez README identifican el núcleo semanal; la aplicación integrada se utiliza desde la semana 2. Dos bloques guiados de 60 min por semana y hasta 10 h autónomas estimadas reutilizan la integración del curso. No se asigna trabajo durante Semana Tec ni se cambian las evaluaciones oficiales. La planificación es una estimación docente, sin ensayo de duración con el grupo. Esta revisión de calendario no cambia el código, los datos ni los experimentos congelados; las pruebas funcionales citadas arriba corresponden a su validación previa.
