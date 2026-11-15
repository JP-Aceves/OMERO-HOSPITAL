"""Una lectura de un sensor, con el mismo formato que enviará el ESP32. Responsable: Medina (OME-31).

{"zona": "Z1", "sensor": "S1", "tipo": "temperatura", "valor": 31.4, "unidad": "°C", "fecha_hora": "2026-11-10T18:30:00"}
"""


class Lectura:

    def __init__(self, zona: str, sensor: str, tipo: str, valor: float, unidad: str, fecha_hora: str) -> None:
        self.zona = zona
        self.sensor = sensor
        self.tipo = tipo
        self.valor = valor
        self.unidad = unidad
        self.fecha_hora = fecha_hora

    def to_dict(self) -> dict:
        return {
            "zona": self.zona,
            "sensor": self.sensor,
            "tipo": self.tipo,
            "valor": self.valor,
            "unidad": self.unidad,
            "fecha_hora": self.fecha_hora,
        }

    @staticmethod
    def desde_dict(datos: dict) -> "Lectura":
        return Lectura(
            zona=datos["zona"],
            sensor=datos["sensor"],
            tipo=datos["tipo"],
            valor=datos["valor"],
            unidad=datos["unidad"],
            fecha_hora=datos["fecha_hora"],
        )
