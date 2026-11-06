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
        if self.buscar(zona.id) is not None:
            raise ValueError(f"Ya existe una zona con el id {zona.id}")
        self._zonas.insertar(zona)
        self.guardar()

    def actualizar(self, zona: Zona) -> None:
        """Sustituye la zona con ese id y guarda. ValueError si no existe."""
        if self.buscar(zona.id) is None:
            raise ValueError(f"No existe ninguna zona con el id {zona.id}")
        nuevas = ListaEnlazada()
        for existente in self._zonas:
            nuevas.insertar(zona if existente.id == zona.id else existente)
        self._zonas = nuevas
        self.guardar()

    def eliminar(self, id_zona: str) -> bool:
        """Borra la zona con ese id y guarda. False si no existía."""
        eliminada = self._zonas.eliminar(lambda zona: zona.id == id_zona)
        if eliminada:
            self.guardar()
        return eliminada

    def zonas_de(self, usuario: str) -> ListaEnlazada:
        """Zonas cuyo responsable es ese nombre de usuario."""
        suyas = ListaEnlazada()
        for zona in self._zonas:
            if zona.responsable == usuario:
                suyas.insertar(zona)
        return suyas

    def siguiente_id(self, prefijo: str) -> str:
        """Siguiente id libre: "Z4" para zonas, "S8" para sensores, "A4" para actuadores."""
        mayor = 0
        for id_existente in self._todos_los_ids():
            numero = id_existente[len(prefijo):]
            if id_existente.startswith(prefijo) and numero.isdigit():
                mayor = max(mayor, int(numero))
        return f"{prefijo}{mayor + 1}"

    def _todos_los_ids(self):
        """Va entregando los ids de todas las zonas, sensores y actuadores."""
        for zona in self._zonas:
            yield zona.id
            for sensor in zona.sensores:
                yield sensor.id
            for actuador in zona.actuadores:
                yield actuador.id
