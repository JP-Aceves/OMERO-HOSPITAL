import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

import controller.dashboard_controller as dashboard_module
from controller.actuadores_controller import ActuadoresController
from controller.dashboard_controller import DashboardController
from controller.zonas_controller import ZonasController
from main import main
from model.actuador import Actuador
from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorHumoGas, SensorTemperatura
from model.usuario import Administrador, JefeSanidad, ResponsableCarpa, TecnicoLogistica, hashear
from model.zona import Zona
from persistence.repositorio_json import RepositorioJSON
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service.simulador import Simulador
from view.actuadores_view import ActuadoresView


@pytest.fixture
def zonas(tmp_path):
    repo = RepositorioZonas(tmp_path / "data" / "zonas.json")
    carpa = Zona("Z1", "Carpa", "carpa", "carpa")
    carpa.anadir_actuador(Actuador("A1", "Ventilador", "ventilador"))
    carpa.anadir_actuador(Actuador("A2", "Semáforo", "led_semaforo"))
    repo.anadir(carpa)
    for id_zona, id_actuador in (("Z2", "A3"), ("Z3", "A4")):
        tecnica = Zona(id_zona, id_zona, "zona_tecnica", "logistica")
        tecnica.anadir_actuador(Actuador(id_actuador, "LED", "led_evacuacion"))
        tecnica.anadir_sensor(SensorHumoGas(f"H{id_zona}", "MQ-2", 20, 50))
        tecnica.anadir_sensor(SensorTemperatura(f"T{id_zona}", "Temperatura", 28, 32))
        repo.anadir(tecnica)
    return repo


def usuario(rol, nombre):
    return rol(nombre, nombre, "", "")


def estado(zonas, id_zona, id_actuador):
    zona = RepositorioZonas(zonas.ruta).buscar(id_zona)
    return zona.actuadores.buscar(lambda actuador: actuador.id == id_actuador).encendido


def test_carpa_cambia_ventilador_y_todos_los_roles_ven_el_estado(zonas):
    controlador = ActuadoresController(zonas)
    carpa = usuario(ResponsableCarpa, "carpa")
    lectores = (
        carpa, usuario(JefeSanidad, "jefe"), usuario(TecnicoLogistica, "logistica"),
        usuario(Administrador, "admin"),
    )

    assert controlador.cambiar("Z1", "A1", True, carpa) is None
    assert estado(zonas, "Z1", "A1")
    for lector in lectores:
        ventilador = next(fila for fila in controlador.listar(lector) if fila[1].id == "A1")
        assert ventilador[1].encendido
        assert ventilador[2] == (isinstance(lector, (ResponsableCarpa, JefeSanidad)))

    assert controlador.cambiar("Z1", "A1", False, carpa) is None
    assert not estado(zonas, "Z1", "A1")


@pytest.mark.parametrize("rol,nombre,id_zona,id_actuador", [
    (ResponsableCarpa, "otra_cuenta", "Z1", "A1"),
    (ResponsableCarpa, "carpa", "Z1", "A2"),
    (ResponsableCarpa, "carpa", "Z2", "A3"),
    (TecnicoLogistica, "otra_cuenta", "Z2", "A3"),
    (TecnicoLogistica, "logistica", "Z1", "A1"),
    (JefeSanidad, "jefe", "Z1", "A2"),
    (JefeSanidad, "jefe", "Z2", "A3"),
    (Administrador, "admin", "Z2", "A3"),
])
def test_permisos_se_aplican_en_ambos_sentidos(zonas, rol, nombre, id_zona, id_actuador):
    controlador = ActuadoresController(zonas)
    lector = usuario(rol, nombre)
    original = zonas.ruta.read_bytes()
    assert controlador.cambiar(id_zona, id_actuador, True, lector) is not None
    assert controlador.cambiar(id_zona, id_actuador, False, lector) is not None
    assert zonas.ruta.read_bytes() == original


def test_tecnico_controla_led_manualmente_sin_lecturas(zonas):
    controlador = ActuadoresController(zonas)
    tecnico = usuario(TecnicoLogistica, "logistica")
    assert controlador.cambiar("Z2", "A3", True, tecnico) is None
    assert estado(zonas, "Z2", "A3")
    assert controlador.cambiar("Z2", "A3", False, tecnico) is None
    assert not estado(zonas, "Z2", "A3")


def test_jefe_puede_controlar_el_ventilador(zonas):
    controlador = ActuadoresController(zonas)
    jefe = usuario(JefeSanidad, "jefe")
    assert controlador.cambiar("Z1", "A1", True, jefe) is None
    actuador = controlador.de_zona("Z1").buscar(lambda dato: dato.id == "A1")
    assert actuador.encendido
    assert controlador.cambiar("Z1", "A1", False, jefe) is None
    assert not estado(zonas, "Z1", "A1")
    assert isinstance(controlador.de_zona("desconocida"), ListaEnlazada)
    assert not controlador.de_zona("desconocida")


def test_dashboard_aplica_la_salida_del_generador_de_alertas(zonas, tmp_path, monkeypatch):
    lecturas = RepositorioLecturas(tmp_path / "lecturas.json")
    simulador = Simulador(zonas, lecturas)
    monkeypatch.setattr(simulador, "_siguiente_valor", lambda sensor: 60)
    dashboard = DashboardController(zonas, lecturas, simulador)

    def generar_alertas(configuracion, ronda):
        assert configuracion.buscar(lambda zona: zona.id == "Z2") is not None
        assert ronda.buscar(lambda lectura: lectura.sensor == "HZ2").valor == 60
        alertas = ListaEnlazada()
        alertas.insertar(SimpleNamespace(zona="Z2", sensor="HZ2", tipo="humo_gas", nivel="aviso"))
        alertas.insertar(SimpleNamespace(zona="Z3", sensor="HZ3", tipo="humo_gas", nivel="critico"))
        return alertas

    monkeypatch.setattr(dashboard_module, "alertas_de_ronda", generar_alertas)
    dashboard.actualizar()
    assert not estado(zonas, "Z2", "A3")
    assert estado(zonas, "Z3", "A4")


def test_solo_humo_critico_de_la_misma_zona_activa_el_led(zonas, tmp_path, monkeypatch):
    lecturas = RepositorioLecturas(tmp_path / "lecturas.json")
    simulador = Simulador(zonas, lecturas)
    dashboard = DashboardController(zonas, lecturas, simulador)
    valores = {"HZ2": 49, "HZ3": 10, "TZ2": 40, "TZ3": 40}
    monkeypatch.setattr(simulador, "_siguiente_valor", lambda sensor: valores[sensor.id])
    dashboard.actualizar()
    assert not estado(zonas, "Z2", "A3")
    assert not estado(zonas, "Z3", "A4")

    valores["HZ2"] = 50
    dashboard.actualizar()
    assert estado(zonas, "Z2", "A3")
    assert not estado(zonas, "Z3", "A4")
    assert not estado(zonas, "Z1", "A1")

    valores["HZ2"] = 10
    dashboard.actualizar()
    assert estado(zonas, "Z2", "A3")


def test_cambios_en_instancias_distintas_no_se_pisan(zonas):
    carpa = ActuadoresController(RepositorioZonas(zonas.ruta))
    tecnico = ActuadoresController(RepositorioZonas(zonas.ruta))
    with ThreadPoolExecutor(max_workers=2) as tareas:
        ventilador = tareas.submit(carpa.cambiar, "Z1", "A1", True, usuario(ResponsableCarpa, "carpa"))
        led = tareas.submit(tecnico.cambiar, "Z2", "A3", True, usuario(TecnicoLogistica, "logistica"))
        assert ventilador.result() is None
        assert led.result() is None
    assert estado(zonas, "Z1", "A1")
    assert estado(zonas, "Z2", "A3")


def test_fallo_de_escritura_conserva_el_estado_anterior(zonas, monkeypatch):
    def fallar(*_args):
        raise OSError("Archivo ocupado")

    monkeypatch.setattr(Path, "replace", fallar)
    controlador = ActuadoresController(zonas)
    assert controlador.cambiar("Z1", "A1", True, usuario(ResponsableCarpa, "carpa"))
    assert not estado(zonas, "Z1", "A1")
    assert not tuple(zonas.ruta.parent.glob("*.tmp"))


def test_editar_zona_con_copia_anterior_conserva_estado_del_ventilador(zonas, tmp_path):
    editor = ZonasController(RepositorioZonas(zonas.ruta), RepositorioJSON(tmp_path / "usuarios.json"))
    controlador = ActuadoresController(zonas)
    assert controlador.cambiar("Z1", "A1", True, usuario(ResponsableCarpa, "carpa")) is None
    assert editor.editar_zona("Z1", "Carpa renombrada", "carpa", None) is None
    assert RepositorioZonas(zonas.ruta).buscar("Z1").nombre == "Carpa renombrada"
    assert estado(zonas, "Z1", "A1")


class _PaginaDePrueba:
    """Ejecuta los callbacks del router sin montar un cliente Flet."""

    def __init__(self):
        self.window = SimpleNamespace()
        self.fonts = {}
        self.views = []

    def go(self, ruta):
        self.route = ruta
        self.on_route_change()

    def update(self):
        pass


def _recorrer(control):
    yield control
    for hijo in getattr(control, "controls", None) or ():
        yield from _recorrer(hijo)
    contenido = getattr(control, "content", None)
    if contenido is not None:
        yield from _recorrer(contenido)


def _entrar(nombre, contrasena):
    pagina = _PaginaDePrueba()
    main(pagina)
    campos = {
        control.key: control for control in _recorrer(pagina.views[0])
        if getattr(control, "key", None)
    }
    campos["test:login_usuario"].value = nombre
    campos["test:login_contrasena"].value = contrasena
    campos["test:login_enviar"].on_click(None)
    return pagina.views[0]


def _fila(vista, nombre):
    panel = next(control for control in _recorrer(vista) if isinstance(control, ActuadoresView))
    return next(fila for fila in panel.controls[1].controls if fila.controls[0].value.startswith(nombre))


def test_desde_los_dashboards_ventilador_y_evacuacion(zonas, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    zona_carpa = zonas.buscar("Z1")
    zona_carpa.anadir_sensor(SensorTemperatura("S1", "Temperatura de la carpa", 28, 32))
    zonas.actualizar(zona_carpa)
    cuentas = RepositorioJSON()
    clave = "prueba-ome-66"
    for rol, nombre in (
        (ResponsableCarpa, "carpa"), (JefeSanidad, "jefe"),
        (TecnicoLogistica, "logistica"), (Administrador, "admin"),
    ):
        sal, codigo = hashear(clave)
        cuentas.anadir(rol(nombre, nombre, codigo, sal))

    critico = False
    temperatura = 33

    def valor(_simulador, sensor):
        if sensor.id == "S1":
            return temperatura
        return 50 if critico and sensor.id == "HZ2" else 10

    monkeypatch.setattr(Simulador, "_siguiente_valor", valor)
    carpa = _entrar("carpa", clave)
    textos = {c.value for c in _recorrer(carpa) if isinstance(getattr(c, "value", None), str)}
    assert {"Mi carpa", "33 °C", "1 activa", "Ventilador · Apagado"} <= textos
    assert "Z2" not in textos

    temperatura = 25
    actualizar_carpa = next(c for c in _recorrer(carpa) if getattr(c, "text", None) == "Actualizar")
    asyncio.run(actualizar_carpa.on_click(None))
    textos = {c.value for c in _recorrer(carpa) if isinstance(getattr(c, "value", None), str)}
    assert {"25 °C", "0 activas"} <= textos
    assert "33 °C" not in textos

    encender = next(
        c for c in _recorrer(carpa) if getattr(c, "text", None) == "Encender ventilador"
    )
    asyncio.run(encender.on_click(None))
    assert any(
        getattr(c, "text", None) == "Apagar ventilador" for c in _recorrer(carpa)
    )

    jefe = _entrar("jefe", clave)
    ventilador = _fila(jefe, "Carpa · Ventilador")
    assert ventilador.controls[0].value.endswith("Encendido")
    assert ventilador.controls[1].text == "Apagar"
    assert _fila(jefe, "Z2 · LED").controls[0].value.endswith("Apagado")

    critico = True
    actualizar = next(c for c in _recorrer(jefe) if getattr(c, "text", None) == "Actualizar")
    asyncio.run(actualizar.on_click(None))
    assert _fila(jefe, "Z2 · LED").controls[0].value.endswith("Encendido")
    assert len(_fila(jefe, "Z2 · LED").controls) == 1
    assert _fila(jefe, "Z3 · LED").controls[0].value.endswith("Apagado")

    tecnico = _entrar("logistica", clave)
    asyncio.run(_fila(tecnico, "Z2 · LED").controls[1].on_click(None))
    assert _fila(tecnico, "Z2 · LED").controls[0].value.endswith("Apagado")
    actualizar = next(
        c for c in _recorrer(tecnico) if getattr(c, "text", None) == "Actualizar alertas"
    )
    asyncio.run(actualizar.on_click(None))
    assert _fila(tecnico, "Z2 · LED").controls[0].value.endswith("Encendido")
    admin = _entrar("admin", clave)
    assert _fila(admin, "Carpa · Ventilador").controls[0].value.endswith("Encendido")
