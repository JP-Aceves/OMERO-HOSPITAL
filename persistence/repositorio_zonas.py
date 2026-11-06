"""Lectura y escritura de zonas (con sus sensores y actuadores) en JSON. Responsable: Ivan (OME-34)."""
import json
from pathlib import Path

from model.lista_enlazada import ListaEnlazada
from model.zona import Zona, crear_zona


class RepositorioZonas:

    def __init__(self, ruta: Path = Path("data/zonas.json")) -> None:
        self.ruta = Path(ruta)
        self._zonas = self.cargar()

    def cargar(self) -> ListaEnlazada:
        """Lee el JSON y devuelve una ListaEnlazada de Zona. Vacía si el fichero no existe."""
        zonas = ListaEnlazada()
        if self.ruta.exists():
            with self.ruta.open(encoding="utf-8") as fichero:
                for datos in json.load(fichero):
                    zonas.insertar(crear_zona(datos))
        return zonas

    def guardar(self) -> None:
        """Escribe todas las zonas en el JSON."""
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        # json solo sabe escribir un array a partir de una list: la creamos
        # aquí, justo al escribir, y no la usamos para guardar datos.
        datos = [zona.to_dict() for zona in self._zonas]
        with self.ruta.open("w", encoding="utf-8") as fichero:
            json.dump(datos, fichero, ensure_ascii=False, indent=2)

    def listar(self) -> ListaEnlazada:
        """Todas las zonas, en el orden del fichero."""
        return self._zonas

    def buscar(self, id_zona: str) -> Zona | None:
        """La zona con ese id, o None si no existe."""
        return self._zonas.buscar(lambda zona: zona.id == id_zona)

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
