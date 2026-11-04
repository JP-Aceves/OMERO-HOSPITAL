"""Zonas del hospital de campaña. Responsable: Medina (OME-31).

Cada zona guarda sus sensores y sus actuadores en ListaEnlazada (no en list).
responsable es el nombre de usuario de quien la tiene asignada, o None.
"""
from model.actuador import Actuador
from model.sensor import Sensor


class Zona:
    TIPOS = ("carpa", "zona_tecnica", "exterior")

    def __init__(self, id: str, nombre: str, tipo: str, responsable: str | None = None) -> None:
        """Crea self.sensores y self.actuadores como ListaEnlazada vacías. ValueError si el tipo no es válido."""
        raise NotImplementedError("OME-31")

    def anadir_sensor(self, sensor: Sensor) -> None:
        """ValueError si ya hay un sensor con ese id."""
        raise NotImplementedError("OME-31")

    def eliminar_sensor(self, id_sensor: str) -> bool:
        raise NotImplementedError("OME-31")

    def buscar_sensor(self, id_sensor: str) -> Sensor | None:
        raise NotImplementedError("OME-31")

    def anadir_actuador(self, actuador: Actuador) -> None:
        """ValueError si ya hay un actuador con ese id."""
        raise NotImplementedError("OME-31")

    def eliminar_actuador(self, id_actuador: str) -> bool:
        raise NotImplementedError("OME-31")

    def to_dict(self) -> dict:
        """{"id", "nombre", "tipo", "responsable", "sensores": [...], "actuadores": [...]}."""
        raise NotImplementedError("OME-31")


def crear_zona(datos: dict) -> Zona:
    """Lo contrario de to_dict. Usa crear_sensor y crear_actuador."""
    raise NotImplementedError("OME-31")
