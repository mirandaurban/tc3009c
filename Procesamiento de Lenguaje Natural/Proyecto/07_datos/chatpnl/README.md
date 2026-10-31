# Datos didácticos ChatPNL
Dominio original ficticio: biblioteca Aurora. CC0-1.0 para estos datos originales. Los cuatro TXT y el PDF de ejemplo no satisfacen el corpus mínimo del proyecto final.

Intenciones: cinco clases, train 30, validation 10 y test 10; no seleccionar C con test. Entidades: ocho ejemplos de anotación con offsets, baseline de reglas, no validación de generalización.

Recuperación vigente: desarrollo 60 consultas (45 respondibles y 15 sin evidencia); prueba nueva recuperacion_prueba_final.json, 20 consultas (15/5), creada DESPUÉS de congelar política y código. Registro de roles en particiones_recuperacion.json. Las cuatro pruebas anteriores permanecen retiradas: recuperacion_test.json, recuperacion_prueba_reservada.json, recuperacion_prueba_confirmacion.json y recuperacion_prueba_validacion.json. No seleccionar reglas ni umbrales con ellas.

La prueba nueva es pública después de su ejecución. Otra modificación requiere otra reserva. Fue redactada por el mismo autor tras congelar, no por un auditor independiente. El evaluador comprueba duplicados de la prueba nueva contra desarrollo y todas las retiradas.

Mínimos de TFG: 10 documentos, 5,000 palabras útiles; cuatro intenciones más fuera de alcance, al menos 25 ejemplos por intención; 40 textos NER; 20 consultas de desarrollo y 20 de prueba, cada partición con 15 respondibles y 5 sin evidencia. No dividir chunks solapados del mismo documento entre train y test. Conservar procedencia, IDs y autorización de los datos.
