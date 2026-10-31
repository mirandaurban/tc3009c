import pytest
from chatpnl_labs.core import *

def test_clean(): assert clean_text("  hola\n mundo\x00 ")=="hola mundo"
def test_txt(): assert read_document("a.txt","área de estudio".encode())==[(1,"área de estudio")]
@pytest.mark.parametrize("name,content",[("a.exe",b"abc"),("a.pdf",b"hello"),("a.txt",b"\x00bad"),("a.txt",b"\xff"),("a.txt",b"%PDF-x"),("a.txt",b""),("a.txt",b" "*2000001),("a.txt",b"   ")])
def test_invalid_document(name,content):
    with pytest.raises(ValueError): read_document(name,content)
def test_pdf_page():
    import fitz
    doc=fitz.open();page=doc.new_page();page.insert_text((40,40),"Texto original de biblioteca")
    pages=read_document("../../nombre.pdf",doc.tobytes());doc.close()
    assert pages==[(1,"Texto original de biblioteca")]
def test_scanned_pdf():
    import fitz
    doc=fitz.open();doc.new_page();content=doc.tobytes();doc.close()
    with pytest.raises(ValueError,match="Sin texto"):read_document("scan.pdf",content)
def test_chunks_metadata():
    chunks=chunk_pages("x.txt",[(2,"uno dos tres cuatro cinco")],3,1)
    assert [(c.page,c.start_word,c.text) for c in chunks]==[(2,0,"uno dos tres"),(2,2,"tres cuatro cinco")]
def test_chunk_bad_overlap():
    with pytest.raises(ValueError):chunk_pages("x",[(1,"hola")],3,3)
def test_tfidf():
    r=Retriever(corpus());assert r.search("préstamo libros")[0]["source"]=="prestamos.txt"
def test_abstain():
    assert answer("xyzz999 galaxia",Retriever(corpus()))["abstained"]
def test_extract_reference():
    result=answer("libros préstamo",Retriever(corpus()))
    assert not result["abstained"] and result["answer"] in result["references"][0]["text"]
def test_ranking_formula():
    assert ranking_metrics(["B","A","C"],["A"])=={"recall_at_3":1.0,"mrr_at_5":0.5}
def test_ranking_duplicates(): assert ranking_metrics(["A","A"],["A","B"])["recall_at_3"]==.5
def test_no_relevant(): assert ranking_metrics(["A"],[])["mrr_at_5"] is None
def test_response_metrics():
    rows=[{"answerable":False,"abstained":True,"citation_valid":False},{"answerable":True,"abstained":False,"citation_valid":True}]
    assert response_metrics(rows)=={"abstention_recall":1,"false_abstention_rate":0,"citation_precision":1}
def test_splits_disjoint():
    import json
    groups=[{r["text"].casefold() for r in json.loads((data_dir()/f"intenciones_{s}.json").read_text())} for s in ["train","validation","test"]]
    assert not(groups[0]&groups[1] or groups[0]&groups[2] or groups[1]&groups[2])
def test_query_proportions():
    import json
    for split in ["dev","test"]:
        rows=json.loads((data_dir()/f"recuperacion_{split}.json").read_text())
        assert sum(bool(r["relevant"]) for r in rows)/len(rows)==.75

def test_primary_question_answers():
    result=answer("¿Cuántos libros puedo pedir?",Retriever(corpus()))
    assert not result["abstained"] and "tres libros" in result["answer"]

def test_missing_encoder_is_explicit():
    from chatpnl_labs.semantic import load_encoder
    with pytest.raises(FileNotFoundError,match="pendiente"):load_encoder(None)
