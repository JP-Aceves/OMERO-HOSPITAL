"""Alerta que salta cuando una lectura pasa a aviso o crítico. Responsable: Medina (OME-60).

{"zona": "Z1", "sensor": "S1", "tipo": "temperatura", "valor": 33.2, "unidad": "°C",
 "nivel": "critico", "fecha_hora": "2026-11-24T18:30:00"}
nivel es "aviso" o "critico" (las constantes de service/estado.py).
"""


class Alerta:

    def __init__(self, zona: str, sensor: str, tipo: str, valor: float, unidad: str,
                 nivel: str, fecha_hora: str) -> None:
        raise NotImplementedError("OME-60")

    def to_dict(self) -> dict:
        raise NotImplementedError("OME-60")
