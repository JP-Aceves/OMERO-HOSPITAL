"""Lecturas de los sensores en data/lecturas.json. Responsable: Ivan (OME-34)."""
from pathlib import Path

from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada


class RepositorioLecturas:

    def __init__(self, ruta: Path = Path("data/lecturas.json")) -> None:
        raise NotImplementedError("OME-34")

    def anadir(self, lecturas: ListaEnlazada) -> None:
        """Añade las lecturas al final del fichero."""
        raise NotImplementedError("OME-34")

    def de_sensor(self, id_sensor: str) -> ListaEnlazada:
        raise NotImplementedError("OME-34")

    def ultima(self, id_sensor: str) -> Lectura | None:
        raise NotImplementedError("OME-34")
