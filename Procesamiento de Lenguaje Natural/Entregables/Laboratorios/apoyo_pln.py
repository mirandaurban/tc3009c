"""Funciones públicas para las Clases 7, 8 y 9. Los datos se leen junto a este archivo."""

"""Datos, normalización conservadora y métricas auditables."""
from pathlib import Path
import json, re, unicodedata, random
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
LABELS = ['acceso', 'conectividad', 'pagos', 'software']
SEED = 42

def seed_all(seed=SEED,neural=True):
    random.seed(seed); np.random.seed(seed)
    if neural:
        import torch
        torch.manual_seed(seed); torch.set_num_threads(2)

def load_requests():
    df = pd.read_csv(ROOT/'solicitudes.csv')
    validate_splits(df)
    return df

def load_json(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))

def validate_splits(df):
    required = {'id','text','label','family','split'}
    if not required <= set(df):
        raise ValueError(f'Faltan columnas: {required-set(df)}')
    if df.id.duplicated().any() or df.text.isna().any():
        raise ValueError('IDs duplicados o textos ausentes')
    if df.groupby('family').split.nunique().max() > 1:
        raise ValueError('Fuga: una familia aparece en más de una partición')
    if df.groupby('text').split.nunique().max() > 1:
        raise ValueError('Fuga: texto idéntico en distintas particiones')
    if set(df.split) != {'train','validation','test'}:
        raise ValueError('Se requieren train, validation y test')
    return True

def normalize(text):
    if not isinstance(text, str):
        raise TypeError('Se esperaba una cadena de texto')
    # Se conservan negación, acentos y signos con valor lingüístico.
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()

def redact(text):
    return re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[CORREO]', text)

def words(text):
    return re.findall(r'\w+|[^\w\s]', normalize(text).lower(), flags=re.UNICODE)

def rule_label(text):
    t=normalize(text).lower()
    rules=[('pagos',r'factura|pag[oó]|cobro|cargo|tarjeta|reembolso'),('acceso',r'contrase|sesión|usuario|c[oó]digo|cuenta|acceso'),('conectividad',r'wifi|red|internet|vpn|conexión')]
    return next((label for label,pattern in rules if re.search(pattern,t)), 'software')

def exact_span_scores(gold, predicted):
    """Micro por tuplas (documento, inicio, fin, tipo), coincidencia exacta."""
    g=set(gold); p=set(predicted); tp=len(g&p)
    precision=tp/len(p) if p else 0.0
    recall=tp/len(g) if g else 0.0
    return dict(tp=tp,fp=len(p-g),fn=len(g-p),precision=precision,recall=recall,
                f1=2*precision*recall/(precision+recall) if precision+recall else 0.0)

def rule_entities(text):
    spans=[]
    for label,pat in [('FOLIO',r'\bINC-\d{4}\b'),('PRODUCTO',r'\b(?:AulaPro|MesaApp|NubeTec)\b')]:
        spans.extend((m.start(),m.end(),label) for m in re.finditer(pat,text))
    return sorted(spans)


"""Modelos de referencia ajustados exclusivamente con entrenamiento."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.decomposition import NMF

def make_baseline(kind='logistic', analyzer='word', ngram_range=(1,2)):
    model=LogisticRegression(max_iter=400,random_state=SEED,C=2.0) if kind=='logistic' else MultinomialNB(alpha=1.0)
    return Pipeline([('tfidf',TfidfVectorizer(analyzer=analyzer,ngram_range=ngram_range,sublinear_tf=False)),('classifier',model)])

def evaluate(model, df, labels=LABELS):
    pred=model.predict(df.text)
    return dict(macro_f1=f1_score(df.label,pred,average='macro',zero_division=0),
                confusion=confusion_matrix(df.label,pred,labels=labels).tolist(),
                report=classification_report(df.label,pred,zero_division=0,output_dict=True),
                predictions=list(pred))

def tfidf_numeric():
    corpus=['pago pago tarjeta','pago acceso','red acceso']
    vectorizer=TfidfVectorizer(norm=None,smooth_idf=True,token_pattern=r'(?u)\b\w+\b')
    actual=vectorizer.fit_transform(corpus).toarray()
    counts=CountVectorizer(vocabulary=vectorizer.vocabulary_).fit_transform(corpus).toarray()
    df=(counts>0).sum(axis=0)
    idf=np.log((1+len(corpus))/(1+df))+1
    expected=counts*idf
    np.testing.assert_allclose(actual,expected)
    return vectorizer.get_feature_names_out(),counts,idf,actual

def topic_model(texts,n_topics=4):
    vec=TfidfVectorizer(max_df=.95,min_df=2,stop_words=['de','la','el','en','un','una','y','no','mi','que','al','del','para','con','lo','se','es'])
    x=vec.fit_transform(texts)
    nmf=NMF(n_components=n_topics,init='nndsvda',random_state=SEED,max_iter=400)
    w=nmf.fit_transform(x)
    names=vec.get_feature_names_out()
    topics=[[str(names[j]) for j in row.argsort()[-6:][::-1]] for row in nmf.components_]
    return topics,w,nmf.reconstruction_err_


"""Redes pequeñas auténticas: no usan checkpoints precalculados."""
import math
import numpy as np
import torch
from torch import nn

def vocabulary(texts):
    return {'<PAD>':0,'<UNK>':1,**{w:i+2 for i,w in enumerate(sorted({w for t in texts for w in words(t)}))}}

def encode(texts,vocab,max_length=32):
    x=torch.zeros((len(texts),max_length),dtype=torch.long)
    for i,t in enumerate(texts):
        ids=[vocab.get(w,1) for w in words(t)[:max_length]]
        x[i,:len(ids)]=torch.tensor(ids,dtype=torch.long)
    return x

class MeanClassifier(nn.Module):
    def __init__(self,vocab_size,dim=24,n_labels=4):
        super().__init__();self.embedding=nn.Embedding(vocab_size,dim,padding_idx=0);self.output=nn.Linear(dim,n_labels)
    def forward(self,ids):
        mask=(ids!=0).unsqueeze(-1)
        pooled=(self.embedding(ids)*mask).sum(1)/mask.sum(1).clamp(min=1)
        return self.output(pooled)

def train_mean(train,validation,epochs=30):
    seed_all();v=vocabulary(train.text)
    x=encode(list(train.text),v); y=torch.tensor([LABELS.index(z) for z in train.label])
    vx=encode(list(validation.text),v);vy=torch.tensor([LABELS.index(z) for z in validation.label])
    model=MeanClassifier(len(v));opt=torch.optim.Adam(model.parameters(),lr=.035)
    best=float('inf');best_state=None;patience=0;history=[]
    for epoch in range(epochs):
        model.train();opt.zero_grad();loss=nn.functional.cross_entropy(model(x),y);loss.backward();opt.step()
        model.eval()
        with torch.no_grad(): val_loss=nn.functional.cross_entropy(model(vx),vy).item()
        history.append({'epoch':epoch+1,'train_loss':loss.item(),'validation_loss':val_loss})
        if val_loss<best-1e-4:
            best=val_loss;best_state={k:v.detach().clone() for k,v in model.state_dict().items()};patience=0
        else: patience+=1
        if patience>=5:break
    model.load_state_dict(best_state)
    return model,v,history

def skipgram_embeddings(texts,epochs=40,dim=16):
    """Skip-gram con softmax completo; corpus pequeño, objetivo Word2Vec."""
    seed_all();v=vocabulary(texts);pairs=[]
    for text in texts:
        ids=[v[w] for w in words(text)]
        for i,c in enumerate(ids):
            pairs.extend((c,ids[j]) for j in range(max(0,i-2),min(len(ids),i+3)) if i!=j)
    x=torch.tensor([a for a,b in pairs]);y=torch.tensor([b for a,b in pairs])
    embedding=nn.Embedding(len(v),dim);out=nn.Linear(dim,len(v),bias=False)
    opt=torch.optim.Adam(list(embedding.parameters())+list(out.parameters()),lr=.035);history=[]
    for epoch in range(epochs):
        opt.zero_grad();loss=nn.functional.cross_entropy(out(embedding(x)),y);loss.backward();opt.step();history.append(loss.item())
    return v,embedding.weight.detach().numpy(),history

def neighbors(word,vectors,vocab,k=5):
    matrix=vectors/np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-8)
    i=vocab.get(word,1);scores=matrix@matrix[i];inverse={i:w for w,i in vocab.items()}
    return [(inverse[j],round(float(scores[j]),3)) for j in scores.argsort()[::-1] if j not in (i,0,1)][:k]

class TinyGRU(nn.Module):
    def __init__(self,n):
        super().__init__();self.embedding=nn.Embedding(n,16);self.rnn=nn.GRU(16,32,batch_first=True);self.head=nn.Linear(32,n)
    def forward(self,x):
        h,_=self.rnn(self.embedding(x));return self.head(h)

def train_language_model(texts,epochs=35):
    seed_all();v=vocabulary(texts);tokens=[v[w] for t in texts for w in words(t)]+[1]
    blocks=[tokens[i:i+9] for i in range(0,len(tokens)-9,8)]
    a=torch.tensor(blocks);x=a[:,:-1];y=a[:,1:]
    model=TinyGRU(len(v));opt=torch.optim.Adam(model.parameters(),lr=.025);history=[]
    for _ in range(epochs):
        opt.zero_grad();z=model(x);loss=nn.functional.cross_entropy(z.reshape(-1,len(v)),y.reshape(-1));loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step();history.append(loss.item())
    return model,v,history

def attention(q,k,v,causal=False):
    scores=q@k.transpose(-2,-1)/math.sqrt(q.shape[-1])
    if causal:
        mask=torch.triu(torch.ones(scores.shape[-2:],dtype=torch.bool),diagonal=1)
        scores=scores.masked_fill(mask,float('-inf'))
    weights=scores.softmax(-1)
    return weights@v,weights
