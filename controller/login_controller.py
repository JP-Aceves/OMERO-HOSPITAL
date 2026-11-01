"""Responsable: Rodas (OME-23)."""
from model.usuario import Usuario
from persistence.repositorio_json import RepositorioJSON


class LoginController:

    def __init__(self, repositorio: RepositorioJSON) -> None:
        self.repositorio = repositorio

    def login(self, usuario: str, contrasena: str) -> Usuario | None:
        """Devuelve el Usuario si las credenciales son correctas, o None."""
        encontrado = self.repositorio.buscar_por_usuario(usuario)
        if encontrado is None:
            return None

        if encontrado.verificar_password(contrasena):
            return encontrado
        return None
