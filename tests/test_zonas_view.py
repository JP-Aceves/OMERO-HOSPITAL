"""Pruebas de la pantalla "Zonas y sensores". Responsable: JP (OME-35).

Usan un controlador falso que apunta las llamadas: así se prueba la vista sin
depender del ZonasController de Rodas ni de ficheros.
"""
from model.lista_enlazada import ListaEnlazada
from model.usuario import JefeSanidad, ResponsableCarpa, TecnicoLogistica
from model.zona import crear_zona
from view.zonas_view import SIN_RESPONSABLE, ZonasView, cantidad, resumen_zona


class ControladorFalso:
    """Imita al ZonasController: guarda las llamadas y devuelve None (todo bien)."""

    def __init__(self, error=None):
        self.error = error
        self.llamadas = []
        self.zonas = ListaEnlazada()
        self.zonas.insertar(crear_zona({
            "id": "Z1", "nombre": "Carpa de hospitalización", "tipo": "carpa", "responsable": "carpa",
            "sensores": [
                {"id": "S1", "nombre": "DHT22 temperatura", "tipo": "temperatura", "umbral_aviso": 28, "umbral_critico": 32},
                {"id": "S4", "nombre": "LDR luz", "tipo": "luz", "umbral_aviso": 40, "umbral_critico": 20},
            ],
            "actuadores": [{"id": "A1", "nombre": "Ventilador", "tipo": "ventilador", "encendido": False}],
        }))
        self.zonas.insertar(crear_zona({"id": "Z3", "nombre": "Exterior", "tipo": "exterior", "responsable": "logistica"}))

    def listar(self, usuario):
        return self.zonas

    def responsables_disponibles(self):
        lista = ListaEnlazada()
        lista.insertar(ResponsableCarpa("Responsable de prueba", "carpa", "h", "s"))
        lista.insertar(TecnicoLogistica("Técnico de prueba", "logistica", "h", "s"))
        return lista

    def _apunta(self, *llamada):
        self.llamadas.append(llamada)
        return self.error

    def editar_zona(self, *a): return self._apunta("editar_zona", *a)
    def asignar_responsable(self, *a): return self._apunta("asignar_responsable", *a)
    def eliminar_zona(self, *a): return self._apunta("eliminar_zona", *a)
    def anadir_sensor(self, *a): return self._apunta("anadir_sensor", *a)
    def editar_sensor(self, *a): return self._apunta("editar_sensor", *a)
    def eliminar_sensor(self, *a): return self._apunta("eliminar_sensor", *a)
    def anadir_actuador(self, *a): return self._apunta("anadir_actuador", *a)
    def eliminar_actuador(self, *a): return self._apunta("eliminar_actuador", *a)

    def crear_zona(self, nombre, tipo, responsable):
        self.llamadas.append(("crear_zona", nombre, tipo, responsable))
        if self.error is None:
            self.zonas.insertar(crear_zona({"id": "Z9", "nombre": nombre, "tipo": tipo, "responsable": responsable}))
        return self.error


def vista(error=None):
    controlador = ControladorFalso(error)
    pantalla = ZonasView(JefeSanidad("Jefe", "jefe", "h", "s"), controlador)
    pantalla.construir()
    return pantalla, controlador


def campo(dialogo, clave):
    for control in dialogo.content.controls:
        if getattr(control, "key", None) == clave:
            return control
    raise KeyError(clave)


def test_resumen_de_una_zona():
    controlador = ControladorFalso()
    assert resumen_zona(next(iter(controlador.zonas))) == "2 sensores · 1 actuador"


def test_cantidad_usa_singular_solo_con_uno():
    assert cantidad(1, "sensor", "sensores") == "1 sensor"
    assert cantidad(0, "sensor", "sensores") == "0 sensores"
    assert cantidad(3, "sensor", "sensores") == "3 sensores"


def test_hay_una_tarjeta_por_zona_y_se_elige_la_primera():
    pantalla, _ = vista()
    assert [t.key for t in pantalla.lista_zonas.controls] == ["zona_Z1", "zona_Z3"]
    assert pantalla.id_seleccionada == "Z1"
    assert pantalla.campo_nombre.value == "Carpa de hospitalización"


def test_al_pulsar_una_tarjeta_cambia_el_detalle():
    pantalla, _ = vista()
    pantalla.lista_zonas.controls[1].on_click(None)
    assert pantalla.id_seleccionada == "Z3"
    assert pantalla.campo_nombre.value == "Exterior"


def test_guardar_cambia_nombre_y_asigna_responsable():
    pantalla, controlador = vista()
    pantalla.campo_nombre.value = "Carpa 1"
    pantalla.campo_responsable.value = "logistica"
    pantalla._guardar_zona()
    assert controlador.llamadas == [
        ("editar_zona", "Z1", "Carpa 1", "carpa", "carpa"),
        ("asignar_responsable", "Z1", "logistica"),
    ]
    assert pantalla.mensaje.value == "Cambios guardados."


def test_quitar_el_responsable_guarda_none():
    pantalla, controlador = vista()
    pantalla.campo_responsable.value = SIN_RESPONSABLE
    pantalla._guardar_zona()
    assert controlador.llamadas[-1] == ("editar_zona", "Z1", "Carpa de hospitalización", "carpa", None)


def test_el_error_del_controlador_se_ve_en_pantalla():
    pantalla, _ = vista(error="Rellena todos los campos")
    pantalla._guardar_zona()
    assert pantalla.mensaje.visible
    assert pantalla.mensaje.value == "Rellena todos los campos"


def test_eliminar_sensor_llama_al_controlador():
    pantalla, controlador = vista()
    pantalla._eliminar_sensor("S4")
    assert controlador.llamadas == [("eliminar_sensor", "Z1", "S4")]


def test_nueva_zona_desde_el_formulario_y_queda_seleccionada():
    pantalla, controlador = vista()
    pantalla._formulario_zona_nueva()
    campo(pantalla.dialogo, "test:nueva_zona_nombre").value = "Carpa 2"
    pantalla.dialogo.actions[1].on_click(None)   # botón Crear
    assert controlador.llamadas == [("crear_zona", "Carpa 2", "carpa", None)]
    assert pantalla.dialogo is None
    assert pantalla.id_seleccionada == "Z9"


def test_si_el_formulario_falla_se_queda_abierto_con_el_error():
    pantalla, _ = vista(error="El umbral debe ser un número")
    pantalla._formulario_sensor()
    campo(pantalla.dialogo, "test:sensor_aviso").value = "abc"
    pantalla.dialogo.actions[1].on_click(None)
    assert pantalla.dialogo is not None
    assert campo(pantalla.dialogo, "dialogo_error").value == "El umbral debe ser un número"


def test_editar_sensor_manda_los_umbrales_como_texto():
    pantalla, controlador = vista()
    sensor = next(iter(next(iter(controlador.zonas)).sensores))
    pantalla._formulario_sensor(sensor=sensor)
    campo(pantalla.dialogo, "test:sensor_critico").value = "33"
    pantalla.dialogo.actions[1].on_click(None)
    assert controlador.llamadas == [("editar_sensor", "Z1", "S1", "DHT22 temperatura", "28", "33")]


def test_eliminar_zona_pide_confirmacion():
    pantalla, controlador = vista()
    pantalla._confirmar_eliminar_zona()
    assert controlador.llamadas == []          # todavía no ha borrado nada
    pantalla.dialogo.actions[1].on_click(None)  # confirma
    assert controlador.llamadas == [("eliminar_zona", "Z1")]
