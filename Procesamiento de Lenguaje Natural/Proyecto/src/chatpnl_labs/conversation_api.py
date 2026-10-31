"""Respuesta documentada y persistencia atómica de cada turno privado."""
import json
from uuid import UUID
from fastapi import Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from . import core
from .auth_api import Message,ChatTurn

class ChatQuery(BaseModel):
    text:str=Field(min_length=1,max_length=2000,pattern=r"\S")
    request_id:UUID

def attach_chat(app,current,db,owned):
    # El índice contiene únicamente el corpus público de práctica, nunca historial privado.
    retriever=core.Retriever(core.corpus())
    @app.post("/conversations/{cid}/query")
    def query(cid:int,body:ChatQuery,user=Depends(current),session=Depends(db)):
        # En MySQL el bloqueo serializa turnos y evita intercalar dos pares de mensajes.
        owned(cid,user,session,lock=True)
        request_id=str(body.request_id)
        previous=session.scalar(select(ChatTurn).where(ChatTurn.conversation_id==cid,ChatTurn.request_id==request_id).with_for_update())
        if previous is not None:
            # La autenticación pudo abrir una instantánea anterior al turno concurrente.
            # Leer también el mensaje con bloqueo obtiene la versión recién confirmada.
            original=session.scalar(select(Message).where(Message.id==previous.user_message_id).with_for_update())
            if original.content!=body.text:
                raise HTTPException(409,"El identificador de envío ya tiene otro texto")
            return {**json.loads(previous.response_json),"user_message_id":previous.user_message_id,
                    "assistant_message_id":previous.assistant_message_id,"replayed":True}
        # Se conserva la política congelada: no se ajusta con el historial ni con test.
        result=core.answer(body.text,retriever)
        serialized=json.dumps(result,ensure_ascii=False)
        question=Message(conversation_id=cid,role="user",content=body.text)
        session.add(question);session.flush()
        reply=Message(conversation_id=cid,role="assistant",content=result["answer"])
        session.add(reply);session.flush()
        session.add(ChatTurn(conversation_id=cid,request_id=request_id,user_message_id=question.id,
                             assistant_message_id=reply.id,response_json=serialized))
        # Una sola confirmación: pregunta, respuesta y referencias se guardan juntas.
        question_id,reply_id=question.id,reply.id
        session.commit()
        return {**result,"user_message_id":question_id,"assistant_message_id":reply_id,"replayed":False}
