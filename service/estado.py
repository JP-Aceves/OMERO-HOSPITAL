"""Estado normal / aviso / crítico de sensores y zonas. Responsable: Medina (OME-40).

Regla (igual para todos los sensores, sin preguntar por el tipo):
- INVERSO = False: valor >= umbral_critico -> "critico"; valor >= umbral_aviso -> "aviso"; si no, "normal".
- INVERSO = True:  valor <= umbral_critico -> "critico"; valor <= umbral_aviso -> "aviso"; si no, "normal".
El estado de una zona es el peor de sus sensores (critico > aviso > normal).
"""
from model.lista_enlazada import ListaEnlazada
from model.sensor import Sensor

NORMAL = "normal"
AVISO = "aviso"
CRITICO = "critico"


def estado_sensor(sensor: Sensor, valor: float) -> str:
    raise NotImplementedError("OME-40")


def peor_estado(estados: ListaEnlazada) -> str:
    """De una ListaEnlazada de estados devuelve el más grave. Vacía -> "normal"."""
    raise NotImplementedError("OME-40")
