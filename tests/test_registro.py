import json

import pytest

from controller.registro_controller import RegistroController
from model.usuario import JefeSanidad, ResponsableCarpa, TecnicoLogistica
from persistence.repositorio_json import RepositorioJSON


@pytest.fixture
def repositorio(tmp_path):
    return RepositorioJSON(tmp_path / "usuarios.json")


@pytest.fixture
def controlador(repositorio):
    return RegistroController(repositorio)


@pytest.mark.parametrize(
    ("rol", "clase"),
    [
        ("jefe_sanidad", JefeSanidad),
        ("responsable_carpa", ResponsableCarpa),
        ("tecnico_logistica", TecnicoLogistica),
    ],
)
def test_registrar_persiste_cada_rol_con_credenciales_hasheadas(
    controlador, repositorio, rol, clase
):
    resultado = controlador.registrar(
        " María López ", " maria ", "clave secreta", "clave secreta", rol
    )

    assert resultado is None
    recargado = RepositorioJSON(repositorio.ruta).buscar_por_usuario("maria")
    assert type(recargado) is clase
    assert recargado.nombre == "María López"
    assert recargado.verificar_password("clave secreta") is True
    assert recargado.verificar_password("incorrecta") is False
    texto = repositorio.ruta.read_text(encoding="utf-8")
    datos = json.loads(texto)
    assert len(datos) == 1
    assert datos[0]["sal"] == recargado.sal
    assert datos[0]["hash"] == recargado.contrasena_hash
    assert "clave secreta" not in texto


@pytest.mark.parametrize("campo", ["nombre", "usuario", "contrasena", "repetir", "rol"])
@pytest.mark.parametrize("valor", ["", " \t "])
def test_registrar_rechaza_campos_vacios_sin_guardar(controlador, repositorio, campo, valor):
    datos = {
        "nombre": "Ana",
        "usuario": "ana",
        "contrasena": "omero123",
        "repetir": "omero123",
        "rol": "jefe_sanidad",
    }
    datos[campo] = valor

    assert controlador.registrar(**datos) == "Rellena todos los campos"
    assert not repositorio.ruta.exists()
    assert len(repositorio.cargar()) == 0


def test_registrar_rechaza_contrasenas_distintas_sin_guardar(controlador, repositorio):
    resultado = controlador.registrar("Ana", "ana", "omero123", "otra", "jefe_sanidad")

    assert resultado == "Las contraseñas no coinciden"
    assert not repositorio.ruta.exists()


def test_registrar_rechaza_un_rol_desconocido_sin_guardar(controlador, repositorio):
    resultado = controlador.registrar("Ana", "ana", "omero123", "omero123", "administrador")

    assert resultado == "Selecciona un rol válido"
    assert not repositorio.ruta.exists()


def test_usuario_repetido_no_modifica_el_original(controlador, repositorio):
    assert controlador.registrar("Ana", "ana", "original", "original", "jefe_sanidad") is None
    contenido_original = repositorio.ruta.read_bytes()

    resultado = controlador.registrar(
        "Otra persona", " ana ", "distinta", "distinta", "tecnico_logistica"
    )

    assert resultado == "Ese usuario ya existe"
    assert repositorio.ruta.read_bytes() == contenido_original
    recargado = RepositorioJSON(repositorio.ruta)
    assert len(recargado.cargar()) == 1
    original = recargado.buscar_por_usuario("ana")
    assert original.nombre == "Ana"
    assert isinstance(original, JefeSanidad)
    assert original.verificar_password("original") is True
    assert original.verificar_password("distinta") is False


def test_contrasena_con_espacios_se_conserva(controlador, repositorio):
    contrasena = " contraseña con espacios "

    assert controlador.registrar(
        "Ana", "ana", contrasena, contrasena, "responsable_carpa"
    ) is None

    guardado = RepositorioJSON(repositorio.ruta).buscar_por_usuario("ana")
    assert guardado.verificar_password(contrasena) is True
    assert guardado.verificar_password(contrasena.strip()) is False


def test_error_de_escritura_no_se_confunde_con_un_usuario_duplicado(tmp_path):
    directorio = tmp_path / "datos"
    repositorio = RepositorioJSON(directorio / "usuarios.json")
    controlador = RegistroController(repositorio)
    directorio.write_text("Este archivo impide crear el directorio", encoding="utf-8")

    with pytest.raises(OSError):
        controlador.registrar("Ana", "ana", "omero123", "omero123", "jefe_sanidad")
