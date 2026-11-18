"""Componentes didácticos de recuperación y generación documentada."""
import re,time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from .hf_models import local_snapshot,ENCODER,load_generator,generate_text
from .core import normalize

class LexicalIndex:
    def __init__(self,docs):
        self.docs=docs;self.vectorizer=TfidfVectorizer(ngram_range=(1,2));self.matrix=self.vectorizer.fit_transform([d['title']+' '+d['text'] for d in docs])
    def search(self,question,k=3):
        scores=(self.matrix@self.vectorizer.transform([question]).T).toarray().ravel()
        return [dict(document=self.docs[i],score=float(scores[i])) for i in np.argsort(-scores)[:k]]

class SemanticIndex:
    def __init__(self,docs):
        from sentence_transformers import SentenceTransformer
        self.docs=docs;self.model=SentenceTransformer(local_snapshot(ENCODER),device='cpu',local_files_only=True,model_kwargs={'use_safetensors':True})
        self.matrix=self.model.encode([d['title']+' '+d['text'] for d in docs],normalize_embeddings=True,show_progress_bar=False)
    def search(self,question,k=3):
        vector=self.model.encode([question],normalize_embeddings=True,show_progress_bar=False)[0]
        scores=self.matrix@vector
        return [dict(document=self.docs[i],score=float(scores[i])) for i in np.argsort(-scores)[:k]]

def retrieval_metrics(index,queries,k=3):
    rows=[]
    for q in queries:
        ranking=[x['document']['id'] for x in index.search(q['question'],k)]
        relevant=set(q['relevant'])
        if relevant:
            hits=[i+1 for i,d in enumerate(ranking) if d in relevant]
            rows.append(dict(id=q['id'],ranking=ranking,recall=len(relevant&set(ranking))/len(relevant),reciprocal_rank=1/min(hits) if hits else 0))
    return dict(recall_at_k=float(np.mean([r['recall'] for r in rows])),mrr=float(np.mean([r['reciprocal_rank'] for r in rows])),n_answerable=len(rows),details=rows)

def choose_threshold(index,development):
    """Desarrollo decide el umbral; las consultas test quedan selladas."""
    scored=[(index.search(q['question'],1)[0]['score'],bool(q['relevant'])) for q in development]
    values=sorted({x for x,y in scored});candidates=[0.0]+[(a+b)/2 for a,b in zip(values,values[1:])]+[1.01]
    def balanced(t):
        pos=[int(x>=t) for x,y in scored if y];neg=[int(x<t) for x,y in scored if not y]
        return (np.mean(pos)+np.mean(neg))/2
    best=max(candidates,key=lambda t:(balanced(t),t))
    return float(best),[dict(score=float(x),answerable=y) for x,y in scored]

def chunk_document(doc,size=60,overlap=10):
    if size<=overlap or overlap<0:raise ValueError('Se necesita 0 <= overlap < size')
    matches=list(re.finditer(r'\S+',doc['text']));chunks=[]
    for i in range(0,len(matches),size-overlap):
        batch=matches[i:i+size]
        if not batch:break
        a,b=batch[0].start(),batch[-1].end()
        chunks.append(dict(id=f"{doc['id']}:{i}",document_id=doc['id'],title=doc['title'],start=a,end=b,text=doc['text'][a:b],version=doc.get('version','1.0')))
        if i+size>=len(matches):break
    return chunks

def suspicious(text):
    # Filtro demostrativo para casos controlados; no es defensa exhaustiva.
    return bool(re.search(r'ignora.{0,30}(instrucciones|reglas)|revela.{0,25}(secreto|contraseña)|ignore.{0,25}instructions',text.lower()))

def canonical(text):
    return re.sub(r'\s+',' ',normalize(text).lower()).strip(' .,:;!?¿¡"')

class GroundedResponder:
    """Ejemplo guiado. Abstiene si la generación no es copia verificable del contexto.
    No constituye una prueba general de verdad ni una solución completa de integración.
    """
    def __init__(self,index,threshold):
        self.index=index;self.threshold=threshold;self.tokenizer,self.generator=load_generator()
    def answer(self,question,k=1,use_context=True):
        start=time.perf_counter()
        if not isinstance(question,str) or not 3<=len(question.strip())<=500:
            raise ValueError('La pregunta debe contener de 3 a 500 caracteres')
        found=self.index.search(question,k)
        allowed=[x for x in found if not suspicious(x['document']['text'])]
        base=dict(question=question,retrieved=[x['document']['id'] for x in found],citations=[],raw_generation='',abstained=True,input_tokens=0,truncated=False,prompt_budget=384)
        if suspicious(question):reason='La consulta contiene instrucciones ajenas a la consulta documental.'
        elif not allowed or allowed[0]['score']<self.threshold:reason='No hay evidencia documental suficiente.'
        elif len({d['document']['text'] for d in allowed})>1 and len({d['document']['title'] for d in allowed})==1:reason='Hay documentos contradictorios; se requiere revisión.'
        else:
            context='\n'.join(x['document']['text'] for x in allowed) if use_context else ''
            prompt=f'Contesta en español con una frase del contexto. Contexto: {context} Pregunta: {question} Respuesta:'
            base['input_tokens']=len(self.tokenizer(prompt,truncation=False)['input_ids'])
            if base['input_tokens']>384:
                base.update(answer='No tengo evidencia suficiente para responder.',reason='Contexto excede presupuesto; se requiere fragmentación.',latency_seconds=round(time.perf_counter()-start,4))
                return base
            raw=generate_text(prompt,self.tokenizer,self.generator,max_new_tokens=40);base['raw_generation']=raw
            support=[x['document']['id'] for x in allowed if len(canonical(raw))>=3 and canonical(raw) in canonical(x['document']['text'])]
            if support and use_context:
                base.update(answer=raw,citations=support,abstained=False,reason='Frase generada localizada literalmente en la evidencia.');reason=None
            else:reason='La generación no pudo verificarse literalmente en el contexto.'
        if reason:base.update(answer='No tengo evidencia suficiente para responder.',reason=reason)
        base['latency_seconds']=round(time.perf_counter()-start,4)
        return base
