"""Carga pública local verificada; sin código remoto y con safetensors."""
import os,json,re
from pathlib import Path
from .core import ROOT,seed_all,LABELS
os.environ.setdefault('HF_HOME',str(ROOT/'.cache/huggingface'))
os.environ.setdefault('HF_HUB_DISABLE_IMPLICIT_TOKEN','1')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1')
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
ENCODER='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
GENERATOR='google/flan-t5-small'

def local_snapshot(model):
    from huggingface_hub import snapshot_download
    registry=Path(__file__).with_name('modelos.json')
    revisions=json.loads(registry.read_text()) if registry.exists() else {}
    revision=revisions.get(model)
    # Todas las descargas se realizan explícitamente mediante scripts/download_models.py.
    return snapshot_download(model,revision=revision,local_files_only=True,token=False)

def load_encoder():
    from transformers import AutoModel,AutoTokenizer
    path=local_snapshot(ENCODER)
    return AutoTokenizer.from_pretrained(path,local_files_only=True),AutoModel.from_pretrained(path,local_files_only=True,use_safetensors=True,trust_remote_code=False)

def load_generator():
    from transformers import AutoTokenizer,AutoModelForSeq2SeqLM
    path=local_snapshot(GENERATOR)
    tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True)
    model=AutoModelForSeq2SeqLM.from_pretrained(path,local_files_only=True,use_safetensors=True,trust_remote_code=False).eval()
    return tokenizer,model

def generate_text(prompt,tokenizer,model,sampling=False,max_new_tokens=48,temperature=.7,top_p=.9):
    import torch
    length=len(tokenizer(prompt,truncation=False)['input_ids'])
    if length>384:raise ValueError(f'El prompt contiene {length} tokens; reduce contexto al presupuesto de 384, no se trunca silenciosamente.')
    encoded=tokenizer(prompt,return_tensors='pt',truncation=False)
    options=dict(max_new_tokens=max_new_tokens,do_sample=sampling)
    if sampling:options.update(temperature=temperature,top_p=top_p)
    with torch.no_grad():out=model.generate(**encoded,**options)
    return tokenizer.decode(out[0],skip_special_tokens=True)

def fine_tune_classifier(train,validation,epochs=2,labels=LABELS,device='cpu'):
    """Actualiza última capa Transformer y cabeza; selección solo con validación."""
    import torch
    from torch import nn
    from sklearn.metrics import f1_score
    seed_all()
    if device not in {'cpu','cuda','mps'}:raise ValueError('Dispositivo permitido: cpu, cuda o mps')
    if device=='cuda' and not torch.cuda.is_available():raise RuntimeError('CUDA no está disponible; usa CPU')
    if device=='mps' and not torch.backends.mps.is_available():raise RuntimeError('MPS no está disponible; usa CPU')
    from transformers import AutoTokenizer,AutoModelForSequenceClassification
    path=local_snapshot(ENCODER)
    tok=AutoTokenizer.from_pretrained(path,local_files_only=True)
    model=AutoModelForSequenceClassification.from_pretrained(
        path,num_labels=len(labels),id2label=dict(enumerate(labels)),
        label2id={name:i for i,name in enumerate(labels)},
        local_files_only=True,use_safetensors=True,trust_remote_code=False)
    # La cabeza de clasificación es nueva: inferir antes del ajuste no prueba calidad.
    for p in model.parameters():p.requires_grad=False
    for part in [model.bert.encoder.layer[-1],model.bert.pooler,model.classifier]:
        for p in part.parameters():p.requires_grad=True
    model.to(device)
    opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=5e-4,weight_decay=.01)
    encode=lambda texts:{k:v.to(device) for k,v in tok(list(texts),padding=True,truncation=True,max_length=48,return_tensors='pt').items()}
    val_x=encode(validation.text);val_y=torch.tensor([labels.index(x) for x in validation.label],device=device)
    history=[];best_loss=float('inf');best=None
    for epoch in range(epochs):
        model.train();losses=[]
        indices=torch.randperm(len(train)).tolist()
        for start in range(0,len(indices),8):
            batch=train.iloc[indices[start:start+8]];x=encode(batch.text);y=torch.tensor([labels.index(x) for x in batch.label],device=device)
            opt.zero_grad();loss=nn.functional.cross_entropy(model(**x).logits,y);loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step();losses.append(loss.item())
        model.eval()
        with torch.no_grad():z=model(**val_x).logits;val_loss=nn.functional.cross_entropy(z,val_y).item()
        history.append(dict(epoch=epoch+1,train_loss=sum(losses)/len(losses),validation_loss=val_loss,validation_macro_f1=f1_score(val_y.cpu(),z.argmax(-1).cpu(),average='macro',zero_division=0)))
        if val_loss<best_loss:
            best_loss=val_loss;best={n:p.detach().clone() for n,p in model.named_parameters() if p.requires_grad}
    with torch.no_grad():
        for n,p in model.named_parameters():
            if p.requires_grad:p.copy_(best[n])
    model.eval()
    return tok,model,history

def contextual_predict(tokenizer,model,texts,labels=LABELS):
    import torch
    out=[]
    with torch.no_grad():
        for start in range(0,len(texts),8):
            x=tokenizer(list(texts)[start:start+8],padding=True,truncation=True,max_length=48,return_tensors='pt')
            x={k:v.to(next(model.parameters()).device) for k,v in x.items()}
            out.extend(labels[int(i)] for i in model(**x).logits.argmax(-1))
    return out

NER_LABELS=['O','B-PRODUCTO','I-PRODUCTO','B-FOLIO','I-FOLIO']
def word_bio(text,spans):
    """Offsets sobre texto original; tokens básicos preservan signos y acentos."""
    matches=list(re.finditer(r'\w+|[^\w\s]',text));tokens=[m.group() for m in matches];tags=[]
    for m in matches:
        tag='O'
        for start,end,label in spans:
            if m.start()>=start and m.end()<=end:tag=('B-' if m.start()==start else 'I-')+label
        tags.append(NER_LABELS.index(tag))
    return tokens,tags,[(m.start(),m.end()) for m in matches]

def align_bio(word_ids,word_tags):
    previous=None;aligned=[]
    for wid in word_ids:
        # Solo la primera subpalabra contribuye a la pérdida; -100 se ignora.
        aligned.append(-100 if wid is None or wid==previous else word_tags[wid]);previous=wid
    return aligned

def bio_to_spans(tags,offsets):
    result=[];active=None
    for tag,(start,end) in zip(tags,offsets):
        name=NER_LABELS[int(tag)]
        if name=='O':
            if active:result.append(tuple(active));active=None
        else:
            prefix,label=name.split('-',1)
            if prefix=='B' or active is None or active[2]!=label:
                if active:result.append(tuple(active))
                active=[start,end,label]
            else:active[1]=end
    if active:result.append(tuple(active))
    return result

def train_contextual_ner(rows,epochs=35):
    """Cabeza BIO entrenada sobre estados de encoder multilingüe congelado.
    Esto NO es un modelo previamente afinado para NER; su calidad se mide aquí.
    """
    import torch
    from torch import nn
    seed_all();tok,encoder=load_encoder();encoder.eval()
    data={}
    for split in ['train','validation','test']:
        samples=[r for r in rows if r['split']==split]
        triples=[word_bio(r['text'],r['entities']) for r in samples]
        x=tok([a[0] for a in triples],is_split_into_words=True,padding=True,truncation=True,max_length=64,return_tensors='pt')
        aligned=torch.tensor([align_bio(x.word_ids(i),triples[i][1]) for i in range(len(samples))])
        with torch.no_grad():features=encoder(**x).last_hidden_state
        data[split]=(samples,triples,x,aligned,features)
    head=nn.Linear(encoder.config.hidden_size,len(NER_LABELS));opt=torch.optim.AdamW(head.parameters(),lr=.025)
    history=[];best=float('inf');best_state=None
    for epoch in range(epochs):
        opt.zero_grad();loss=nn.functional.cross_entropy(head(data['train'][4]).reshape(-1,len(NER_LABELS)),data['train'][3].reshape(-1),ignore_index=-100);loss.backward();opt.step()
        with torch.no_grad():vl=nn.functional.cross_entropy(head(data['validation'][4]).reshape(-1,len(NER_LABELS)),data['validation'][3].reshape(-1),ignore_index=-100).item()
        history.append(dict(epoch=epoch+1,train_loss=loss.item(),validation_loss=vl))
        if vl<best:best=vl;best_state={k:v.detach().clone() for k,v in head.state_dict().items()}
    head.load_state_dict(best_state)
    predictions=[]
    with torch.no_grad():p=head(data['test'][4]).argmax(-1)
    for i,(sample,triple) in enumerate(zip(data['test'][0],data['test'][1])):
        word_tags=[];previous=None
        for j,wid in enumerate(data['test'][2].word_ids(i)):
            if wid is not None and wid!=previous:word_tags.append(int(p[i,j]))
            previous=wid
        predictions.append(dict(id=sample['id'],text=sample['text'],gold=sample['entities'],predicted=bio_to_spans(word_tags,triple[2])))
    return predictions,history

def save_trainable_checkpoint(model,path):
    """Solo tensores propios entrenables; safetensors evita deserializar objetos Python."""
    from safetensors.torch import save_file
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    state={name:p.detach().cpu().contiguous() for name,p in model.named_parameters() if p.requires_grad}
    save_file(state,str(path),metadata={'encoder':ENCODER,'scope':'ultima capa y cabeza; reconstruir backbone desde revisión fijada'})

def load_trainable_checkpoint(model,path):
    import torch
    from safetensors.torch import load_file
    state=load_file(str(path));expected={n:p for n,p in model.named_parameters() if p.requires_grad}
    if set(state)!=set(expected):raise ValueError('El checkpoint no corresponde a los parámetros entrenables del modelo')
    with torch.no_grad():
        for n,p in expected.items():
            if p.shape!=state[n].shape:raise ValueError('Dimensión incompatible: '+n)
            p.copy_(state[n])
