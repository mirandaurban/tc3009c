"""Cliente con timeout y errores legibles sin exponer tokens ni cuerpos privados."""
import httpx
class ServiceError(Exception):
    def __init__(self,message,status_code=None):
        super().__init__(message)
        self.status_code=status_code
def request_json(base, method, path, token=None, **kwargs):
    headers={"Authorization":f"Bearer {token}"} if token else {}
    try:
        with httpx.Client(base_url=base,timeout=5.0) as client:
            response=client.request(method,path,headers=headers,**kwargs)
            response.raise_for_status()
            return None if response.status_code==204 else response.json()
    except httpx.TimeoutException as exc:
        raise ServiceError("La API tardó más de 5 segundos. Intente de nuevo.") from exc
    except httpx.HTTPStatusError as exc:
        code=exc.response.status_code
        messages={401:"Sesión inválida o expirada. Inicie sesión.",404:"Recurso no disponible.",409:"Registro existente o envío repetido con datos distintos.",422:"Datos inválidos: revise los campos."}
        raise ServiceError(f"HTTP {code}: "+messages.get(code,"La API rechazó la solicitud."),status_code=code) from exc
    except (httpx.RequestError, ValueError) as exc:
        raise ServiceError("No se puede conectar con la API o su JSON es inválido.") from exc
