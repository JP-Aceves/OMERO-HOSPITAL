from pathlib import Path

import pytest

from controller.zonas_controller import ZonasController
from model.lista_enlazada import ListaEnlazada
from model.usuario import crear_usuario, hashear
from persistence.repositorio_json import RepositorioJSON
from persistence.repositorio_zonas import RepositorioZonas


def _crear_cuenta(repositorio, nombre, usuario, rol):
    sal, hash_contrasena = hashear("clave de prueba")
    cuenta = crear_usuario({
        "nombre": nombre,
        "usuario": usuario,
        "rol": rol,
        "sal": sal,
        "hash": hash_contrasena,
    })
    repositorio.anadir(cuenta)
    return cuenta


@pytest.fixture
def contexto(tmp_path):
    ruta_zonas = tmp_path / "zonas.json"
    datos_zonas = Path(__file__).parents[1] / "data" / "zonas.json"
    ruta_zonas.write_text(datos_zonas.read_text(encoding="utf-8"), encoding="utf-8")
    repo_zonas = RepositorioZonas(ruta_zonas)
    repo_usuarios = RepositorioJSON(tmp_path / "usuarios.json")
    jefe = _crear_cuenta(repo_usuarios, "Jefe", "jefe", "jefe_sanidad")
    responsable = _crear_cuenta(repo_usuarios, "Responsable", "carpa", "responsable_carpa")
    tecnico = _crear_cuenta(repo_usuarios, "Técnico", "logistica", "tecnico_logistica")
    administrador = _crear_cuenta(repo_usuarios, "Admin", "admin", "administrador")
    controlador = ZonasController(repo_zonas, repo_usuarios)
    return controlador, repo_zonas, repo_usuarios, jefe, responsable, tecnico, administrador


def test_listar_jefe_devuelve_todas_las_zonas(contexto):
    controlador, _, _, jefe, *_ = contexto

    zonas = controlador.listar(jefe)

    assert isinstance(zonas, ListaEnlazada)
    assert {zona.id for zona in zonas} == {"Z1", "Z2", "Z3"}


@pytest.mark.parametrize(("indice_usuario", "esperadas"), [(4, {"Z1"}), (5, {"Z2", "Z3"})])
def test_listar_responsable_y_tecnico_solo_devuelve_sus_zonas(contexto, indice_usuario, esperadas):
    controlador, _, _, _, responsable, tecnico, _ = contexto
    usuario = responsable if indice_usuario == 4 else tecnico

    zonas = controlador.listar(usuario)

    assert {zona.id for zona in zonas} == esperadas


def test_listar_rol_no_operativo_devuelve_lista_vacia(contexto):
    controlador, _, _, _, _, _, administrador = contexto

    zonas = controlador.listar(administrador)

    assert isinstance(zonas, ListaEnlazada)
    assert len(zonas) == 0


def test_crear_zona_asigna_id_z4_y_persiste(contexto):
    controlador, repo_zonas, *_ = contexto

    assert controlador.crear_zona("  Almacén  ", "exterior", None) is None

    recargado = RepositorioZonas(repo_zonas.ruta)
    zona = recargado.buscar("Z4")
    assert zona is not None
    assert (zona.nombre, zona.tipo, zona.responsable) == ("Almacén", "exterior", None)


@pytest.mark.parametrize(
    ("nombre", "tipo", "responsable", "error"),
    [
        ("   ", "carpa", None, "El nombre de la zona es obligatorio"),
        ("Almacén", "desconocido", None, "Selecciona un tipo de zona válido"),
        ("Almacén", "carpa", "no_existe", "El usuario responsable no existe"),
        (
            "Almacén", "carpa", "jefe",
            "Solo se puede asignar a responsables de carpa o técnicos de logística",
        ),
    ],
)
def test_crear_zona_rechaza_datos_invalidos_sin_persistir(contexto, nombre, tipo, responsable, error):
    controlador, repo_zonas, *_ = contexto
    original = repo_zonas.ruta.read_bytes()

    assert controlador.crear_zona(nombre, tipo, responsable) == error
    assert repo_zonas.ruta.read_bytes() == original


def test_editar_zona_actualiza_campos_sin_perder_dispositivos(contexto):
    controlador, repo_zonas, *_ = contexto

    assert controlador.editar_zona("Z1", "Carpa ampliada", "carpa", "logistica") is None

    recargada = RepositorioZonas(repo_zonas.ruta).buscar("Z1")
    assert recargada.nombre == "Carpa ampliada"
    assert recargada.responsable == "logistica"
    assert len(recargada.sensores) == 4
    assert len(recargada.actuadores) == 2


@pytest.mark.parametrize(
    ("id_zona", "nombre", "tipo", "responsable", "error"),
    [
        ("Z99", "Nueva", "carpa", None, "La zona no existe"),
        ("Z1", " ", "carpa", None, "El nombre de la zona es obligatorio"),
        ("Z1", "Nueva", "otro", None, "Selecciona un tipo de zona válido"),
        ("Z1", "Nueva", "carpa", "admin", "Solo se puede asignar a responsables de carpa o técnicos de logística"),
    ],
)
def test_editar_zona_rechaza_datos_invalidos_sin_persistir(contexto, id_zona, nombre, tipo, responsable, error):
    controlador, repo_zonas, *_ = contexto
    original = repo_zonas.ruta.read_bytes()

    assert controlador.editar_zona(id_zona, nombre, tipo, responsable) == error
    assert repo_zonas.ruta.read_bytes() == original


def test_editar_zona_puede_quitar_responsable(contexto):
    controlador, repo_zonas, *_ = contexto

    assert controlador.editar_zona("Z1", "Carpa", "carpa", "  ") is None

    assert RepositorioZonas(repo_zonas.ruta).buscar("Z1").responsable is None


def test_eliminar_zona_persiste_la_baja(contexto):
    controlador, repo_zonas, *_ = contexto

    assert controlador.eliminar_zona("Z3") is None
    assert RepositorioZonas(repo_zonas.ruta).buscar("Z3") is None


def test_eliminar_zona_inexistente_devuelve_error(contexto):
    controlador, repo_zonas, *_ = contexto
    original = repo_zonas.ruta.read_bytes()

    assert controlador.eliminar_zona("Z99") == "La zona no existe"
    assert repo_zonas.ruta.read_bytes() == original


def test_anadir_sensor_asigna_id_s8_y_persiste(contexto):
    controlador, repo_zonas, *_ = contexto

    assert controlador.anadir_sensor("Z1", "Sensor extra", "humedad", "45", "65") is None

    recargada = RepositorioZonas(repo_zonas.ruta).buscar("Z1")
    sensor = recargada.buscar_sensor("S8")
    assert sensor is not None
    assert (sensor.nombre, sensor.TIPO, sensor.umbral_aviso, sensor.umbral_critico) == (
        "Sensor extra", "humedad", 45.0, 65.0
    )


@pytest.mark.parametrize(
    ("id_zona", "nombre", "tipo", "aviso", "critico", "error"),
    [
        ("Z99", "Sensor", "temperatura", "10", "20", "La zona no existe"),
        ("Z1", " ", "temperatura", "10", "20", "El nombre del sensor es obligatorio"),
        ("Z1", "Sensor", "desconocido", "10", "20", "Selecciona un tipo de sensor válido"),
        ("Z1", "Sensor", "temperatura", "x", "20", "Los umbrales deben ser números válidos"),
        ("Z1", "Sensor", "temperatura", "10", "x", "Los umbrales deben ser números válidos"),
        ("Z1", "Sensor", "temperatura", "nan", "20", "Los umbrales deben ser números válidos"),
        ("Z1", "Sensor", "temperatura", "inf", "20", "Los umbrales deben ser números válidos"),
    ],
)
def test_anadir_sensor_rechaza_datos_invalidos_sin_persistir(
    contexto, id_zona, nombre, tipo, aviso, critico, error
):
    controlador, repo_zonas, *_ = contexto
    original = repo_zonas.ruta.read_bytes()

    assert controlador.anadir_sensor(id_zona, nombre, tipo, aviso, critico) == error
    assert repo_zonas.ruta.read_bytes() == original


def test_editar_sensor_actualiza_nombre_y_umbrales(contexto):
    controlador, repo_zonas, *_ = contexto

    assert controlador.editar_sensor("Z1", "S1", "Temperatura interior", "29", "33") is None

    sensor = RepositorioZonas(repo_zonas.ruta).buscar("Z1").buscar_sensor("S1")
    assert (sensor.nombre, sensor.TIPO, sensor.umbral_aviso, sensor.umbral_critico) == (
        "Temperatura interior", "temperatura", 29.0, 33.0
    )


@pytest.mark.parametrize(
    ("id_zona", "id_sensor", "nombre", "aviso", "critico", "error"),
    [
        ("Z99", "S1", "Nuevo", "1", "2", "La zona no existe"),
        ("Z1", "S99", "Nuevo", "1", "2", "El sensor no existe en esa zona"),
        ("Z1", "S1", " ", "1", "2", "El nombre del sensor es obligatorio"),
        ("Z1", "S1", "Nuevo", "x", "2", "Los umbrales deben ser números válidos"),
        ("Z1", "S1", "Nuevo", "1", "nan", "Los umbrales deben ser números válidos"),
    ],
)
def test_editar_sensor_rechaza_datos_invalidos_sin_persistir(
    contexto, id_zona, id_sensor, nombre, aviso, critico, error
):
    controlador, repo_zonas, *_ = contexto
    original = repo_zonas.ruta.read_bytes()

    assert controlador.editar_sensor(id_zona, id_sensor, nombre, aviso, critico) == error
    assert repo_zonas.ruta.read_bytes() == original


def test_eliminar_sensor_persiste_la_baja(contexto):
    controlador, repo_zonas, *_ = contexto

    assert controlador.eliminar_sensor("Z1", "S1") is None
    assert RepositorioZonas(repo_zonas.ruta).buscar("Z1").buscar_sensor("S1") is None


@pytest.mark.parametrize(
    ("id_zona", "id_sensor", "error"),
    [("Z99", "S1", "La zona no existe"), ("Z1", "S99", "El sensor no existe en esa zona")],
)
def test_eliminar_sensor_inexistente_devuelve_error(contexto, id_zona, id_sensor, error):
    controlador, repo_zonas, *_ = contexto
    original = repo_zonas.ruta.read_bytes()

    assert controlador.eliminar_sensor(id_zona, id_sensor) == error
    assert repo_zonas.ruta.read_bytes() == original


def test_anadir_actuador_asigna_id_a4_y_persiste(contexto):
    controlador, repo_zonas, *_ = contexto

    assert controlador.anadir_actuador("Z1", "Ventilador auxiliar", "ventilador") is None

    recargada = RepositorioZonas(repo_zonas.ruta).buscar("Z1")
    actuador = recargada.actuadores.buscar(lambda elemento: elemento.id == "A4")
    assert actuador is not None
    assert (actuador.nombre, actuador.tipo, actuador.encendido) == (
        "Ventilador auxiliar", "ventilador", False
    )


@pytest.mark.parametrize(
    ("id_zona", "nombre", "tipo", "error"),
    [
        ("Z99", "Ventilador", "ventilador", "La zona no existe"),
        ("Z1", " ", "ventilador", "El nombre del actuador es obligatorio"),
        ("Z1", "Ventilador", "motor", "Selecciona un tipo de actuador válido"),
    ],
)
def test_anadir_actuador_rechaza_datos_invalidos_sin_persistir(contexto, id_zona, nombre, tipo, error):
    controlador, repo_zonas, *_ = contexto
    original = repo_zonas.ruta.read_bytes()

    assert controlador.anadir_actuador(id_zona, nombre, tipo) == error
    assert repo_zonas.ruta.read_bytes() == original


def test_eliminar_actuador_persiste_la_baja(contexto):
    controlador, repo_zonas, *_ = contexto

    assert controlador.eliminar_actuador("Z1", "A1") is None
    recargada = RepositorioZonas(repo_zonas.ruta).buscar("Z1")
    assert recargada.actuadores.buscar(lambda elemento: elemento.id == "A1") is None


@pytest.mark.parametrize(
    ("id_zona", "id_actuador", "error"),
    [("Z99", "A1", "La zona no existe"), ("Z1", "A99", "El actuador no existe en esa zona")],
)
def test_eliminar_actuador_inexistente_devuelve_error(contexto, id_zona, id_actuador, error):
    controlador, repo_zonas, *_ = contexto
    original = repo_zonas.ruta.read_bytes()

    assert controlador.eliminar_actuador(id_zona, id_actuador) == error
    assert repo_zonas.ruta.read_bytes() == original


def test_asignar_responsable_guarda_usuario_valido(contexto):
    controlador, repo_zonas, *_ = contexto

    assert controlador.asignar_responsable("Z3", "carpa") is None
    assert RepositorioZonas(repo_zonas.ruta).buscar("Z3").responsable == "carpa"


@pytest.mark.parametrize(
    ("id_zona", "usuario", "error"),
    [
        ("Z99", "carpa", "La zona no existe"),
        ("Z1", "  ", "Indica un usuario responsable"),
        ("Z1", "no_existe", "El usuario responsable no existe"),
        (
            "Z1", "jefe",
            "Solo se puede asignar a responsables de carpa o técnicos de logística",
        ),
    ],
)
def test_asignar_responsable_rechaza_usuario_o_zona_invalidos(contexto, id_zona, usuario, error):
    controlador, repo_zonas, *_ = contexto
    original = repo_zonas.ruta.read_bytes()

    assert controlador.asignar_responsable(id_zona, usuario) == error
    assert repo_zonas.ruta.read_bytes() == original


def test_responsables_disponibles_solo_incluye_roles_asignables(contexto):
    controlador, _, _, *_ = contexto

    disponibles = controlador.responsables_disponibles()

    assert isinstance(disponibles, ListaEnlazada)
    assert {usuario.usuario for usuario in disponibles} == {"carpa", "logistica"}
