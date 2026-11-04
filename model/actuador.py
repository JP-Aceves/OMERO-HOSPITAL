"""Actuadores de una zona (ventilador y LEDs). Responsable: Medina (OME-31)."""


class Actuador:
    TIPOS = ("ventilador", "led_semaforo", "led_evacuacion")

    def __init__(self, id: str, nombre: str, tipo: str, encendido: bool = False) -> None:
        """ValueError si el tipo no está en TIPOS."""
        raise NotImplementedError("OME-31")

    def encender(self) -> None:
        raise NotImplementedError("OME-31")

    def apagar(self) -> None:
        raise NotImplementedError("OME-31")

    def to_dict(self) -> dict:
        """{"id", "nombre", "tipo", "encendido"}."""
        raise NotImplementedError("OME-31")


def crear_actuador(datos: dict) -> Actuador:
    raise NotImplementedError("OME-31")
