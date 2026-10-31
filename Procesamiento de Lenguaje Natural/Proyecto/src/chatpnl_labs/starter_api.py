"""Aplicación integrada: cuentas, conversaciones privadas y chat con evidencia en MySQL."""
from .auth_api import create_app as create_auth_app

def create_app(database_url=None,secret=None):
    app=create_auth_app(database_url,secret,with_chat=True)
    app.title="ChatPNL: acceso, chat e historial"
    return app
