"""Lectura y escritura de zonas (con sus sensores y actuadores) en JSON. Responsable: Ivan (OME-34)."""
from pathlib import Path

from model.lista_enlazada import ListaEnlazada
from model.zona import Zona


class RepositorioZonas:

    def __init__(self, ruta: Path = Path("data/zonas.json")) -> None:
        raise NotImplementedError("OME-34")

    def cargar(self) -> ListaEnlazada:
        """Lee el JSON y devuelve una ListaEnlazada de Zona. Vacía si el fichero no existe."""
        raise NotImplementedError("OME-34")

    def guardar(self) -> None:
        """Escribe todas las zonas en el JSON."""
        raise NotImplementedError("OME-34")

    def listar(self) -> ListaEnlazada:
        raise NotImplementedError("OME-34")

    def buscar(self, id_zona: str) -> Zona | None:
        raise NotImplementedError("OME-34")

    def anadir(self, zona: Zona) -> None:
        """Guarda una zona nueva. ValueError si el id ya existe."""
        raise NotImplementedError("OME-34")

    def actualizar(self, zona: Zona) -> None:
        """Sustituye la zona con ese id y guarda. ValueError si no existe."""
        raise NotImplementedError("OME-34")

    def eliminar(self, id_zona: str) -> bool:
        raise NotImplementedError("OME-34")

    def zonas_de(self, usuario: str) -> ListaEnlazada:
        """Zonas cuyo responsable es ese nombre de usuario."""
        raise NotImplementedError("OME-34")

    def siguiente_id(self, prefijo: str) -> str:
        """Siguiente id libre: "Z4" para zonas, "S8" para sensores, "A4" para actuadores."""
        raise NotImplementedError("OME-34")
