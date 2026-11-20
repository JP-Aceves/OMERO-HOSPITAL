"""Predicción del vaciado del depósito con regresión lineal. Responsable: Ivan (OME-65).

Ajusta una recta nivel = a + b · t por mínimos cuadrados (sin librerías externas),
con t en minutos desde la primera lectura, y calcula cuándo llega a 0 %.
"""
from datetime import datetime

from model.lista_enlazada import ListaEnlazada

MINIMO_LECTURAS = 5


def recta(lecturas: ListaEnlazada) -> tuple[float, float]:
    """(a, b) de la recta de mínimos cuadrados. b es la pendiente en % por minuto."""
    raise NotImplementedError("OME-65")


def predecir_vaciado(lecturas: ListaEnlazada) -> datetime | None:
    """Fecha y hora estimada en la que el depósito llega a 0 %.

    lecturas: Lectura del sensor nivel_deposito, en orden de fecha_hora.
    Devuelve None si hay menos de MINIMO_LECTURAS lecturas o si el nivel no baja (b >= 0).
    """
    raise NotImplementedError("OME-65")
