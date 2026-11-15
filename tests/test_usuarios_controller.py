from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from controller.usuarios_controller import UsuariosController
from model.lista_enlazada import ListaEnlazada
from model.usuario import Administrador, TecnicoLogistica, crear_usuario, hashear
from persistence.repositorio_json import RepositorioJSON


CONTRASENA = "contraseña de prueba"


def _anadir_cuenta(repositorio, usuario, rol):
    sal, hash_contrasena = hashear(CONTRASENA)
    cuenta = crear_usuario({
        "nombre": usuario.capitalize(),
        "usuario": usuario,
        "rol": rol,
        "sal": sal,
        "hash": hash_contrasena,
    })
    repositorio.anadir(cuenta)
    return cuenta


@pytest.fixture
def usuarios(tmp_path):
    repositorio = RepositorioJSON(tmp_path / "usuarios.json")
    admin = _anadir_cuenta(repositorio, "admin", "administrador")
    tecnico = _anadir_cuenta(repositorio, "tecnico", "tecnico_logistica")
    return UsuariosController(repositorio), repositorio, admin, tecnico


def test_listar_devuelve_las_cuentas_en_una_lista_enlazada(usuarios):
    controlador, _, _, _ = usuarios

    cuentas = controlador.listar()

    assert isinstance(cuentas, ListaEnlazada)
    assert {cuenta.usuario for cuenta in cuentas} == {"admin", "tecnico"}


def test_cambiar_rol_persiste_la_subclase_sin_modificar_credenciales(usuarios):
    controlador, repositorio, _, tecnico = usuarios
    datos_originales = tecnico.to_dict()

    assert controlador.cambiar_rol("tecnico", "administrador") is None

    recargado = RepositorioJSON(repositorio.ruta).buscar_por_usuario("tecnico")
    assert isinstance(recargado, Administrador)
    assert recargado.to_dict() == {**datos_originales, "rol": "administrador"}
    assert recargado.verificar_password(CONTRASENA)


def test_cambiar_rol_permite_degradar_a_un_admin_si_queda_otro(usuarios):
    controlador, repositorio, _, _ = usuarios
    _anadir_cuenta(repositorio, "otro_admin", "administrador")

    assert controlador.cambiar_rol("admin", "tecnico_logistica") is None

    recargado = RepositorioJSON(repositorio.ruta)
    assert isinstance(recargado.buscar_por_usuario("admin"), TecnicoLogistica)
    assert isinstance(recargado.buscar_por_usuario("otro_admin"), Administrador)


def test_dos_cambios_simultaneos_conservan_un_administrador(usuarios):
    controlador, repositorio, _, _ = usuarios
    _anadir_cuenta(repositorio, "otro_admin", "administrador")
    inicio = Barrier(2, timeout=5)

    def degradar(nombre_usuario):
        inicio.wait()
        return controlador.cambiar_rol(nombre_usuario, "tecnico_logistica")

    with ThreadPoolExecutor(max_workers=2) as hilos:
        resultados = tuple(hilos.map(degradar, ("admin", "otro_admin")))

    assert resultados.count(None) == 1
    assert "Debe quedar al menos un administrador" in resultados
    recargado = RepositorioJSON(repositorio.ruta)
    assert sum(cuenta.ROL == Administrador.ROL for cuenta in recargado.cargar()) == 1


@pytest.mark.parametrize(
    ("usuario", "rol", "error"),
    [
        ("tecnico", "desconocido", "Selecciona un rol válido"),
        ("no_existe", "administrador", "El usuario no existe"),
        ("admin", "tecnico_logistica", "Debe quedar al menos un administrador"),
    ],
)
def test_cambiar_rol_rechaza_la_operacion_sin_modificar_json(usuarios, usuario, rol, error):
    controlador, repositorio, _, _ = usuarios
    contenido_original = repositorio.ruta.read_bytes()

    assert controlador.cambiar_rol(usuario, rol) == error
    assert repositorio.ruta.read_bytes() == contenido_original


@pytest.mark.parametrize("usuario", ["tecnico", "otro_admin"])
def test_eliminar_persiste_la_baja_si_queda_un_admin(usuarios, usuario):
    controlador, repositorio, admin, _ = usuarios
    if usuario == "otro_admin":
        _anadir_cuenta(repositorio, usuario, "administrador")

    assert controlador.eliminar(usuario, admin) is None

    recargado = RepositorioJSON(repositorio.ruta)
    assert recargado.buscar_por_usuario(usuario) is None
    assert isinstance(recargado.buscar_por_usuario("admin"), Administrador)


def test_eliminar_rechaza_borrarse_a_si_mismo_aunque_haya_otro_admin(usuarios):
    controlador, repositorio, admin, _ = usuarios
    _anadir_cuenta(repositorio, "otro_admin", "administrador")
    contenido_original = repositorio.ruta.read_bytes()

    assert controlador.eliminar("admin", admin) == "No puedes eliminar tu propia cuenta"
    assert repositorio.ruta.read_bytes() == contenido_original


def test_eliminar_rechaza_una_cuenta_inexistente(usuarios):
    controlador, repositorio, admin, _ = usuarios
    contenido_original = repositorio.ruta.read_bytes()

    assert controlador.eliminar("no_existe", admin) == "El usuario no existe"
    assert repositorio.ruta.read_bytes() == contenido_original


def test_eliminar_rechaza_a_un_usuario_sin_rol_de_administrador(usuarios):
    controlador, repositorio, _, tecnico = usuarios
    _anadir_cuenta(repositorio, "otra_cuenta", "responsable_carpa")
    contenido_original = repositorio.ruta.read_bytes()

    assert controlador.eliminar("otra_cuenta", tecnico) == "Solo un administrador puede eliminar usuarios"
    assert repositorio.ruta.read_bytes() == contenido_original


def test_eliminar_rechaza_a_un_admin_degradado_aunque_la_sesion_sea_anterior(usuarios):
    controlador, repositorio, admin, _ = usuarios
    _anadir_cuenta(repositorio, "otro_admin", "administrador")
    assert controlador.cambiar_rol("admin", "tecnico_logistica") is None
    contenido_original = repositorio.ruta.read_bytes()

    assert controlador.eliminar("tecnico", admin) == "Solo un administrador puede eliminar usuarios"
    assert repositorio.ruta.read_bytes() == contenido_original
