"""Pruebas de la navegación por rol. Responsable: JP (OME-25)."""
import pytest

from controller.navegacion import MENU_POR_ROL, puede_acceder, ruta_inicial


@pytest.mark.parametrize("rol, ruta", [
    ("jefe_sanidad", "/inicio"),
    ("responsable_carpa", "/inicio"),
    ("tecnico_logistica", "/inicio"),
    ("administrador", "/usuarios"),
])
def test_cada_rol_empieza_en_su_ruta(rol, ruta):
    assert ruta_inicial(rol) == ruta


def test_un_rol_desconocido_vuelve_al_login():
    assert ruta_inicial("pirata") == "/login"


def test_el_jefe_entra_a_zonas_y_los_demas_no():
    assert puede_acceder("jefe_sanidad", "/zonas")
    assert not puede_acceder("responsable_carpa", "/zonas")
    assert not puede_acceder("tecnico_logistica", "/zonas")


def test_solo_el_admin_gestiona_usuarios():
    assert puede_acceder("administrador", "/usuarios")
    for rol in ("jefe_sanidad", "responsable_carpa", "tecnico_logistica"):
        assert not puede_acceder(rol, "/usuarios")


def test_el_admin_no_tiene_inicio_de_zonas():
    assert not puede_acceder("administrador", "/inicio")


def test_cada_ruta_del_menu_se_puede_abrir():
    for rol, menu in MENU_POR_ROL.items():
        for _, ruta in menu:
            assert puede_acceder(rol, ruta)
