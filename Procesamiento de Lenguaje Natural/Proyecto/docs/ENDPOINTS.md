# Servicios disponibles

La aplicación integrada ofrece Swagger en `/docs`. Registro y login son públicos; las rutas de conversaciones y chat requieren `Authorization: Bearer TOKEN`. No registres contraseñas ni cabeceras de autorización en reportes.

| Método y ruta | Entrada | Resultado |
|---|---|---|
| GET /health | Sin token | status ok; no acredita por sí solo una consulta a MySQL. |
| POST /auth/register | username y password de al menos 10 caracteres | 201 id/username; 409 si ya existe. |
| POST /auth/login | username y password | access_token, token_type, expires_in; 401 si falla. |
| GET /auth/me | Bearer | id y username. |
| GET /conversations | Bearer | Solo conversaciones propias, más nuevas primero. |
| POST /conversations | Bearer y title | 201 con id y title. |
| PATCH /conversations/{cid} | Bearer y title | Conversación propia renombrada. |
| GET /conversations/{cid}/messages | Bearer | Mensajes propios en orden, con fuentes guardadas y abstención. |
| POST /conversations/{cid}/query | Bearer, text y request_id UUID | Respuesta y referencias persistidas junto a ambos mensajes. |
| DELETE /conversations/{cid} | Bearer | 204; elimina turnos, referencias y mensajes propios. |
| POST /conversations/{cid}/messages | Bearer y content | 201; conserva el ejemplo de mensaje de usuario de L06, sin generar respuesta. |

La interfaz genera un UUID nuevo por envío lógico. Un reintento conserva el UUID y el mismo texto: devuelve la respuesta guardada con `replayed: true`, sin duplicar el turno. Reutilizar ese UUID con otro texto produce 409. En un envío nuevo, `replayed` es false. La respuesta también contiene `user_message_id` y `assistant_message_id`.

`references` conserva identificador de fragmento, nombre de documento, página, texto, posición y score. `abstained: true` debe acompañarse de referencias vacías. Las fuentes históricas se leen de la base, no se recalculan. El score es similitud, no probabilidad.

HTTP 401 indica token ausente, inválido o vencido; 404 oculta tanto un recurso ajeno como uno inexistente; 422 señala un contrato inválido. El endpoint público `/api/v1/query` de la versión inicial ya no se ofrece. No hay carga privada de documentos en la API integrada.

El ejemplo separado de L05 conserva `/api/v1/echo` y `/api/v1/analyze`. No arranques esa API en lugar de la integrada para usar el chat.
