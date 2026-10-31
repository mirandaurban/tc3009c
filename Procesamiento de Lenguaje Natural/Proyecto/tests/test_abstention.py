"""Regresiones del fallo retirado y propiedades de la puerta de evidencia.

Las consultas de la nueva prueba no se usan para ajustar ni se duplican aquí.
"""
from pathlib import Path
import importlib.util
import pytest
from fastapi.testclient import TestClient
from chatpnl_labs.core import Retriever,Chunk,corpus,answer,content_terms,evidence_check
from chatpnl_labs.starter_api import create_app

@pytest.mark.parametrize("query",["receta de tortilla","órbita de Saturno"])
def test_retired_failure_is_regression_only(query):
    result=answer(query,Retriever(corpus()))
    assert result["abstained"] and result["references"]==[]
    assert result["evidence"]["missing_terms"]

@pytest.mark.parametrize("query",["de la en para","¿Qué?", "¿Cuál es la contraseña de las salas?", "¿Qué seguro cubre los libros?"])
def test_function_words_or_unknown_attribute_cannot_authorize(query):
    result=answer(query,Retriever(corpus()),threshold=0.0)
    assert result["abstained"] and not result["references"]

def test_oov_terms_survive_vectorization():
    r=Retriever([Chunk("uno","publico.txt",1,"La biblioteca presta libros")])
    result=answer("libros teletransporte",r,threshold=0.0)
    assert result["abstained"]
    assert "teletransporte" in result["evidence"]["missing_terms"]
    assert result["evidence"]["score"]>0

def test_negation_and_numbers_are_not_silently_deleted():
    assert {"no","nunca","42"} <= content_terms("no nunca 42 libros")

def test_matching_terms_and_actual_reference_still_answer():
    result=answer("libros préstamo",Retriever(corpus()))
    assert not result["abstained"]
    assert result["evidence"]["coverage"]==1
    assert result["references"][0]["source"]=="prestamos.txt"

def test_coverage_is_checked_on_selected_passage():
    r=Retriever([Chunk("1","a.txt",1,"biblioteca libros"),Chunk("2","b.txt",1,"vacunas hospital")])
    assert answer("biblioteca vacunas",r,threshold=0)["abstained"]

def test_threshold_can_still_reject_lexically_covered_query():
    result=answer("libros préstamo",Retriever(corpus()),threshold=1.0)
    assert result["abstained"] and result["evidence"]["reason"]=="similitud_insuficiente"

def test_starter_http_abstains_without_references(integrated):
    from conftest import account
    from uuid import uuid4
    client,_,_,_=integrated
    headers,_=account(client,"abstencion")
    cid=client.post("/conversations",headers=headers,json={"title":"Prueba"}).json()["id"]
    result=client.post(f"/conversations/{cid}/query",headers=headers,json={"text":"órbita de Saturno","request_id":str(uuid4())})
    assert result.status_code==200
    body=result.json()
    assert body["abstained"] and not body["references"]
    assert "saturno" in body["evidence"]["missing_terms"]
    saved=client.get(f"/conversations/{cid}/messages",headers=headers).json()
    assert saved[-1]["abstained"] is True and saved[-1]["references"]==[]

def evaluator():
    p=Path(__file__).resolve().parents[1]/"evaluacion_pnl/abstencion.py"
    spec=importlib.util.spec_from_file_location("abstention_evaluator",p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def test_calibration_never_opens_any_test(monkeypatch):
    module=evaluator();original=module.read;opened=[]
    def dev_only(path):
        opened.append(Path(path).name)
        assert Path(path).name=="recuperacion_dev.json"
        return original(path)
    monkeypatch.setattr(module,"read",dev_only)
    policy=module.calibrate()
    assert set(opened)=={"recuperacion_dev.json"}
    assert policy["dev_selected"]["unsupported_answers"]==0

def test_changed_policy_inputs_fail_before_test_is_opened():
    module=evaluator()
    with pytest.raises(RuntimeError,match="cambiaron"):
        module.evaluate({"inputs":{}},"archivo_que_no_existe.json")

def test_incomplete_first_hit_does_not_hide_supported_second_hit():
    class RankedExample:
        def search(self,query,k=3):
            return [
                {"id":"1","source":"horarios.txt","page":1,"text":"Devolución de libros en mostrador","score":0.8},
                {"id":"2","source":"prestamos.txt","page":1,"text":"Se permite solicitar libros con credencial","score":0.2}]
    result=answer("libros pedir",RankedExample())
    assert not result["abstained"]
    assert result["references"][0]["id"]=="2"
    assert result["evidence"]["selected_rank"]==2

@pytest.mark.parametrize("query,passage",[
    ("proporcionar folio", "Se proporciona el folio"),
    ("presentarse con credencial", "Se presenta una credencial"),
    ("plazo préstamo", "El préstamo dura siete días"),
    ("duración reserva", "La reserva es por dos horas"),
    ("renovar sin reserva", "Se permite renovar si no hay otra reserva"),
    ("requisito préstamo", "Para solicitar un préstamo se presenta credencial"),
    ("máximo libros", "Hasta tres libros por persona"),
])
def test_linguistic_support_is_backed_by_explicit_text(query,passage):
    hit={"text":passage,"score":.5}
    assert evidence_check(query,hit)["accepted"]

@pytest.mark.parametrize("query",[
    "plazo visa", "sin pasaporte", "proporcionar contraseña",
    "máximo automóviles", "requisito vacuna",
])
def test_normalization_does_not_hide_unknown_subjects(query):
    hit={"text":"Para solicitar libros se presenta credencial. Hasta tres libros por persona. El préstamo dura siete días. No hay otra reserva.","score":.99}
    result=evidence_check(query,hit,threshold=0)
    assert not result["accepted"] and result["missing_terms"]

def test_opening_time_is_not_assumed_to_be_a_duration():
    assert not evidence_check("plazo",{"text":"Abre a las nueve horas","score":.99})["accepted"]

@pytest.mark.parametrize("filename",[
    "recuperacion_test.json","recuperacion_prueba_reservada.json",
    "recuperacion_prueba_confirmacion.json","recuperacion_prueba_validacion.json",
])
def test_every_previous_test_is_retired(filename):
    module=evaluator()
    with pytest.raises(ValueError,match="retirado"):
        module.evaluate({"inputs":module.inputs()},filename)
