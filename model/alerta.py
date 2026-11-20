"""Alerta que salta cuando una lectura pasa a aviso o crítico. Responsable: Medina (OME-60).

{"zona": "Z1", "sensor": "S1", "tipo": "temperatura", "valor": 33.2, "unidad": "°C",
 "nivel": "critico", "fecha_hora": "2026-11-24T18:30:00"}
nivel es "aviso" o "critico" (las constantes de service/estado.py).
"""


class Alerta:

    def __init__(self, zona: str, sensor: str, tipo: str, valor: float, unidad: str,
                 nivel: str, fecha_hora: str) -> None:
        if nivel not in ("aviso", "critico"):
            raise ValueError("Una alerta debe ser de aviso o critica")
        self.zona = zona
        self.sensor = sensor
        self.tipo = tipo
        self.valor = valor
        self.unidad = unidad
        self.nivel = nivel
        self.fecha_hora = fecha_hora

    def to_dict(self) -> dict:
        return {
            "zona": self.zona,
            "sensor": self.sensor,
            "tipo": self.tipo,
            "valor": self.valor,
            "unidad": self.unidad,
            "nivel": self.nivel,
            "fecha_hora": self.fecha_hora,
        }
