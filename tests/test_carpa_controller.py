from pathlib import Path
from shutil import copyfile

import pytest

from controller.actuadores_controller import ActuadoresController
from controller.carpa_controller import CarpaController
from controller.dashboard_controller import DashboardController
from model.usuario import JefeSanidad, ResponsableCarpa
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service.simulador import Simulador


@pytest.fixture
def contexto(tmp_path):
    origen = Path(__file__).resolve().parents[1] / "data" / "zonas.json"
    ruta_zonas = tmp_path / "zonas.json"
    copyfile(origen, ruta_zonas)
    zonas = RepositorioZonas(ruta_zonas)
    tecnica = zonas.buscar("Z2")
    tecnica.responsable = "carpa"
    zonas.actualizar(tecnica)
    lecturas = RepositorioLecturas(tmp_path / "lecturas.json")
    simulador = Simulador(zonas, lecturas, semilla=7)
    actuadores = ActuadoresController(RepositorioZonas(ruta_zonas))
    controlador = CarpaController(DashboardController(zonas, lecturas, simulador), actuadores)
    return controlador, ResponsableCarpa("Responsable", "carpa", "", ""), simulador


def test_muestra_cuatro_sensores_con_unidad_estado_y_alertas_de_su_carpa(contexto, monkeypatch):
    controlador, usuario, simulador = contexto
    valores = {
        "temperatura": 33, "humedad": 65, "calidad_aire": 10, "luz": 18,
        "humo_gas": 90, "nivel_deposito": 70, "viento": 70,
    }
    monkeypatch.setattr(simulador, "_siguiente_valor", lambda sensor: valores[sensor.TIPO])
    controlador.inicializar(usuario)

    zona, = controlador.resumen(usuario)
    assert zona["id"] == "Z1"
    assert [(s["valor"], s["unidad"], s["estado"]) for s in zona["sensores"]] == [
        (33, "°C", "critico"), (65, "%", "aviso"), (10, "%", "normal"), (18, "%", "critico"),
    ]
    assert {a["zona"] for a in controlador.alertas(usuario)} == {"Z1"}
    assert {a["tipo"] for a in controlador.alertas(usuario)} == {"temperatura", "humedad", "luz"}

    valores.update(temperatura=25, humedad=55, luz=60)
    controlador.actualizar()

    zona, = controlador.resumen(usuario)
    assert [s["valor"] for s in zona["sensores"]] == [25, 55, 10, 60]
    assert controlador.alertas(usuario) == []


def test_ventilador_se_guarda_y_conserva_su_estado_al_actualizar(contexto):
    controlador, usuario, _ = contexto
    assert controlador.ventilador(usuario) == {
        "zona": "Z1", "id": "A1", "nombre": "Ventilador", "encendido": False,
    }

    assert controlador.cambiar_ventilador(usuario, True, "Z1") is None
    controlador.actualizar()
    assert controlador.ventilador(usuario)["encendido"] is True
    assert controlador.cambiar_ventilador(usuario, False) is None
    assert controlador.ventilador(usuario)["encendido"] is False


@pytest.mark.parametrize(("clase", "nombre"), [
    (ResponsableCarpa, "sin_asignar"),
    (JefeSanidad, "carpa"),
])
def test_sin_carpa_o_sin_rol_no_hay_acceso(contexto, clase, nombre):
    controlador, titular, simulador = contexto
    usuario = clase("Otra persona", nombre, "", "")

    controlador.inicializar(usuario)
    assert not simulador.repo_lecturas.ruta.exists()
    assert controlador.resumen(usuario) == []
    assert controlador.alertas(usuario) == []
    assert controlador.ventilador(usuario) is None
    assert controlador.cambiar_ventilador(usuario, True)
    assert controlador.cambiar_ventilador(titular, True, "Z2")
    assert controlador.ventilador(titular)["encendido"] is False


def test_reasignacion_revoca_acceso_en_la_sesion_abierta(contexto):
    controlador, usuario, simulador = contexto
    assert controlador.ventilador(usuario) is not None
    zonas = RepositorioZonas(simulador.repo_zonas.ruta)
    carpa = zonas.buscar("Z1")
    carpa.responsable = "otro_responsable"
    zonas.actualizar(carpa)

    assert controlador.resumen(usuario) == []
    assert controlador.ventilador(usuario) is None
    assert controlador.cambiar_ventilador(usuario, True, "Z1")
