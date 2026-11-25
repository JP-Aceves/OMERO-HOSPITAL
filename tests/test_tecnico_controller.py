"""Pruebas del controlador del dashboard "Recursos" del técnico de logística (OME-63)."""
from datetime import datetime, timedelta
from pathlib import Path
from shutil import copyfile

import pytest

from controller.actuadores_controller import ActuadoresController
from controller.dashboard_controller import DashboardController
from controller.tecnico_controller import TecnicoController
from model.actuador import Actuador
from model.usuario import JefeSanidad, TecnicoLogistica
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service.simulador import Simulador

# Valores normales de todos los sensores; cada prueba cambia los que necesita.
NORMALES = {
    "temperatura": 25, "humedad": 50, "calidad_aire": 10, "luz": 60,
    "humo_gas": 5, "nivel_deposito": 80, "viento": 10,
}


@pytest.fixture
def contexto(tmp_path, monkeypatch):
    origen = Path(__file__).resolve().parents[1] / "data" / "zonas.json"
    ruta_zonas = tmp_path / "zonas.json"
    copyfile(origen, ruta_zonas)
    ruta_lecturas = tmp_path / "lecturas.json"
    zonas = RepositorioZonas(ruta_zonas)
    simulador = Simulador(zonas, RepositorioLecturas(ruta_lecturas), semilla=7)
    valores = dict(NORMALES)
    niveles = []  # si tiene valores, el depósito los va dando en orden

    def siguiente_valor(sensor):
        if sensor.TIPO == "nivel_deposito" and niveles:
            return niveles.pop(0)
        return valores[sensor.TIPO]

    monkeypatch.setattr(simulador, "_siguiente_valor", siguiente_valor)
    controlador = TecnicoController(
        DashboardController(zonas, RepositorioLecturas(ruta_lecturas), simulador),
        ActuadoresController(RepositorioZonas(ruta_zonas)),
        RepositorioLecturas(ruta_lecturas),
    )
    usuario = TecnicoLogistica("Técnico", "logistica", "", "")
    return controlador, usuario, simulador, valores, niveles, ruta_zonas


def test_ve_la_zona_tecnica_y_el_exterior_con_unidad_y_estado(contexto):
    controlador, usuario, _, valores, _, _ = contexto
    valores.update(humo_gas=60, nivel_deposito=40, viento=10)
    controlador.inicializar(usuario)

    tecnica, exterior = controlador.resumen(usuario)
    assert (tecnica["id"], exterior["id"]) == ("Z2", "Z3")
    assert [(s["tipo"], s["valor"], s["unidad"], s["estado"]) for s in tecnica["sensores"]] == [
        ("humo_gas", 60, "%", "critico"), ("nivel_deposito", 40, "%", "aviso"),
    ]
    assert [(s["tipo"], s["valor"], s["unidad"], s["estado"]) for s in exterior["sensores"]] == [
        ("viento", 10, "km/h", "normal"),
    ]
    assert (tecnica["estado"], exterior["estado"]) == ("critico", "normal")
    viento = exterior["sensores"][0]
    assert (viento["umbral_aviso"], viento["umbral_critico"]) == (30, 50)


@pytest.mark.parametrize(("nivel", "estado"), [(80, "normal"), (45, "aviso"), (18, "critico")])
def test_el_deposito_pasa_a_critico_por_debajo_del_20(contexto, nivel, estado):
    controlador, usuario, _, valores, _, _ = contexto
    valores["nivel_deposito"] = nivel
    controlador.inicializar(usuario)

    deposito = controlador.deposito(usuario)
    assert (deposito["zona"], deposito["nivel"], deposito["estado"]) == ("Z2", nivel, estado)


def test_el_deposito_predice_el_vaciado_y_da_su_historico(contexto):
    controlador, usuario, simulador, _, niveles, _ = contexto
    niveles.extend([90, 88, 86, 84, 82, 80])
    simulador.generar(6, 10)  # 6 rondas separadas 10 minutos

    deposito = controlador.deposito(usuario)
    primera = datetime.fromisoformat(deposito["historico"][0][0])
    assert [nivel for _, nivel in deposito["historico"]] == [90, 88, 86, 84, 82, 80]
    assert deposito["nivel"] == 80
    # Baja 0,2 % por minuto (12 % por hora) desde el 90 %: llega a 0 a los 450 minutos.
    assert deposito["pendiente"] == pytest.approx(-12)
    assert datetime.fromisoformat(deposito["vaciado"]) == primera + timedelta(minutes=450)
    assert (deposito["umbral_aviso"], deposito["umbral_critico"]) == (50, 20)


def test_el_historico_empieza_en_el_ultimo_rellenado(contexto):
    controlador, usuario, simulador, _, niveles, _ = contexto
    niveles.extend([30, 20, 12, 95, 93, 91, 89, 87])
    simulador.generar(8, 10)

    deposito = controlador.deposito(usuario)
    assert [nivel for _, nivel in deposito["historico"]] == [95, 93, 91, 89, 87]
    assert deposito["vaciado"] is not None


def test_sin_suficientes_lecturas_no_hay_prediccion(contexto):
    controlador, usuario, _, _, _, _ = contexto

    deposito = controlador.deposito(usuario)
    assert deposito["nivel"] is None and deposito["estado"] == "normal"
    assert deposito["vaciado"] is None and deposito["pendiente"] is None
    assert deposito["historico"] == []

    controlador.inicializar(usuario)
    controlador.actualizar()
    assert len(controlador.deposito(usuario)["historico"]) == 2
    assert controlador.deposito(usuario)["vaciado"] is None


def test_solo_ve_las_alertas_de_sus_zonas(contexto):
    controlador, usuario, _, valores, _, _ = contexto
    valores.update(temperatura=35, humo_gas=60, viento=40)
    controlador.inicializar(usuario)

    alertas = controlador.alertas(usuario)
    assert {(a["zona"], a["tipo"], a["nivel"]) for a in alertas} == {
        ("Z2", "humo_gas", "critico"), ("Z3", "viento", "aviso"),
    }


def test_al_actualizar_cambian_los_valores_y_se_retiran_las_alertas(contexto):
    controlador, usuario, _, valores, _, _ = contexto
    valores.update(humo_gas=60)
    controlador.inicializar(usuario)
    assert controlador.alertas(usuario)

    valores.update(humo_gas=5, viento=20)
    controlador.actualizar()

    tecnica, exterior = controlador.resumen(usuario)
    assert tecnica["sensores"][0]["valor"] == 5
    assert exterior["sensores"][0]["valor"] == 20
    assert controlador.alertas(usuario) == []


def test_el_led_de_evacuacion_se_cambia_y_se_guarda(contexto):
    controlador, usuario, _, _, _, ruta_zonas = contexto
    assert controlador.led_evacuacion(usuario) == {
        "zona": "Z2", "id": "A3", "nombre": "LEDs de evacuación", "encendido": False,
    }

    assert controlador.cambiar_led(usuario, True) is None
    assert controlador.led_evacuacion(usuario)["encendido"] is True
    led = RepositorioZonas(ruta_zonas).buscar("Z2").actuadores.buscar(lambda a: a.id == "A3")
    assert led.encendido is True

    assert controlador.cambiar_led(usuario, False) is None
    assert controlador.led_evacuacion(usuario)["encendido"] is False


def test_con_dos_zonas_con_led_cada_una_controla_el_suyo(contexto):
    controlador, usuario, _, _, _, ruta_zonas = contexto
    zonas = RepositorioZonas(ruta_zonas)
    exterior = zonas.buscar("Z3")
    exterior.anadir_actuador(Actuador("A4", "LED del exterior", "led_evacuacion"))
    zonas.actualizar(exterior)

    assert controlador.led_evacuacion(usuario)["id"] == "A3"
    assert controlador.led_evacuacion(usuario, "Z3")["id"] == "A4"

    assert controlador.cambiar_led(usuario, True, "Z3") is None
    assert controlador.led_evacuacion(usuario, "Z3")["encendido"] is True
    assert controlador.led_evacuacion(usuario, "Z2")["encendido"] is False


def test_humo_critico_enciende_el_led_al_actualizar(contexto):
    controlador, usuario, _, valores, _, _ = contexto
    controlador.inicializar(usuario)
    assert controlador.led_evacuacion(usuario)["encendido"] is False

    valores["humo_gas"] = 60
    controlador.actualizar()

    assert controlador.led_evacuacion(usuario)["encendido"] is True


@pytest.mark.parametrize(("clase", "nombre"), [
    (TecnicoLogistica, "sin_asignar"),
    (JefeSanidad, "logistica"),
])
def test_sin_zonas_o_sin_rol_no_hay_acceso(contexto, clase, nombre):
    controlador, _, simulador, _, _, _ = contexto
    usuario = clase("Otra persona", nombre, "", "")

    controlador.inicializar(usuario)
    assert not simulador.repo_lecturas.ruta.exists()
    assert controlador.resumen(usuario) == []
    assert controlador.deposito(usuario) is None
    assert controlador.alertas(usuario) == []
    assert controlador.led_evacuacion(usuario) is None
    assert controlador.cambiar_led(usuario, True) == "No tienes un LED de evacuación asignado"