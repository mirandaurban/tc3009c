# Corpus sintético de soporte - preparación para clasificación

Origen: ejemplos originales del curso, sin personas reales. Uso educativo autorizado por el proyecto. No se descargó un corpus comercial.

Campos: id identifica la fila; family reúne variantes de una misma solicitud; split identifica train, validation o test; label es la categoría de referencia; text_original conserva la fuente; text_processed aplica NFC y reducción de espacios. Las categorías son acceso (autenticación/cuenta), pagos (cargos/documentos de pago), conectividad (red/internet) y software (aplicaciones/archivos). En mensajes con un problema resuelto y otro vigente se etiqueta el vigente. Una referencia sintética no resuelve toda ambigüedad real.

El modelo recibe solamente text_processed. id, family, split y label no se concatenan al texto ni se convierten en características. Las familias y particiones se fijaron antes de entrenar; no se cambian para aumentar métricas. Conservar acentos y negación no garantiza que el clasificador los interprete.

La limpieza de este archivo está preparada para centrar la práctica en representación y evaluación. No es una solución que el alumno deba copiar en Actividad 1. Los textos cortos, las categorías equilibradas y las variantes repetitivas limitan la generalización. Se necesitan datos independientes de uso real para estimarla.

Esta versión añade un corpus distinto para Actividad 2: 40 familias, tres variantes por familia y cuatro categorías. El reparto por categoría es seis familias train, dos validation y dos test. No sustituye ni modifica los datos compartidos anteriores.

Para reutilizar un corpus propio de A1, conserva su fuente y decisiones; utiliza su text_processed y particiones verificadas, con al menos dos categorías presentes en train y cobertura justificable en validation/test. No fuerces sus conteos ni categorías a coincidir con esta referencia; compara ambos modelos sobre el mismo corpus elegido. Consulta el enunciado.

En el ZIP, apoyos/ contiene las presentaciones y notebooks públicos de Clases 3–4; sus datos están en apoyos/data/. Abre esos notebooks desde apoyos/ para consultar y ejecutar las demostraciones.
