"""Datos del dashboard del jefe de sanidad. Responsable: Medina (OME-40)."""
from datetime import datetime

from model.lectura import Lectura
from model.lista_enlazada import ListaEnlazada
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
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
        """Genera la primera ronda si hay sensores y ninguno tiene lecturas."""
        hay_sensores = False
        for zona in self.repo_zonas.listar():
            for sensor in zona.sensores:
                hay_sensores = True
                if self._ultima_lectura(zona.id, sensor.id) is not None:
                    return
        if hay_sensores:
            self.actualizar()

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
        zonas = []
        ultima_actualizacion = None
        for zona in self.repo_zonas.listar():
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
        # El simulador ya guarda la ronda y puede usar otro repositorio en memoria.
        self._ultima_ronda = self.simulador.generar_ronda()
