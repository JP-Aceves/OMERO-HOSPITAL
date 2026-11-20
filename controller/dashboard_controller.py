"""Datos del dashboard del jefe de sanidad. Responsable: Medina (OME-40)."""
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from model.usuario import Usuario
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service.alertas import alertas_de_ronda, alertas_de_zonas
from service.estado import AVISO, CRITICO, NORMAL, estado_sensor, peor_estado
from service.simulador import Simulador


class DashboardController:

    def __init__(
        self,
        repo_zonas: RepositorioZonas,
        repo_lecturas: RepositorioLecturas,
        simulador: Simulador,
    ) -> None:
        self.repo_zonas = repo_zonas
        self.repo_lecturas = repo_lecturas
        self.simulador = simulador
        self._ultima_ronda = ListaEnlazada()
        self.ultima_actualizacion: datetime | None = None

    def inicializar(self) -> None:
        """Sincroniza los semáforos y genera la primera ronda si faltan lecturas."""
        hay_sensores = False
        for zona in self.repo_zonas.listar():
            for sensor in zona.sensores:
                hay_sensores = True
                if self._ultima_lectura(zona.id, sensor.id) is not None:
                    self._sincronizar_semaforos()
                    return
        if hay_sensores:
            self.actualizar()
        else:
            self._sincronizar_semaforos()

    def _ultima_lectura(self, zona_id: str, sensor_id: str) -> Lectura | None:
        lectura = self._ultima_ronda.buscar(
            lambda dato: dato.zona == zona_id and dato.sensor == sensor_id
        )
        if lectura is not None:
            return lectura
        lectura = self.repo_lecturas.ultima(sensor_id)
        if lectura is not None and lectura.zona == zona_id:
            return lectura
        return None

    def resumen(self) -> list[dict]:
        """Una entrada por zona, lista para pintar (la vista no toca el modelo):

        {"id": "Z1", "nombre": "...", "responsable": "carpa", "estado": "aviso",
         "sensores": [{"nombre": "...", "valor": 31.4, "unidad": "°C", "estado": "aviso"}, ...]}
        Si un sensor aún no tiene lecturas: "valor": None y "estado": "normal".
        La list solo se crea aquí para entregar los datos a la vista; los datos viven en ListaEnlazada.
        """
        return self._resumen_zonas(self.repo_zonas.listar())

    def _resumen_zonas(self, zonas_modelo: ListaEnlazada) -> list[dict]:
        zonas = []
        ultima_actualizacion = None
        for zona in zonas_modelo:
            sensores = []
            estados = ListaEnlazada()
            for sensor in zona.sensores:
                lectura = self._ultima_lectura(zona.id, sensor.id)
                estado = NORMAL
                if lectura is not None:
                    estado = estado_sensor(sensor, lectura.valor)
                    momento = datetime.fromisoformat(lectura.fecha_hora)
                    if momento.tzinfo is not None:
                        momento = momento.astimezone().replace(tzinfo=None)
                    if ultima_actualizacion is None or momento > ultima_actualizacion:
                        ultima_actualizacion = momento
                estados.insertar(estado)
                sensores.append({
                    "nombre": sensor.nombre,
                    "valor": lectura.valor if lectura is not None else None,
                    "unidad": lectura.unidad if lectura is not None else sensor.UNIDAD,
                    "estado": estado,
                })
            zonas.append({
                "id": zona.id,
                "nombre": zona.nombre,
                "responsable": zona.responsable,
                "estado": peor_estado(estados),
                "sensores": sensores,
            })
        self.ultima_actualizacion = ultima_actualizacion
        return zonas

    def contadores(self, zonas: list[dict] | None = None) -> dict[str, int]:
        """{"normal": 1, "aviso": 1, "critico": 1} contando zonas."""
        contadores = {NORMAL: 0, AVISO: 0, CRITICO: 0}
        for zona in self.resumen() if zonas is None else zonas:
            contadores[zona["estado"]] += 1
        return contadores

    def actualizar(self) -> None:
        """Pide una ronda nueva al simulador."""
        # OME-64 (HU-09): antes de cada lectura se releen las zonas, así un umbral
        # cambiado en "Zonas y sensores" se aplica en la siguiente lectura.
        self.repo_zonas.recargar()
        if self.simulador.repo_zonas is not self.repo_zonas:
            self.simulador.repo_zonas.recargar()
        # El simulador ya guarda la ronda y puede usar otro repositorio en memoria.
        self._ultima_ronda = self.simulador.generar_ronda()
        self._sincronizar_semaforos()

    def _sincronizar_semaforos(self) -> None:
        # Otro controlador puede haber cambiado umbrales o actuadores desde el login.
        repositorio = RepositorioZonas(self.repo_zonas.ruta)
        cambios = False
        for resumen in self._resumen_zonas(repositorio.listar()):
            zona = repositorio.buscar(resumen["id"])
            for actuador in zona.actuadores:
                if actuador.tipo == "led_semaforo":
                    if actuador.estado != resumen["estado"] or not actuador.encendido:
                        actuador.fijar_estado(resumen["estado"])
                        actuador.encender()
                        cambios = True
        if cambios:
            # Publica el JSON completo para poder reintentar si falla la escritura.
            ruta = repositorio.ruta
            with NamedTemporaryFile(
                dir=ruta.parent, prefix=f".{ruta.name}-", suffix=".tmp", delete=False,
            ) as temporal:
                ruta_temporal = Path(temporal.name)
            try:
                repositorio.ruta = ruta_temporal
                repositorio.guardar()
                ruta_temporal.replace(ruta)
            finally:
                repositorio.ruta = ruta
                ruta_temporal.unlink(missing_ok=True)
        self.repo_zonas = repositorio

    def alertas(self, usuario: Usuario | None = None) -> list[dict]:
        """Alertas activas de la última ronda (OME-60, Medina). Usa service/alertas.py.

        El jefe y las llamadas internas sin usuario reciben todas las alertas.
        Carpa y logística reciben las correspondientes a sus zonas asignadas.
        [{"zona": "Z1", "zona_nombre": "Carpa de hospitalización", "sensor": "S1",
          "sensor_nombre": "DHT22 temperatura", "valor": 33.2, "unidad": "°C",
          "nivel": "critico", "fecha_hora": "2026-11-24T18:30:00"}, ...]
        """
        if usuario is not None and usuario.ROL not in (
            "jefe_sanidad", "responsable_carpa", "tecnico_logistica",
        ):
            return []

        zonas = self.repo_zonas.cargar()
        repositorio = RepositorioLecturas(self.repo_lecturas.ruta)
        lecturas = ListaEnlazada()
        ids_permitidos = ListaEnlazada()
        ve_todas = usuario is None or usuario.ROL == "jefe_sanidad"
        for zona in zonas:
            if ve_todas or zona.responsable == usuario.usuario:
                ids_permitidos.insertar(zona.id)
            for sensor in zona.sensores:
                ultima = None
                for lectura in repositorio.de_sensor(sensor.id):
                    if lectura.zona == zona.id and lectura.tipo == sensor.TIPO:
                        ultima = lectura
                if ultima is not None:
                    lecturas.insertar(ultima)

        activas = alertas_de_zonas(alertas_de_ronda(zonas, lecturas), ids_permitidos)
        resultado = []
        for alerta in activas:
            zona = zonas.buscar(lambda dato: dato.id == alerta.zona)
            sensor = zona.buscar_sensor(alerta.sensor)
            resultado.append({
                **alerta.to_dict(),
                "zona_nombre": zona.nombre,
                "sensor_nombre": sensor.nombre,
            })
        return resultado
