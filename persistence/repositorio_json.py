"""Lectura y escritura de usuarios en JSON. Responsable: Ivan (OME-22)."""
from pathlib import Path

from model.lista_enlazada import ListaEnlazada
from model.usuario import Usuario


class RepositorioJSON:

    def __init__(self, ruta: Path = Path("data/usuarios.json")) -> None:
        self.ruta = ruta

    def cargar(self) -> ListaEnlazada:
        """Lee el JSON y devuelve una ListaEnlazada de Usuario."""
        raise NotImplementedError("OME-22")

    def guardar(self, usuarios: ListaEnlazada) -> None:
        raise NotImplementedError("OME-22")

    def buscar_por_usuario(self, nombre_usuario: str) -> Usuario | None:
        raise NotImplementedError("OME-22")

    def anadir(self, usuario: Usuario) -> None:
        """Guarda un usuario nuevo. Lanza ValueError si el nombre de usuario ya existe."""
        raise NotImplementedError("OME-22")
