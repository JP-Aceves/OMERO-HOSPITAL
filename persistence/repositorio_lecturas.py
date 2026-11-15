"""Lecturas de los sensores en data/lecturas.json. Responsable: Ivan (OME-34).

El fichero lo genera el simulador (OME-33) y no se sube a Git.
"""
import json
from pathlib import Path

from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada


class RepositorioLecturas:

    def __init__(self, ruta: Path = Path("data/lecturas.json")) -> None:
        self.ruta = Path(ruta)
        self._lecturas = ListaEnlazada()
        if self.ruta.exists():
            with self.ruta.open(encoding="utf-8") as fichero:
                for datos in json.load(fichero):
                    self._lecturas.insertar(Lectura.desde_dict(datos))

    def anadir(self, lecturas: ListaEnlazada) -> None:
        """Añade las lecturas al final del fichero."""
        for lectura in lecturas:
            self._lecturas.insertar(lectura)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        # json solo sabe escribir un array a partir de una list: la creamos
        # aquí, justo al escribir, y no la usamos para guardar datos.
        datos = [lectura.to_dict() for lectura in self._lecturas]
        with self.ruta.open("w", encoding="utf-8") as fichero:
            json.dump(datos, fichero, ensure_ascii=False, indent=2)

    def de_sensor(self, id_sensor: str) -> ListaEnlazada:
        """Todas las lecturas de ese sensor, de la más antigua a la más reciente."""
        suyas = ListaEnlazada()
        for lectura in self._lecturas:
            if lectura.sensor == id_sensor:
                suyas.insertar(lectura)
        return suyas

    def ultima(self, id_sensor: str) -> Lectura | None:
        """La lectura más reciente de ese sensor, o None si todavía no tiene."""
        ultima = None
        for lectura in self._lecturas:
            if lectura.sensor == id_sensor:
                ultima = lectura
        return ultima