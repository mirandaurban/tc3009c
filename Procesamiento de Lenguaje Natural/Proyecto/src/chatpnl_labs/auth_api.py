"""Autenticación real del L06. Crear tablas es didáctico; producción requiere migraciones."""
import os
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.low_level import Type
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, ForeignKey, Text, UniqueConstraint, select, event, delete as sql_delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__="chatpnl_users"
    id:Mapped[int]=mapped_column(primary_key=True)
    username:Mapped[str]=mapped_column(String(60),unique=True)
    password_hash:Mapped[str]=mapped_column(String(255))
class Conversation(Base):
    __tablename__="chatpnl_conversations"
    id:Mapped[int]=mapped_column(primary_key=True)
    owner_id:Mapped[int]=mapped_column(ForeignKey("chatpnl_users.id"),index=True)
    title:Mapped[str]=mapped_column(String(120))
class Message(Base):
    __tablename__="chatpnl_messages"
    id:Mapped[int]=mapped_column(primary_key=True)
    conversation_id:Mapped[int]=mapped_column(ForeignKey("chatpnl_conversations.id"),index=True)
    role:Mapped[str]=mapped_column(String(16))
    content:Mapped[str]=mapped_column(Text)
class ChatTurn(Base):
    # Tabla adicional: conserva las tablas existentes de L06 sin alterar sus columnas.
    __tablename__="chatpnl_turns"
    __table_args__=(UniqueConstraint("conversation_id","request_id",name="uq_chatpnl_turn_request"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    conversation_id:Mapped[int]=mapped_column(ForeignKey("chatpnl_conversations.id"),index=True)
    request_id:Mapped[str]=mapped_column(String(36))
    user_message_id:Mapped[int]=mapped_column(ForeignKey("chatpnl_messages.id"))
    assistant_message_id:Mapped[int]=mapped_column(ForeignKey("chatpnl_messages.id"),unique=True)
    response_json:Mapped[str]=mapped_column(Text)

class Document(Base):
    __tablename__="chatpnl_documents"
    id:Mapped[int]=mapped_column(primary_key=True)
    owner_id:Mapped[int]=mapped_column(ForeignKey("chatpnl_users.id"),index=True)
    source:Mapped[str]=mapped_column(String(255))
    # TODO_ESTUDIANTE: persistir texto/fragmentos con páginas y autorizar cada acceso.

class Credentials(BaseModel):
    username:str=Field(min_length=3,max_length=60,pattern=r"^[a-z0-9_]+$")
    password:str=Field(min_length=10,max_length=128)
class ConversationInput(BaseModel):
    title:str=Field(min_length=1,max_length=120,pattern=r"\S")
class MessageInput(BaseModel):
    content:str=Field(min_length=1,max_length=2000,pattern=r"\S")

def issue_token(user_id,secret,minutes=15):
    now=datetime.now(timezone.utc)
    return jwt.encode({"sub":str(user_id),"iat":now,"exp":now+timedelta(minutes=minutes),"iss":"chatpnl-lab","aud":"chatpnl-ui"},secret,algorithm="HS256")

def create_app(database_url=None, secret=None, *, with_chat=False):
    load_dotenv(".env")
    database_url=database_url or os.environ.get("CHATPNL_DATABASE_URL")
    secret=secret or os.environ.get("CHATPNL_JWT_SECRET","")
    if not database_url or len(secret.encode())<32 or len(set(secret))<10:
        raise RuntimeError("Configure base de datos y clave aleatoria de al menos 32 bytes en .env")
    engine=create_engine(database_url,pool_pre_ping=True,hide_parameters=True,connect_args={"check_same_thread":False} if database_url.startswith("sqlite") else {})
    if database_url.startswith("sqlite"):
        @event.listens_for(engine,"connect")
        def enable_foreign_keys(connection,record):
            connection.execute("PRAGMA foreign_keys=ON")
    Session=sessionmaker(engine)
    hasher=PasswordHasher(type=Type.ID)
    bearer=HTTPBearer(auto_error=False)
    @asynccontextmanager
    async def lifespan(app):
        Base.metadata.create_all(engine)
        yield
        engine.dispose()
    app=FastAPI(title="ChatPNL · autenticación",lifespan=lifespan)
    app.state.engine=engine
    def db():
        with Session() as session: yield session
    def current(auth:HTTPAuthorizationCredentials|None=Depends(bearer),session=Depends(db)):
        try:
            if not auth: raise ValueError()
            claims=jwt.decode(auth.credentials,secret,algorithms=["HS256"],issuer="chatpnl-lab",audience="chatpnl-ui",options={"require":["exp","sub","iat","iss","aud"]})
            user=session.get(User,int(claims["sub"]))
            if not user: raise ValueError()
            return user
        except (jwt.InvalidTokenError,ValueError,TypeError):
            raise HTTPException(401,"Token inválido o expirado",headers={"WWW-Authenticate":"Bearer"})
    def owned(cid,user,session,*,lock=False):
        statement=select(Conversation).where(Conversation.id==cid,Conversation.owner_id==user.id)
        if lock: statement=statement.with_for_update()
        item=session.scalar(statement)
        if item is None: raise HTTPException(404,"Recurso no disponible")
        return item
    @app.get("/health")
    def health(): return {"status":"ok"}
    @app.post("/auth/register",status_code=201)
    def register(body:Credentials,session=Depends(db)):
        user=User(username=body.username,password_hash=hasher.hash(body.password))
        session.add(user)
        try: session.commit()
        except IntegrityError:
            session.rollback(); raise HTTPException(409,"Usuario existente")
        return {"id":user.id,"username":user.username}
    @app.post("/auth/login")
    def login(body:Credentials,session=Depends(db)):
        user=session.scalar(select(User).where(User.username==body.username))
        try:
            if user is None: raise ValueError()
            hasher.verify(user.password_hash,body.password)
        except (VerificationError,InvalidHashError,ValueError):
            raise HTTPException(401,"Credenciales inválidas")
        return {"access_token":issue_token(user.id,secret),"token_type":"bearer","expires_in":900}
    @app.get("/auth/me")
    def me(user=Depends(current)): return {"id":user.id,"username":user.username}
    @app.get("/conversations")
    def conversations(user=Depends(current),session=Depends(db)):
        return [{"id":c.id,"title":c.title} for c in session.scalars(select(Conversation).where(Conversation.owner_id==user.id).order_by(Conversation.id.desc()))]
    @app.post("/conversations",status_code=201)
    def create(body:ConversationInput,user=Depends(current),session=Depends(db)):
        item=Conversation(owner_id=user.id,title=body.title);session.add(item);session.commit()
        return {"id":item.id,"title":item.title}
    @app.get("/conversations/{cid}/messages")
    def messages(cid:int,user=Depends(current),session=Depends(db)):
        owned(cid,user,session)
        saved={turn.assistant_message_id:json.loads(turn.response_json) for turn in session.scalars(select(ChatTurn).where(ChatTurn.conversation_id==cid))}
        return [{"id":m.id,"role":m.role,"content":m.content,
                 "references":saved.get(m.id,{}).get("references",[]),
                 "abstained":saved.get(m.id,{}).get("abstained")}
                for m in session.scalars(select(Message).where(Message.conversation_id==cid).order_by(Message.id))]
    @app.post("/conversations/{cid}/messages",status_code=201)
    def add_message(cid:int,body:MessageInput,user=Depends(current),session=Depends(db)):
        owned(cid,user,session,lock=True)
        m=Message(conversation_id=cid,role="user",content=body.content);session.add(m);session.commit()
        return {"id":m.id,"role":m.role,"content":m.content}
    @app.patch("/conversations/{cid}")
    def rename(cid:int,body:ConversationInput,user=Depends(current),session=Depends(db)):
        item=owned(cid,user,session,lock=True)
        item.title=body.title;session.commit()
        return {"id":item.id,"title":item.title}
    @app.delete("/conversations/{cid}",status_code=204)
    def delete(cid:int,user=Depends(current),session=Depends(db)):
        item=owned(cid,user,session,lock=True)
        session.execute(sql_delete(ChatTurn).where(ChatTurn.conversation_id==cid))
        # Borrado explícito en orden de dependencias, también con claves foráneas activas.
        session.execute(sql_delete(Message).where(Message.conversation_id==cid))
        session.delete(item);session.commit()
    if with_chat:
        from .conversation_api import attach_chat
        attach_chat(app,current,db,owned)
    return app
