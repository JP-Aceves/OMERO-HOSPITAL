"""Genera y filtra las alertas a partir de las lecturas. Responsable: Medina (OME-60).

La regla de cuándo hay alerta es la misma que la del semáforo (service/estado.py):
un sensor en "aviso" o "critico" genera una Alerta; en "normal", ninguna.
"""
from model.lista_enlazada import ListaEnlazada


def alertas_de_ronda(zonas: ListaEnlazada, lecturas: ListaEnlazada) -> ListaEnlazada:
    """Una Alerta por cada lectura de la ronda que esté en aviso o crítico.

    zonas: las Zona del repositorio (para encontrar el sensor y sus umbrales).
    lecturas: las Lectura de la última ronda.
    """
    raise NotImplementedError("OME-60")


def alertas_de_zonas(alertas: ListaEnlazada, ids_zona: ListaEnlazada) -> ListaEnlazada:
    """Solo las alertas de esas zonas (lo que ve el responsable de carpa o el técnico)."""
    raise NotImplementedError("OME-60")


def hay_alerta_critica(alertas: ListaEnlazada, tipo: str = "humo_gas") -> bool:
    """True si hay alguna alerta crítica de ese tipo de sensor. La usa el LED de evacuación (OME-66)."""
    raise NotImplementedError("OME-60")
