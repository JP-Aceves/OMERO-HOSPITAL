"""Predicción del vaciado del depósito con regresión lineal. Responsable: Ivan (OME-65).

Ajusta una recta nivel = a + b · t por mínimos cuadrados (sin librerías externas),
con t en minutos desde la primera lectura, y calcula cuándo llega a 0 %.
"""
from datetime import datetime, timedelta

from model.lista_enlazada import ListaEnlazada

MINIMO_LECTURAS = 5

# Si el nivel sube más de esto entre dos lecturas seguidas, el depósito se ha
# rellenado. El simulador rellena del 10 % al 90-100 % (sube más de 80 puntos);
# con 10 puntos de margen el ruido pequeño del HC-SR04 real no cuenta como rellenado.
SUBIDA_RELLENADO = 10


def _minutos(desde: datetime, hasta: datetime) -> float:
    return (hasta - desde).total_seconds() / 60


def recta(lecturas: ListaEnlazada) -> tuple[float, float]:
    """(a, b) de la recta de mínimos cuadrados. b es la pendiente en % por minuto.

    a es el nivel que marca la recta en la primera lectura (t = 0).
    ValueError si hay menos de 2 lecturas o si todas tienen la misma hora.
    """
    n = 0
    suma_t = suma_y = suma_tt = suma_ty = 0.0
    inicio = None
    for lectura in lecturas:
        momento = datetime.fromisoformat(lectura.fecha_hora)
        if inicio is None:
            inicio = momento
        t = _minutos(inicio, momento)
        y = lectura.valor
        n += 1
        suma_t += t
        suma_y += y
        suma_tt += t * t
        suma_ty += t * y

    denominador = n * suma_tt - suma_t * suma_t
    if n < 2 or denominador == 0:
        raise ValueError("Hacen falta al menos dos lecturas en horas distintas")
    b = (n * suma_ty - suma_t * suma_y) / denominador
    a = (suma_y - b * suma_t) / n
    return a, b


def ultimo_tramo(lecturas: ListaEnlazada) -> ListaEnlazada:
    """Las lecturas desde el último rellenado del depósito.

    Con el histórico completo la gráfica es un diente de sierra (baja, se rellena,
    vuelve a bajar) y una sola recta no sirve para predecir.
    """
    tramo = ListaEnlazada()
    anterior = None
    for lectura in lecturas:
        if anterior is not None and lectura.valor - anterior > SUBIDA_RELLENADO:
            tramo = ListaEnlazada()
        tramo.insertar(lectura)
        anterior = lectura.valor
    return tramo


def predecir_vaciado(lecturas: ListaEnlazada) -> datetime | None:
    """Fecha y hora estimada en la que el depósito llega a 0 %.

    lecturas: Lectura del sensor nivel_deposito, en orden de fecha_hora.
    Solo usa las lecturas desde el último rellenado (ultimo_tramo).
    Devuelve None si en ese tramo hay menos de MINIMO_LECTURAS lecturas o si el nivel no baja (b >= 0).
    """
    tramo = ultimo_tramo(lecturas)
    if len(tramo) < MINIMO_LECTURAS:
        return None
    try:
        a, b = recta(tramo)
    except ValueError:
        return None
    if b >= 0:
        return None

    # La recta corta el 0 % cuando a + b · t = 0, es decir, en t = -a / b minutos.
    inicio = datetime.fromisoformat(next(iter(tramo)).fecha_hora)
    return (inicio + timedelta(minutes=-a / b)).replace(microsecond=0)
