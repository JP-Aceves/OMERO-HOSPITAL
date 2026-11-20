"""Actuadores de una zona (ventilador y LEDs). Responsable: Medina (OME-31)."""


class Actuador:
    TIPOS = ("ventilador", "led_semaforo", "led_evacuacion")

    def __init__(
        self, id: str, nombre: str, tipo: str, encendido: bool = False,
        estado: str | None = None,
    ) -> None:
        """ValueError si el tipo no está en TIPOS."""
        if tipo not in self.TIPOS:
            raise ValueError(f"Tipo de actuador desconocido: {tipo}")
        self.id = id
        self.nombre = nombre
        self.tipo = tipo
        self.encendido = encendido
        self.estado: str | None = None
        if estado is not None:
            self.fijar_estado(estado)

    def encender(self) -> None:
        self.encendido = True

    def apagar(self) -> None:
        self.encendido = False

    def fijar_estado(self, estado: str) -> None:
        """Fija el color lógico del semáforo, conservando su encendido."""
        if self.tipo != "led_semaforo" or estado not in ("normal", "aviso", "critico"):
            raise ValueError("El semáforo admite los estados normal, aviso y critico")
        self.estado = estado

    def to_dict(self) -> dict:
        """Datos del actuador y, si se ha fijado, el estado del semáforo."""
        datos = {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "encendido": self.encendido,
        }
        if self.estado is not None:
            datos["estado"] = self.estado
        return datos


def crear_actuador(datos: dict) -> Actuador:
    return Actuador(
        id=datos["id"],
        nombre=datos["nombre"],
        tipo=datos["tipo"],
        encendido=datos.get("encendido", False),
        estado=datos.get("estado"),
    )
