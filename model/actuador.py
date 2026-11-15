"""Actuadores de una zona (ventilador y LEDs). Responsable: Medina (OME-31)."""


class Actuador:
    TIPOS = ("ventilador", "led_semaforo", "led_evacuacion")

    def __init__(self, id: str, nombre: str, tipo: str, encendido: bool = False) -> None:
        """ValueError si el tipo no está en TIPOS."""
        if tipo not in self.TIPOS:
            raise ValueError(f"Tipo de actuador desconocido: {tipo}")
        self.id = id
        self.nombre = nombre
        self.tipo = tipo
        self.encendido = encendido

    def encender(self) -> None:
        self.encendido = True

    def apagar(self) -> None:
        self.encendido = False

    def to_dict(self) -> dict:
        """{"id", "nombre", "tipo", "encendido"}."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "encendido": self.encendido,
        }


def crear_actuador(datos: dict) -> Actuador:
    return Actuador(
        id=datos["id"],
        nombre=datos["nombre"],
        tipo=datos["tipo"],
        encendido=datos.get("encendido", False),
    )
