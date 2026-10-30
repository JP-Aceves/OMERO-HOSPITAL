from unittest.mock import Mock

import flet as ft
import pytest

from view.registro_view import RegistroView


def recorrer(controles):
    for control in controles:
        yield control
        yield from recorrer(getattr(control, "controls", None) or [])
        contenido = getattr(control, "content", None)
        if isinstance(contenido, ft.Control):
            yield from recorrer([contenido])


@pytest.fixture
def formulario():
    registrar = Mock(return_value=None)
    volver = Mock()
    vista = RegistroView(registrar, volver).construir()
    campos = {
        control.key: control
        for control in recorrer(vista.controls)
        if getattr(control, "key", None) is not None
    }
    return vista, campos, registrar, volver


def test_formulario_incluye_roles_y_oculta_las_contrasenas(formulario):
    vista, campos, _, _ = formulario

    assert vista.route == "/registro"
    for clave in ("nombre", "usuario", "contrasena", "repetir"):
        assert isinstance(campos[f"registro_{clave}"], ft.TextField)
    for clave in ("contrasena", "repetir"):
        assert campos[f"registro_{clave}"].password is True
        assert campos[f"registro_{clave}"].can_reveal_password is True
    assert {opcion.key for opcion in campos["registro_rol"].options} == {
        "jefe_sanidad", "responsable_carpa", "tecnico_logistica"
    }
    assert campos["registro_error"].visible is False


@pytest.mark.parametrize(
    "rol", ["jefe_sanidad", "responsable_carpa", "tecnico_logistica"]
)
def test_enviar_delega_los_datos_y_la_navegacion(formulario, monkeypatch, rol):
    _, campos, registrar, volver = formulario
    valores = ("María López", "maria", " clave ", " clave ", rol)
    for clave, valor in zip(
        ("nombre", "usuario", "contrasena", "repetir", "rol"), valores
    ):
        campos[f"registro_{clave}"].value = valor
    actualizar = Mock()
    monkeypatch.setattr(campos["registro_error"], "update", actualizar)

    campos["registro_enviar"].on_click(None)

    registrar.assert_called_once_with(*valores)
    volver.assert_not_called()
    actualizar.assert_not_called()


def test_campos_sin_valor_se_envian_como_cadenas_vacias(formulario):
    _, campos, registrar, _ = formulario

    campos["registro_enviar"].on_click(None)

    registrar.assert_called_once_with("", "", "", "", "")


def test_error_del_controlador_se_muestra_en_la_vista(formulario, monkeypatch):
    _, campos, registrar, volver = formulario
    registrar.return_value = "Ese usuario ya existe"
    actualizar = Mock()
    monkeypatch.setattr(campos["registro_error"], "update", actualizar)

    campos["registro_enviar"].on_click(None)

    assert campos["registro_error"].value == "Ese usuario ya existe"
    assert campos["registro_error"].visible is True
    actualizar.assert_called_once_with()
    volver.assert_not_called()


def test_volver_no_intenta_registrar(formulario):
    _, campos, registrar, volver = formulario

    campos["registro_volver"].on_click(None)

    volver.assert_called_once_with()
    registrar.assert_not_called()


def test_enter_en_repetir_contrasena_envia_el_formulario(formulario):
    _, campos, registrar, _ = formulario

    campos["registro_repetir"].on_submit(None)

    registrar.assert_called_once_with("", "", "", "", "")
