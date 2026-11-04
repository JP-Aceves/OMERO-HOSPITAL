"""Una lectura de un sensor, con el mismo formato que enviará el ESP32. Responsable: Medina (OME-31).

{"zona": "Z1", "sensor": "S1", "tipo": "temperatura", "valor": 31.4, "unidad": "°C", "fecha_hora": "2026-11-10T18:30:00"}
"""


class Lectura:

    def __init__(self, zona: str, sensor: str, tipo: str, valor: float, unidad: str, fecha_hora: str) -> None:
        raise NotImplementedError("OME-31")

    def to_dict(self) -> dict:
        raise NotImplementedError("OME-31")

    @staticmethod
    def desde_dict(datos: dict) -> "Lectura":
        raise NotImplementedError("OME-31")
