"""Texto, documentos, recuperación y métricas con entradas/salidas explícitas."""
from dataclasses import dataclass, asdict
from pathlib import Path
import re
import unicodedata
from nltk.stem.snowball import SpanishStemmer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    page: int
    text: str
    start_word: int = 0

def data_dir():
    # Sirve en el curso y en el paquete extraído con 07_datos/ a su raíz.
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "07_datos" / "chatpnl"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("Falta 07_datos/chatpnl; extraiga el paquete completo")

def clean_text(text):
    return re.sub(r"\s+", " ", text.replace("\x00", " ")).strip()

def read_document(name, content, max_bytes=2_000_000):
    """Devuelve (página 1-based, texto). No escribe nombres del usuario al disco."""
    if not content or len(content) > max_bytes:
        raise ValueError("Archivo vacío o mayor de 2 MB")
    suffix = Path(name).suffix.lower()
    if suffix == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("El contenido no es un PDF")
        import fitz
        try:
            with fitz.open(stream=content, filetype="pdf") as doc:
                if doc.is_encrypted or len(doc) > 100:
                    raise ValueError("PDF cifrado o con más de 100 páginas")
                pages = [(i+1, clean_text(page.get_text())) for i, page in enumerate(doc)]
        except Exception as exc:
            raise ValueError("PDF inválido, cifrado o no procesable") from exc
    elif suffix == ".txt":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeError as exc:
            raise ValueError("El TXT debe tener codificación UTF-8") from exc
        if any(ord(c)<32 and c not in "\n\r\t" for c in text) or content.startswith(b"%PDF-"):
            raise ValueError("El contenido no es texto plano")
        pages = [(1, clean_text(text))]
    else:
        raise ValueError("Solo se admiten PDF y TXT")
    if not any(text for _, text in pages):
        raise ValueError("Sin texto extraíble: PDF escaneado o documento vacío; requiere OCR previo")
    return [(page, text) for page, text in pages if text]

def chunk_pages(source, pages, size=90, overlap=15):
    if not 0 <= overlap < size or size < 1:
        raise ValueError("Debe cumplirse 0 ≤ solapamiento < tamaño")
    chunks = []
    for page, text in pages:
        words = clean_text(text).split()
        for start in range(0, len(words), size-overlap):
            chunks.append(Chunk(f"{source}:p{page}:w{start}",source,page," ".join(words[start:start+size]),start))
            if start+size >= len(words):
                break
    return chunks

def corpus():
    # Corpus público ficticio. Los documentos privados no se almacenan en cachés globales.
    chunks=[]
    for path in sorted((data_dir()/"documentos").glob("*.txt")):
        chunks += chunk_pages(path.name,read_document(path.name,path.read_bytes()))
    return chunks

# Política léxica explícita, escrita antes de crear la nueva prueba reservada.
# Se conservan negaciones, cantidades y palabras desconocidas: borrarlas ocultaría
# la parte de la pregunta para la que NO existe evidencia.
STOP_WORDS = frozenset("a al algo alguna alguno algunos ante como con cual cuales cuando cuanto cuanta cuantos cuantas de del desde donde durante el ella ellas ellos en entre es esta estas este estos la las le les lo los me mi mis o para por que quien se si su sus te tu tus un una uno unas unos y yo puedo puede pueden quiero necesito saber dime favor hay tiene tienen debe debo necesario posible pasa ocurre".split())
TERM_ALIASES = {
    "libros":"libro", "prestamos":"prestamo", "salas":"sala",
    "multas":"multa", "creditos":"credito", "dias":"dia",
    "horas":"hora", "personas":"persona", "grupos":"grupo",
    "sabados":"sabado", "domingos":"domingo", "abren":"abre",
    "pedir":"solicitar", "plazo":"duracion", "dura":"duracion",
    "sin":"no",
}
DEFAULT_THRESHOLD = 0.08
POLICY_VERSION = "cobertura_linguistica_top3_4"
STEMMER = SpanishStemmer()
# Formas de auxiliares/copulativos: selección gramatical explícita. Se preservan
# números, negaciones, comparativos y sustantivos desconocidos.
STOP_WORDS = STOP_WORDS | frozenset("cada son ser soy somos eres fue eran ha han haber haya habia he hemos sea sean estar estaba estamos estan estuvo estoy deben deber deberia podria podrian podemos pueda puedan".split())
TERM_ALIASES.update({"limite":"maximo", "maxima":"maximo", "maximas":"maximo",
    "adicional":"otra", "obligatorio":"requisito", "obligatoria":"requisito",
    "necesario":"requisito", "necesaria":"requisito", "servicio":"atencion",
    "dato":"identificador", "datos":"identificador", "numero":"cantidad"})

def content_terms(text):
    """Normaliza sin perder términos fuera del vocabulario del índice."""
    plain="".join(c for c in unicodedata.normalize("NFD",text.casefold())
                  if unicodedata.category(c)!="Mn")
    tokens=re.findall(r"[^\W_]+",plain,flags=re.UNICODE)
    return {TERM_ALIASES.get(t,t) for t in tokens if t not in STOP_WORDS}


def term_key(term):
    """Raíz morfológica: proporcionar/proporciona comparten clave; no implica sinonimia."""
    if term in {"no","nunca","ni"} or term.isdigit():
        return term
    root=STEMMER.stem(term)
    # Presentar/proporcionar se reconocen como entrega de un dato. La regla es
    # una equivalencia declarada del dominio, no una consulta memorizada.
    if root in {STEMMER.stem("presentar"),STEMMER.stem("proporcionar")}:
        return "entregar_dato"
    return root

def support_keys(text):
    keys={term_key(t) for t in content_terms(text)}
    # Solo inferir duración desde una expresión explícita de duración, nunca
    # desde una hora de apertura/cierre aislada. No depende de IDs ni consultas.
    plain="".join(c for c in unicodedata.normalize("NFD",text.casefold())
                  if unicodedata.category(c)!="Mn")
    if re.search(r"\b(?:por|durante|dura|despues de)\s+(?:un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|quince|veinte|[0-9]+)\s+(?:minutos?|horas?|dias?|semanas?)\b",plain):
        keys.add(term_key("duracion"))
    if re.search(r"\bhasta\s+(?:un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|[0-9]+)\s+[a-z]+\b",plain):
        keys.update({term_key("maximo"),term_key("cantidad")})
    if re.search(r"\bpara\s+[^.]+?\bse\s+(?:presenta|proporciona)\b",plain):
        keys.add(term_key("requisito"))
    if re.search(r"\b(?:credencial|folio)\b",plain):
        keys.add(term_key("identificador"))
    return keys

class Retriever:
    def __init__(self, chunks, ngram_range=(1,2)):
        if not chunks:
            raise ValueError("Corpus vacío")
        self.chunks=chunks
        # El ranking también excluye palabras funcionales; la puerta de evidencia
        # comprueba por separado la pregunta original, incluso sus términos OOV.
        self.vectorizer=TfidfVectorizer(lowercase=True,strip_accents="unicode",
            stop_words=sorted(STOP_WORDS),ngram_range=ngram_range)
        self.matrix=self.vectorizer.fit_transform([c.text for c in chunks])
    def search(self, query, k=3):
        if not query.strip() or not 1 <= k <= 20:
            raise ValueError("Consulta vacía o k fuera de 1–20")
        scores=cosine_similarity(self.vectorizer.transform([query]),self.matrix)[0]
        order=np.argsort(-scores,kind="stable")[:k]
        return [{**asdict(self.chunks[i]),"score":float(scores[i])} for i in order]

def evidence_check(query, hit, threshold=DEFAULT_THRESHOLD):
    """Puerta conservadora: coseno positivo y TODOS los términos normalizados cubiertos.

    No es prueba de implicación lógica. Puede abstenerse ante paráfrasis válidas;
    no permite que una palabra desconocida desaparezca silenciosamente del control.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("Umbral fuera de [0, 1]")
    required=content_terms(query)
    supported=support_keys(hit["text"])
    missing=sorted(t for t in required if term_key(t) not in supported)
    coverage=(len(required)-len(missing))/len(required) if required else 0.0
    if not required: reason="sin_terminos_informativos"
    elif missing: reason="terminos_sin_respaldo"
    elif hit["score"]<=0 or hit["score"]<threshold: reason="similitud_insuficiente"
    else: reason="evidencia_lexica_cubierta"
    return {"accepted":reason=="evidencia_lexica_cubierta", "reason":reason,
            "query_terms":sorted(required),"missing_terms":missing,
            "coverage":coverage,"score":hit["score"],"threshold":threshold,
            "policy_version":POLICY_VERSION}

def find_supported_hit(query, retriever, threshold=DEFAULT_THRESHOLD):
    """Busca respaldo en top-3; un primer candidato incompleto no oculta otro válido."""
    if not 0 <= threshold <= 1:
        raise ValueError("Umbral fuera de [0, 1]")
    hits=retriever.search(query,k=3)
    checked=[]
    for rank,hit in enumerate(hits,1):
        decision=evidence_check(query,hit,threshold)
        checked.append({"id":hit["id"],"rank":rank,**decision})
        if decision["accepted"]:
            return hit,{**decision,"selected_rank":rank,"checked_candidates":checked}
    # Explicar el mejor candidato cuando ninguno respalda la consulta completa.
    return None,{**checked[0],"selected_rank":None,"checked_candidates":checked}

def answer(query, retriever, threshold=DEFAULT_THRESHOLD):
    first,decision=find_supported_hit(query,retriever,threshold)
    if first is None:
        return {"answer":"No encuentro evidencia suficiente en este corpus.",
                "abstained":True,"references":[],"evidence":decision}
    # Extractivo: copia un fragmento; no obedece instrucciones del contenido ni inventa síntesis.
    return {"answer":first["text"],"abstained":False,"references":[first],"evidence":decision}

def ranking_metrics(ranked, relevant, k_recall=3, k_mrr=5):
    """Recall=aciertos únicos/relevantes. MRR=1/rango del primer relevante. Sin evidencia: None."""
    relevant=set(relevant)
    if not relevant:
        return {"recall_at_3":None,"mrr_at_5":None}
    unique=list(dict.fromkeys(ranked))
    recall=len(set(unique[:k_recall]) & relevant)/len(relevant)
    rr=next((1/i for i,x in enumerate(unique[:k_mrr],1) if x in relevant),0.0)
    return {"recall_at_3":recall,"mrr_at_5":rr}

def response_metrics(rows):
    """Cada fila contiene answerable, abstained, citation_valid (verificación contra la fuente)."""
    if not rows:
        raise ValueError("Se requieren casos")
    no=[r for r in rows if not r["answerable"]]
    yes=[r for r in rows if r["answerable"]]
    emitted=[r for r in rows if not r["abstained"]]
    return {
      "abstention_recall":sum(r["abstained"] for r in no)/len(no) if no else None,
      "false_abstention_rate":sum(r["abstained"] for r in yes)/len(yes) if yes else None,
      "citation_precision":sum(r["citation_valid"] for r in emitted)/len(emitted) if emitted else None}

def deterministic_reply(prompt):
    if "hola" in prompt.lower():
        return "Hola. Esta demostración conserva mensajes durante tu sesión."
    return f"Recibí {len(prompt.split())} palabras. Soy una función local, no un modelo generativo."
