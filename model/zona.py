"""Zonas del hospital de campaña. Responsable: Medina (OME-31).

Cada zona guarda sus sensores y sus actuadores en ListaEnlazada (no en list).
responsable es el nombre de usuario de quien la tiene asignada, o None.
"""
from model.actuador import Actuador, crear_actuador
from model.lista_enlazada import ListaEnlazada
from model.sensor import Sensor, crear_sensor


class Zona:
    TIPOS = ("carpa", "zona_tecnica", "exterior")

    def __init__(self, id: str, nombre: str, tipo: str, responsable: str | None = None) -> None:
        """Crea self.sensores y self.actuadores como ListaEnlazada vacías. ValueError si el tipo no es válido."""
        if tipo not in self.TIPOS:
            raise ValueError(f"Tipo de zona desconocido: {tipo}")
        self.id = id
        self.nombre = nombre
        self.tipo = tipo
        self.responsable = responsable
        self.sensores = ListaEnlazada()
        self.actuadores = ListaEnlazada()

    def anadir_sensor(self, sensor: Sensor) -> None:
        """ValueError si ya hay un sensor con ese id."""
        if self.buscar_sensor(sensor.id) is not None:
            raise ValueError(f"Ya existe un sensor con el id {sensor.id}")
        self.sensores.insertar(sensor)

    def eliminar_sensor(self, id_sensor: str) -> bool:
        return self.sensores.eliminar(lambda sensor: sensor.id == id_sensor)

    def buscar_sensor(self, id_sensor: str) -> Sensor | None:
        return self.sensores.buscar(lambda sensor: sensor.id == id_sensor)

    def anadir_actuador(self, actuador: Actuador) -> None:
        """ValueError si ya hay un actuador con ese id."""
        if self.actuadores.buscar(lambda elemento: elemento.id == actuador.id) is not None:
            raise ValueError(f"Ya existe un actuador con el id {actuador.id}")
        self.actuadores.insertar(actuador)

    def eliminar_actuador(self, id_actuador: str) -> bool:
        return self.actuadores.eliminar(lambda actuador: actuador.id == id_actuador)

    def to_dict(self) -> dict:
        """{"id", "nombre", "tipo", "responsable", "sensores": [...], "actuadores": [...]}."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "responsable": self.responsable,
            "sensores": [sensor.to_dict() for sensor in self.sensores],
            "actuadores": [actuador.to_dict() for actuador in self.actuadores],
        }


def crear_zona(datos: dict) -> Zona:
    """Lo contrario de to_dict. Usa crear_sensor y crear_actuador."""
    zona = Zona(datos["id"], datos["nombre"], datos["tipo"], datos.get("responsable"))
    for sensor in datos.get("sensores", ()):
        zona.anadir_sensor(crear_sensor(sensor))
    for actuador in datos.get("actuadores", ()):
        zona.anadir_actuador(crear_actuador(actuador))
    return zona
