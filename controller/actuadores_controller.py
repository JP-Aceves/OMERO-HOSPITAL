"""Consulta y control de los actuadores de cada zona (OME-66)."""
from collections.abc import Iterator

from model.actuador import Actuador
from model.alerta import Alerta
from model.lista_enlazada import ListaEnlazada
from model.sensor import SensorHumoGas
from model.usuario import Administrador, JefeSanidad, ResponsableCarpa, TecnicoLogistica, Usuario
from model.zona import Zona
from persistence.repositorio_zonas import RepositorioZonas
from service.alertas import hay_alerta_critica
from service.estado import CRITICO


class _OrdenNoValida(ValueError):
    pass


class ActuadoresController:

    def __init__(self, repo_zonas: RepositorioZonas) -> None:
        self.repo_zonas = repo_zonas

    def de_zona(self, id_zona: str) -> ListaEnlazada:
        """Los Actuador de la zona, con su estado."""
        zona = self.repo_zonas.cargar().buscar(lambda dato: dato.id == id_zona)
        return zona.actuadores if zona is not None else ListaEnlazada()

    def listar(self, usuario: Usuario) -> Iterator[tuple[Zona, Actuador, bool]]:
        """Datos del panel de estado para los roles con acceso a la aplicación."""
        if usuario.ROL not in (
            Administrador.ROL, JefeSanidad.ROL, ResponsableCarpa.ROL, TecnicoLogistica.ROL
        ):
            return
        for zona in self.repo_zonas.cargar():
            for actuador in zona.actuadores:
                if actuador.tipo in ("ventilador", "led_evacuacion"):
                    yield zona, actuador, self._puede_controlar(usuario, zona, actuador)

    @staticmethod
    def _puede_controlar(usuario: Usuario, zona: Zona, actuador: Actuador) -> bool:
        asignada = zona.responsable == usuario.usuario
        if actuador.tipo == "ventilador":
            return usuario.ROL == JefeSanidad.ROL or (
                asignada and usuario.ROL == ResponsableCarpa.ROL and zona.tipo == "carpa"
            )
        return actuador.tipo == "led_evacuacion" and asignada and usuario.ROL == TecnicoLogistica.ROL

    def cambiar(self, id_zona: str, id_actuador: str, encendido: bool, usuario: Usuario) -> str | None:
        """Cambio manual. Comprueba el permiso del usuario según el tipo de actuador y lo guarda."""
        def cambiar_estado(zonas: ListaEnlazada) -> bool:
            zona = zonas.buscar(lambda dato: dato.id == id_zona)
            if zona is None:
                raise _OrdenNoValida("La zona no existe")
            actuador = zona.actuadores.buscar(lambda dato: dato.id == id_actuador)
            if actuador is None:
                raise _OrdenNoValida("El actuador no existe en esa zona")
            if not self._puede_controlar(usuario, zona, actuador):
                raise _OrdenNoValida("No tienes permiso para controlar ese actuador")
            if actuador.encendido == encendido:
                return False
            if encendido:
                actuador.encender()
            else:
                actuador.apagar()
            return True

        try:
            self.repo_zonas.modificar_estados(cambiar_estado)
        except _OrdenNoValida as error:
            return str(error)
        except (OSError, ValueError):
            return "No se pudo guardar el estado del actuador"
        return None

    def aplicar_alertas(self, alertas: ListaEnlazada) -> None:
        """Enciende el LED de evacuación de las zonas con alerta crítica de humo/gas."""
        def es_critica_de_humo(alerta: Alerta) -> bool:
            return alerta.tipo == SensorHumoGas.TIPO and alerta.nivel == CRITICO

        if not hay_alerta_critica(alertas, SensorHumoGas.TIPO):
            return

        def activar(zonas: ListaEnlazada) -> bool:
            cambio = False
            for alerta in alertas:
                if not es_critica_de_humo(alerta):
                    continue
                zona = zonas.buscar(lambda dato: dato.id == alerta.zona)
                sensor = zona.buscar_sensor(alerta.sensor) if zona is not None else None
                if not isinstance(sensor, SensorHumoGas):
                    continue
                for actuador in zona.actuadores:
                    if actuador.tipo == "led_evacuacion" and not actuador.encendido:
                        actuador.encender()
                        cambio = True
            return cambio

        self.repo_zonas.modificar_estados(activar)
