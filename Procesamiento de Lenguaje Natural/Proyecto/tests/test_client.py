import httpx,pytest
from chatpnl_labs.http_client import request_json,ServiceError
@pytest.mark.parametrize("code",[401,404,422,500])
def test_http_errors(monkeypatch,code):
    def fake(self,*args,**kwargs):return httpx.Response(code,request=httpx.Request("POST","http://test/x"))
    monkeypatch.setattr(httpx.Client,"request",fake)
    with pytest.raises(ServiceError,match=str(code)):request_json("http://test","POST","/x")
@pytest.mark.parametrize("kind",[httpx.ConnectError,httpx.ReadTimeout])
def test_connection_timeout(monkeypatch,kind):
    def fake(self,*args,**kwargs):raise kind("test")
    monkeypatch.setattr(httpx.Client,"request",fake)
    with pytest.raises(ServiceError):request_json("http://test","GET","/x")


def test_delete_204_is_success_without_json(monkeypatch):
    def empty(self,*args,**kwargs):return httpx.Response(204,request=httpx.Request("DELETE","http://test/x"))
    monkeypatch.setattr(httpx.Client,"request",empty)
    assert request_json("http://test","DELETE","/x") is None
