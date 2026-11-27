"""Datos del dashboard "Recursos" del técnico de logística. Responsable: Ivan (OME-63).

Se apoya en DashboardController (lecturas, estado y alertas), en
service/prediccion.py (vaciado del depósito) y en ActuadoresController (LED).
La vista no toca el modelo: todo lo que pinta sale de aquí.
"""
from controller.actuadores_controller import ActuadoresController
from controller.dashboard_controller import DashboardController
from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorNivelDeposito
from model.usuario import TecnicoLogistica, Usuario
from persistence.repositorio_lecturas import RepositorioLecturas
from service.estado import NORMAL, estado_sensor
from service.prediccion import predecir_vaciado, recta, ultimo_tramo


class TecnicoController:

    def __init__(self, dashboard: DashboardController, actuadores: ActuadoresController,
                 repo_lecturas: RepositorioLecturas) -> None:
        self.dashboard = dashboard
        self.actuadores = actuadores
        self.repo_lecturas = repo_lecturas

    def _zonas(self, usuario: Usuario) -> ListaEnlazada:
        """Zonas asignadas al técnico, releídas por si otra pantalla las cambió."""
        if usuario.ROL != TecnicoLogistica.ROL:
            return ListaEnlazada()
        repositorio = self.dashboard.repo_zonas
        repositorio.recargar()
        return repositorio.zonas_de(usuario.usuario)

    def inicializar(self, usuario: Usuario) -> None:
        """Prepara las lecturas al entrar si el técnico tiene zonas asignadas."""
        if self._zonas(usuario):
            self.dashboard.inicializar()

    def resumen(self, usuario: Usuario) -> list[dict]:
        """Las zonas del usuario con el mismo formato que DashboardController.resumen().

        Sensores: depósito, humo/gas y viento. Cada sensor lleva además "id", "tipo",
        "umbral_aviso" y "umbral_critico", para que la vista sepa qué tarjeta pintar.
        """
        zonas_modelo = self._zonas(usuario)
        zonas = self.dashboard._resumen_zonas(zonas_modelo)
        # _resumen_zonas respeta el orden de zonas y sensores, así que van emparejados.
        for zona, datos_zona in zip(zonas_modelo, zonas):
            for sensor, datos_sensor in zip(zona.sensores, datos_zona["sensores"]):
                datos_sensor.update(
                    id=sensor.id, tipo=sensor.TIPO,
                    umbral_aviso=sensor.umbral_aviso, umbral_critico=sensor.umbral_critico,
                )
        return zonas

    def deposito(self, usuario: Usuario) -> dict | None:
        """{"zona": "Z2", "nivel": 43.0, "estado": "aviso", "vaciado": "2026-11-27T10:00:00" | None,
        "historico": [(fecha_hora, nivel), ...]} o None si no tiene depósito.

        Además lleva "nombre", "umbral_aviso", "umbral_critico" y "pendiente" (% por hora,
        solo si hay predicción). El histórico son las lecturas que usa la predicción:
        las del último rellenado (service/prediccion.py).
        """
        for zona in self._zonas(usuario):
            sensor = zona.sensores.buscar(lambda dato: dato.TIPO == SensorNivelDeposito.TIPO)
            if sensor is None:
                continue
            # Se relee el fichero: el simulador guarda las rondas con su propio repositorio.
            lecturas = ListaEnlazada()
            for lectura in RepositorioLecturas(self.repo_lecturas.ruta).de_sensor(sensor.id):
                if lectura.zona == zona.id:
                    lecturas.insertar(lectura)

            tramo = ultimo_tramo(lecturas)
            ultima = None
            for lectura in tramo:
                ultima = lectura
            vaciado = predecir_vaciado(lecturas)
            pendiente = recta(tramo)[1] * 60 if vaciado is not None else None

            return {
                "zona": zona.id,
                "nombre": sensor.nombre,
                "nivel": ultima.valor if ultima is not None else None,
                "estado": estado_sensor(sensor, ultima.valor) if ultima is not None else NORMAL,
                "vaciado": vaciado.isoformat() if vaciado is not None else None,
                "pendiente": pendiente,
                "umbral_aviso": sensor.umbral_aviso,
                "umbral_critico": sensor.umbral_critico,
                # La list solo se crea aquí para entregar los datos a la vista.
                "historico": [(lectura.fecha_hora, lectura.valor) for lectura in tramo],
            }
        return None

    def alertas(self, usuario: Usuario) -> list[dict]:
        """Alertas activas de sus zonas (DashboardController.alertas)."""
        ids = {zona.id for zona in self._zonas(usuario)}
        if not ids:
            return []
        return [alerta for alerta in self.dashboard.alertas(usuario) if alerta["zona"] in ids]

    def led_evacuacion(self, usuario: Usuario, zona_id: str | None = None) -> dict | None:
        """{"zona": "Z2", "id": "A3", "nombre": "Tira LED de evacuación", "encendido": False} o None.

        Sin zona_id, el de su primera zona que tenga LED (como CarpaController.ventilador).
        """
        for zona in self._zonas(usuario):
            if zona_id is not None and zona.id != zona_id:
                continue
            led = zona.actuadores.buscar(lambda actuador: actuador.tipo == "led_evacuacion")
            if led is not None:
                return {"zona": zona.id, "id": led.id, "nombre": led.nombre, "encendido": led.encendido}
        return None

    def cambiar_led(self, usuario: Usuario, encendido: bool, zona_id: str | None = None) -> str | None:
        """None si va bien, o el mensaje de error (usa ActuadoresController.cambiar)."""
        led = self.led_evacuacion(usuario, zona_id)
        if led is None:
            return "No tienes un LED de evacuación asignado"
        return self.actuadores.cambiar(led["zona"], led["id"], encendido, usuario)

    def actualizar(self) -> None:
        """Pide una ronda nueva (DashboardController.actualizar)."""
        self.dashboard.actualizar()