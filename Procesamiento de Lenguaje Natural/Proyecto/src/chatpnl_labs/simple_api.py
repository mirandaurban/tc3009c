from fastapi import FastAPI
from pydantic import BaseModel, Field
app=FastAPI(title="ChatPNL · HTTP",version="1.0")
class TextInput(BaseModel):
    text:str=Field(min_length=1,max_length=2000,pattern=r"\S")
@app.get("/health")
def health():
    return {"status":"ok"}
@app.post("/api/v1/echo")
def echo(body:TextInput):
    return {"text":body.text}
@app.post("/api/v1/analyze")
def analyze(body:TextInput):
    return {"words":len(body.text.split()),"characters":len(body.text)}
