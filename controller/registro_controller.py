"""Responsable: Medina (OME-24)."""
from persistence.repositorio_json import RepositorioJSON


class RegistroController:

    def __init__(self, repositorio: RepositorioJSON) -> None:
        self.repositorio = repositorio

    def registrar(self, nombre: str, usuario: str, contrasena: str, repetir: str, rol: str) -> str | None:
        """Devuelve None si se registró, o el mensaje de error que hay que mostrar."""
        raise NotImplementedError("OME-24")
