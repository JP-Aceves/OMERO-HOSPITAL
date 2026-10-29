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