import pytest

from controller.dashboard_controller import DashboardController
from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorHumoGas, SensorLuz, SensorTemperatura, SensorViento
from model.usuario import (
    Administrador,
    JefeSanidad,
    Pendiente,
    ResponsableCarpa,
    TecnicoLogistica,
)
from model.zona import Zona
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas


def guardar_lecturas(repositorio, *lecturas):
    lote = ListaEnlazada()
    for lectura in lecturas:
        lote.insertar(lectura)
    repositorio.anadir(lote)
    return lote


class SimuladorDePrueba:
    def __init__(self, repo_zonas, repositorio, rondas=()):
        self.repo_zonas = repo_zonas
        self.repositorio = repositorio
        self.rondas = iter(rondas)
        self.llamadas = 0

    def generar_ronda(self):
        self.llamadas += 1
        return guardar_lecturas(self.repositorio, *next(self.rondas))


@pytest.fixture
def contexto(tmp_path):
    zonas = RepositorioZonas(tmp_path / "zonas.json")
    carpa = Zona("Z1", "Carpa de hospitalización", "carpa", "carpa")
    carpa.anadir_sensor(SensorTemperatura("S1", "Temperatura de la carpa", 28, 32))
    carpa.anadir_sensor(SensorLuz("S2", "Luz de la carpa", 40, 20))
    tecnica = Zona("Z2", "Zona técnica", "zona_tecnica", "logistica")
    tecnica.anadir_sensor(SensorHumoGas("S3", "Humo junto al generador", 20, 50))
    exterior = Zona("Z3", "Exterior", "exterior")
    exterior.anadir_sensor(SensorViento("S4", "Viento exterior", 30, 50))
    for zona in (carpa, tecnica, exterior):
        zonas.anadir(zona)
    lecturas = RepositorioLecturas(tmp_path / "lecturas.json")
    simulador = SimuladorDePrueba(zonas, RepositorioLecturas(lecturas.ruta))
    return zonas, lecturas, DashboardController(zonas, lecturas, simulador), simulador


def sembrar_alertas(lecturas):
    guardar_lecturas(
        lecturas,
        Lectura("Z1", "S1", "temperatura", 33, "°C", "2026-11-20T18:00:00"),
        Lectura("Z1", "S2", "luz", 39, "%", "2026-11-20T18:01:00"),
        Lectura("Z2", "S3", "humo_gas", 55, "%", "2026-11-20T18:02:00"),
        Lectura("Z3", "S4", "viento", 35, "km/h", "2026-11-20T18:03:00"),
    )


def test_alertas_enriquecidas_con_nombres_sin_generar_ni_escribir(contexto):
    zonas, lecturas, dashboard, simulador = contexto
    sembrar_alertas(lecturas)
    json_zonas = zonas.ruta.read_bytes()
    json_lecturas = lecturas.ruta.read_bytes()

    alertas = dashboard.alertas()

    assert isinstance(alertas, list)
    assert len(alertas) == 4
    por_sensor = {alerta["sensor"]: alerta for alerta in alertas}
    for clave, valor in {
        "zona": "Z1", "zona_nombre": "Carpa de hospitalización", "sensor": "S1",
        "sensor_nombre": "Temperatura de la carpa", "valor": 33, "unidad": "°C",
        "nivel": "critico", "fecha_hora": "2026-11-20T18:00:00",
    }.items():
        assert por_sensor["S1"][clave] == valor
    assert por_sensor["S2"]["nivel"] == "aviso"
    assert simulador.llamadas == 0
    assert zonas.ruta.read_bytes() == json_zonas
    assert lecturas.ruta.read_bytes() == json_lecturas


@pytest.mark.parametrize(
    ("clase", "usuario", "esperados"),
    [
        (JefeSanidad, "jefe", {"S1", "S2", "S3", "S4"}),
        (ResponsableCarpa, "carpa", {"S1", "S2"}),
        (TecnicoLogistica, "logistica", {"S3"}),
        (ResponsableCarpa, "sin_asignar", set()),
        (Administrador, "admin", set()),
        (Pendiente, "nueva_cuenta", set()),
    ],
    ids=("jefe", "carpa", "logistica", "sin-asignacion", "administrador", "pendiente"),
)
def test_cada_rol_solo_ve_las_alertas_que_le_corresponden(
    contexto, clase, usuario, esperados
):
    _, lecturas, dashboard, _ = contexto
    sembrar_alertas(lecturas)
    cuenta = clase("Persona de prueba", usuario, "hash-no-usado", "sal-no-usada")

    assert {alerta["sensor"] for alerta in dashboard.alertas(cuenta)} == esperados


def test_una_lectura_normal_posterior_resuelve_la_alerta_historica(contexto):
    _, lecturas, dashboard, _ = contexto
    sembrar_alertas(lecturas)
    assert "S1" in {alerta["sensor"] for alerta in dashboard.alertas()}
    guardar_lecturas(
        RepositorioLecturas(lecturas.ruta),
        Lectura("Z1", "S1", "temperatura", 25, "°C", "2026-11-20T18:05:00"),
    )

    assert {alerta["sensor"] for alerta in dashboard.alertas()} == {"S2", "S3", "S4"}


def test_no_resucita_una_ronda_en_memoria_mas_antigua_que_el_json(contexto):
    zonas, lecturas, _, _ = contexto
    simulador = SimuladorDePrueba(
        zonas, RepositorioLecturas(lecturas.ruta),
        [(Lectura("Z1", "S1", "temperatura", 33, "°C", "2026-11-20T18:00:00"),)],
    )
    dashboard = DashboardController(zonas, lecturas, simulador)
    dashboard.actualizar()
    assert len(dashboard.alertas()) == 1
    guardar_lecturas(
        RepositorioLecturas(lecturas.ruta),
        Lectura("Z1", "S1", "temperatura", 25, "°C", "2026-11-20T18:05:00"),
    )

    assert dashboard.alertas() == []


def test_al_reabrir_la_sesion_se_conservan_las_alertas_activas(contexto):
    zonas, lecturas, dashboard, _ = contexto
    sembrar_alertas(lecturas)
    primero = {alerta["sensor"]: alerta for alerta in dashboard.alertas()}
    reabierto = DashboardController(
        RepositorioZonas(zonas.ruta), RepositorioLecturas(lecturas.ruta),
        SimuladorDePrueba(RepositorioZonas(zonas.ruta), RepositorioLecturas(lecturas.ruta)),
    )

    assert {alerta["sensor"]: alerta for alerta in reabierto.alertas()} == primero


def test_reasignar_zona_retira_las_alertas_al_anterior_responsable(contexto):
    zonas, lecturas, dashboard, _ = contexto
    sembrar_alertas(lecturas)
    cuenta = ResponsableCarpa("Responsable", "carpa", "hash-no-usado", "sal-no-usada")
    assert len(dashboard.alertas(cuenta)) == 2
    otro_repositorio = RepositorioZonas(zonas.ruta)
    editada = otro_repositorio.buscar("Z1")
    editada.responsable = "otra_carpa"
    otro_repositorio.actualizar(editada)

    assert dashboard.alertas(cuenta) == []


def test_los_umbrales_actuales_se_aplican_a_la_ultima_lectura(contexto):
    zonas, lecturas, dashboard, _ = contexto
    sembrar_alertas(lecturas)
    otro_repositorio = RepositorioZonas(zonas.ruta)
    editada = otro_repositorio.buscar("Z1")
    editada.buscar_sensor("S1").umbral_aviso = 34
    editada.buscar_sensor("S1").umbral_critico = 38
    otro_repositorio.actualizar(editada)

    assert {alerta["sensor"] for alerta in dashboard.alertas()} == {"S2", "S3", "S4"}


def test_un_sensor_eliminado_no_deja_una_alerta_huerfana(contexto):
    zonas, lecturas, dashboard, _ = contexto
    sembrar_alertas(lecturas)
    otro_repositorio = RepositorioZonas(zonas.ruta)
    editada = otro_repositorio.buscar("Z1")
    editada.eliminar_sensor("S1")
    otro_repositorio.actualizar(editada)

    assert {alerta["sensor"] for alerta in dashboard.alertas()} == {"S2", "S3", "S4"}


def test_sin_lecturas_no_hay_alertas_y_no_se_crea_un_fichero(contexto):
    _, lecturas, dashboard, simulador = contexto

    assert dashboard.alertas() == []
    assert not lecturas.ruta.exists()
    assert simulador.llamadas == 0
