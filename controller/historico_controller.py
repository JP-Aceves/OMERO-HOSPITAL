"""Histórico de lecturas y sus estadísticas (HU-10, mockup 07). Responsable: JP (OME-70).

El jefe de sanidad consulta todas las zonas; el responsable de carpa y el
técnico de logística, solo las suyas. Las lecturas viven en ListaEnlazada:
las list solo se crean al final para entregar los datos a la vista.
"""
from datetime import datetime

from model.lista_enlazada import ListaEnlazada
from model.usuario import Usuario
from persistence.repositorio_lecturas import RepositorioLecturas
from persistence.repositorio_zonas import RepositorioZonas
from service.estado import estado_sensor

FORMATOS_FECHA = ("%d/%m/%Y %H:%M", "%d/%m/%Y")
MAXIMO_PUNTOS_GRAFICA = 300  # con más, la gráfica de Flet va lenta y no se ve mejor


def leer_fecha(texto: str, fin_del_dia: bool = False) -> datetime | None:
    """"23/11/2026 18:30" o "23/11/2026". Sin hora, el día entero. None si no es una fecha."""
    texto = (texto or "").strip()
    for formato in FORMATOS_FECHA:
        try:
            fecha = datetime.strptime(texto, formato)
        except ValueError:
            continue
        if formato == "%d/%m/%Y" and fin_del_dia:
            fecha = fecha.replace(hour=23, minute=59, second=59)
        return fecha
    return None


class HistoricoController:

    def __init__(self, repo_zonas: RepositorioZonas, repo_lecturas: RepositorioLecturas) -> None:
        self.repo_zonas = repo_zonas
        self.repo_lecturas = repo_lecturas

    def zonas(self, usuario: Usuario) -> list[dict]:
        """Las zonas que puede consultar el usuario: [{"id": "Z1", "nombre": "..."}, ...]."""
        return [{"id": zona.id, "nombre": zona.nombre} for zona in self._zonas_visibles(usuario)]

    def sensores(self, usuario: Usuario, id_zona: str) -> list[dict]:
        """Sensores de esa zona: [{"id": "S1", "nombre": "...", "tipo": "temperatura", "unidad": "°C"}]."""
        zona = self._zona(usuario, id_zona)
        if zona is None:
            return []
        return [{"id": s.id, "nombre": s.nombre, "tipo": s.TIPO, "unidad": s.UNIDAD} for s in zona.sensores]

    def consultar(self, usuario: Usuario, id_zona: str, id_sensor: str,
                  desde: str = "", hasta: str = "") -> dict | str:
        """Lecturas del sensor entre dos fechas (vacías = sin límite) y sus estadísticas.

        Devuelve el texto del error, o:
        {"zona": "...", "sensor": "...", "tipo": "temperatura", "unidad": "°C",
         "umbral_aviso": 28, "umbral_critico": 32, "inverso": False,
         "lecturas": [{"fecha_hora": "2026-11-23T18:30:00", "valor": 31.4, "estado": "aviso"}, ...],
         "grafica": [...las mismas, reducidas a MAXIMO_PUNTOS_GRAFICA...],
         "total": 98, "media": 26.9, "maximo": {...lectura...}, "minimo": {...lectura...}}
        Sin lecturas en el periodo: "total": 0 y media, maximo y minimo a None.
        """
        if not id_zona:
            return "Elige una zona"
        zona = self._zona(usuario, id_zona)
        if zona is None:
            return "No tienes acceso a esa zona"
        if not id_sensor:
            return "Elige un sensor"
        sensor = zona.buscar_sensor(id_sensor)
        if sensor is None:
            return "Ese sensor no es de la zona elegida"

        inicio = fin = None
        if (desde or "").strip():
            inicio = leer_fecha(desde)
            if inicio is None:
                return "La fecha «Desde» debe tener el formato dd/mm/aaaa hh:mm"
        if (hasta or "").strip():
            fin = leer_fecha(hasta, fin_del_dia=True)
            if fin is None:
                return "La fecha «Hasta» debe tener el formato dd/mm/aaaa hh:mm"
        if inicio is not None and fin is not None and inicio > fin:
            return "La fecha «Desde» no puede ser posterior a «Hasta»"

        lecturas = ListaEnlazada()
        for lectura in self.repo_lecturas.de_sensor(sensor.id):
            if lectura.zona != zona.id:
                continue
            momento = datetime.fromisoformat(lectura.fecha_hora)
            if (inicio is None or momento >= inicio) and (fin is None or momento <= fin):
                lecturas.insertar(lectura)

        total, suma, maximo, minimo = 0, 0.0, None, None
        for lectura in lecturas:
            total += 1
            suma += lectura.valor
            if maximo is None or lectura.valor > maximo.valor:
                maximo = lectura
            if minimo is None or lectura.valor < minimo.valor:
                minimo = lectura

        filas = [self._fila(sensor, lectura) for lectura in lecturas]
        return {
            "zona": zona.nombre, "sensor": sensor.nombre, "tipo": sensor.TIPO, "unidad": sensor.UNIDAD,
            "umbral_aviso": sensor.umbral_aviso, "umbral_critico": sensor.umbral_critico,
            "inverso": sensor.INVERSO,
            "lecturas": filas,
            "grafica": self._reducir(filas),
            "total": total,
            "media": round(suma / total, 1) if total else None,
            "maximo": self._fila(sensor, maximo) if maximo else None,
            "minimo": self._fila(sensor, minimo) if minimo else None,
        }

    # ---------- privados ----------

    def _zonas_visibles(self, usuario: Usuario) -> ListaEnlazada:
        if usuario.ROL == "jefe_sanidad":
            return self.repo_zonas.listar()
        return self.repo_zonas.zonas_de(usuario.usuario)

    def _zona(self, usuario: Usuario, id_zona: str):
        return self._zonas_visibles(usuario).buscar(lambda zona: zona.id == id_zona)

    @staticmethod
    def _fila(sensor, lectura) -> dict:
        return {"fecha_hora": lectura.fecha_hora, "valor": lectura.valor,
                "estado": estado_sensor(sensor, lectura.valor)}

    @staticmethod
    def _reducir(filas: list[dict]) -> list[dict]:
        """Si hay demasiadas lecturas, coge una de cada N (siempre la última) para la gráfica."""
        if len(filas) <= MAXIMO_PUNTOS_GRAFICA:
            return filas
        paso = len(filas) / MAXIMO_PUNTOS_GRAFICA
        reducidas = [filas[int(i * paso)] for i in range(MAXIMO_PUNTOS_GRAFICA - 1)]
        reducidas.append(filas[-1])
        return reducidas
