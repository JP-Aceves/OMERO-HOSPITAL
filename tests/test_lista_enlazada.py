"""Pruebas de la lista enlazada (OME-30)."""
from model.lista_enlazada import ListaEnlazada


def lista_con(*datos):
    lista = ListaEnlazada()
    for dato in datos:
        lista.insertar(dato)
    return lista


def contenido(lista):
    """Recorre la lista y devuelve sus datos como texto, sin usar list."""
    return ",".join(str(dato) for dato in lista)


def test_lista_nueva_esta_vacia():
    lista = ListaEnlazada()

    assert len(lista) == 0
    assert lista.cabeza is None
    assert contenido(lista) == ""


def test_insertar_anade_al_final_y_mantiene_el_orden():
    lista = lista_con(1, 2, 3)

    assert len(lista) == 3
    assert contenido(lista) == "1,2,3"


def test_se_puede_recorrer_varias_veces():
    lista = lista_con(1, 2)

    assert contenido(lista) == contenido(lista) == "1,2"


def test_buscar_devuelve_el_primero_que_cumple():
    lista = lista_con(1, 4, 6)

    assert lista.buscar(lambda x: x % 2 == 0) == 4


def test_buscar_devuelve_none_si_no_hay_ninguno():
    lista = lista_con(1, 3)

    assert lista.buscar(lambda x: x > 10) is None
    assert ListaEnlazada().buscar(lambda x: True) is None


def test_eliminar_la_cabeza():
    lista = lista_con(1, 2, 3)

    assert lista.eliminar(lambda x: x == 1) is True
    assert contenido(lista) == "2,3"
    assert len(lista) == 2


def test_eliminar_en_medio():
    lista = lista_con(1, 2, 3)

    assert lista.eliminar(lambda x: x == 2) is True
    assert contenido(lista) == "1,3"


def test_eliminar_el_ultimo_y_seguir_insertando():
    lista = lista_con(1, 2, 3)

    assert lista.eliminar(lambda x: x == 3) is True
    lista.insertar(4)

    assert contenido(lista) == "1,2,4"
    assert len(lista) == 3


def test_eliminar_el_unico_elemento_deja_la_lista_vacia():
    lista = lista_con("a")

    assert lista.eliminar(lambda x: x == "a") is True
    assert len(lista) == 0
    assert lista.cabeza is None

    lista.insertar("b")
    assert contenido(lista) == "b"


def test_eliminar_solo_borra_el_primero_que_cumple():
    lista = lista_con(5, 5, 5)

    lista.eliminar(lambda x: x == 5)

    assert len(lista) == 2


def test_eliminar_sin_coincidencias_devuelve_false():
    lista = lista_con(1, 2)

    assert lista.eliminar(lambda x: x == 9) is False
    assert len(lista) == 2
    assert ListaEnlazada().eliminar(lambda x: True) is False


class Lectura:
    """Objeto cualquiera, como lo sería un Usuario o una lectura de sensor."""

    def __init__(self, sensor, valor):
        self.sensor = sensor
        self.valor = valor


def test_guarda_cualquier_tipo_de_objeto():
    temperatura = Lectura("DHT22", 24.5)
    humo = Lectura("MQ-2", 310)
    lista = lista_con(temperatura, humo, {"usuario": "ana"}, "texto")

    assert len(lista) == 4
    assert lista.buscar(lambda d: isinstance(d, Lectura) and d.sensor == "MQ-2") is humo
    assert lista.eliminar(lambda d: d is temperatura) is True
    assert lista.cabeza.dato is humo