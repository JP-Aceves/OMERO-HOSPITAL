"""Responsable: Rodas (OME-23)."""
from model.usuario import Usuario
from persistence.repositorio_json import RepositorioJSON


class LoginController:

    def __init__(self, repositorio: RepositorioJSON) -> None:
        self.repositorio = repositorio

    def login(self, usuario: str, contrasena: str) -> Usuario | None:
        """Devuelve el Usuario si las credenciales son correctas, o None."""
        raise NotImplementedError("OME-23")
