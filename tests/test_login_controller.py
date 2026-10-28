"""Pruebas unitarias del login (OME-23)."""

from controller.login_controller import LoginController
from model.usuario import JefeSanidad, hashear
from persistence.repositorio_json import RepositorioJSON


def preparar_login(tmp_path):
    sal, hash_contrasena = hashear("omero123")
    usuario = JefeSanidad("Ana", "ana", hash_contrasena, sal)
    repositorio = RepositorioJSON(tmp_path / "usuarios.json")
    repositorio.anadir(usuario)
    return LoginController(repositorio), usuario


def test_login_correcto_devuelve_el_usuario(tmp_path):
    controlador, usuario = preparar_login(tmp_path)

    resultado = controlador.login("ana", "omero123")

    assert resultado is not None
    assert resultado.usuario == "ana"
    assert resultado.ROL == "jefe_sanidad"


def test_login_con_contrasena_incorrecta_devuelve_none(tmp_path):
    controlador, _ = preparar_login(tmp_path)

    assert controlador.login("ana", "incorrecta") is None


def test_login_con_usuario_inexistente_devuelve_none(tmp_path):
    controlador, _ = preparar_login(tmp_path)

    assert controlador.login("desconocido", "omero123") is None
