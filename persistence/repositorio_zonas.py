"""Lectura y escritura de zonas (con sus sensores y actuadores) en JSON. Responsable: Ivan (OME-34)."""
import json
from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock

from model.lista_enlazada import ListaEnlazada
from model.zona import Zona, crear_zona


_bloqueo_zonas = RLock()


class RepositorioZonas:

    def __init__(self, ruta: Path = Path("data/zonas.json")) -> None:
        self.ruta = Path(ruta)
        self._zonas = self.cargar()

    def cargar(self) -> ListaEnlazada:
        """Lee el JSON y devuelve una ListaEnlazada de Zona. Vacía si el fichero no existe."""
        zonas = ListaEnlazada()
        with _bloqueo_zonas:
            if self.ruta.exists():
                with self.ruta.open(encoding="utf-8") as fichero:
                    for datos in json.load(fichero):
                        zonas.insertar(crear_zona(datos))
        return zonas

    def recargar(self) -> None:
        """Vuelve a leer el JSON por si otra pantalla lo cambió (OME-64).

        Cada pantalla crea su propio repositorio: sin esto, el dashboard seguiría
        usando los umbrales que había al abrirlo aunque el jefe los cambie en
        "Zonas y sensores".
        """
        self._zonas = self.cargar()

    def guardar(self) -> None:
        """Escribe todas las zonas en el JSON."""
        with _bloqueo_zonas:
            self._guardar_zonas(self._zonas)

    def _guardar_zonas(self, zonas: ListaEnlazada) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        datos = [zona.to_dict() for zona in zonas]
        fichero = NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self.ruta.parent,
            prefix=f".{self.ruta.name}-", suffix=".tmp", delete=False,
        )
        temporal = Path(fichero.name)
        try:
            with fichero:
                json.dump(datos, fichero, ensure_ascii=False, indent=2)
            temporal.replace(self.ruta)
        finally:
            temporal.unlink(missing_ok=True)

    def modificar_estados(self, cambiar: Callable[[ListaEnlazada], bool]) -> None:
        """Aplica cambios de actuadores sobre la copia vigente y guarda si hubo cambios."""
        with _bloqueo_zonas:
            zonas = self.cargar()
            if cambiar(zonas):
                self._guardar_zonas(zonas)
            self._zonas = zonas

    def listar(self) -> ListaEnlazada:
        """Todas las zonas, en el orden del fichero."""
        return self._zonas

    def buscar(self, id_zona: str) -> Zona | None:
        """La zona con ese id, o None si no existe."""
        return self._zonas.buscar(lambda zona: zona.id == id_zona)

    def anadir(self, zona: Zona) -> None:
        """Guarda una zona nueva. ValueError si el id ya existe."""
        with _bloqueo_zonas:
            zonas = self.cargar()
            if zonas.buscar(lambda existente: existente.id == zona.id) is not None:
                raise ValueError(f"Ya existe una zona con el id {zona.id}")
            zonas.insertar(zona)
            self._guardar_zonas(zonas)
            self._zonas = zonas

    def actualizar(self, zona: Zona, *, conservar_estados: bool = False) -> None:
        """Sustituye la zona con ese id. El editor conserva los estados vigentes."""
        with _bloqueo_zonas:
            zonas = self.cargar()
            anterior = zonas.buscar(lambda existente: existente.id == zona.id)
            if anterior is None:
                raise ValueError(f"No existe ninguna zona con el id {zona.id}")
            if conservar_estados:
                for actuador in zona.actuadores:
                    vigente = anterior.actuadores.buscar(
                        lambda dato: dato.id == actuador.id and dato.tipo == actuador.tipo
                    )
                    if vigente is not None:
                        actuador.encendido = vigente.encendido
                        if vigente.estado is not None:
                            actuador.fijar_estado(vigente.estado)
            nuevas = ListaEnlazada()
            for existente in zonas:
                nuevas.insertar(zona if existente.id == zona.id else existente)
            self._guardar_zonas(nuevas)
            self._zonas = nuevas

    def eliminar(self, id_zona: str) -> bool:
        """Borra la zona con ese id y guarda. False si no existía."""
        with _bloqueo_zonas:
            zonas = self.cargar()
            eliminada = zonas.eliminar(lambda zona: zona.id == id_zona)
            if eliminada:
                self._guardar_zonas(zonas)
            self._zonas = zonas
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
