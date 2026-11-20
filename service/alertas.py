"""Genera y filtra las alertas a partir de las lecturas. Responsable: Medina (OME-60).

La regla de cuándo hay alerta es la misma que la del semáforo (service/estado.py):
un sensor en "aviso" o "critico" genera una Alerta; en "normal", ninguna.
"""
from model.alerta import Alerta
from model.lista_enlazada import ListaEnlazada
from service.estado import CRITICO, NORMAL, estado_sensor


def alertas_de_ronda(zonas: ListaEnlazada, lecturas: ListaEnlazada) -> ListaEnlazada:
    """Una alerta por sensor cuya última lectura esté en aviso o crítico.

    zonas: las Zona del repositorio (para encontrar el sensor y sus umbrales).
    lecturas: las Lectura de la última ronda.
    """
    alertas = ListaEnlazada()
    for lectura in lecturas:
        zona = zonas.buscar(lambda dato: dato.id == lectura.zona)
        if zona is None:
            continue
        sensor = zona.buscar_sensor(lectura.sensor)
        if sensor is None or sensor.TIPO != lectura.tipo:
            continue
        alertas.eliminar(
            lambda alerta: alerta.zona == lectura.zona and alerta.sensor == lectura.sensor
        )
        nivel = estado_sensor(sensor, lectura.valor)
        if nivel != NORMAL:
            alertas.insertar(Alerta(
                lectura.zona, lectura.sensor, lectura.tipo, lectura.valor,
                lectura.unidad, nivel, lectura.fecha_hora,
            ))
    return alertas


def alertas_de_zonas(alertas: ListaEnlazada, ids_zona: ListaEnlazada) -> ListaEnlazada:
    """Solo las alertas de esas zonas (lo que ve el responsable de carpa o el técnico)."""
    filtradas = ListaEnlazada()
    for alerta in alertas:
        if ids_zona.buscar(lambda id_zona: id_zona == alerta.zona) is not None:
            filtradas.insertar(alerta)
    return filtradas


def hay_alerta_critica(alertas: ListaEnlazada, tipo: str = "humo_gas") -> bool:
    """True si hay alguna alerta crítica de ese tipo de sensor. La usa el LED de evacuación (OME-66)."""
    return any(alerta.nivel == CRITICO and alerta.tipo == tipo for alerta in alertas)
