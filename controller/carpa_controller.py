"""Datos del dashboard "Mi carpa" del responsable de carpa. Responsable: Rodas (OME-62).

Se apoya en DashboardController (lecturas, estado y alertas) y en
ActuadoresController (ventilador); la vista no toca el modelo.
"""
from controller.actuadores_controller import ActuadoresController
from controller.dashboard_controller import DashboardController
from model.lista_enlazada import ListaEnlazada
from model.usuario import ResponsableCarpa, Usuario


class CarpaController:

    def __init__(self, dashboard: DashboardController, actuadores: ActuadoresController) -> None:
        self.dashboard = dashboard
        self.actuadores = actuadores

    def _carpas(self, usuario: Usuario) -> ListaEnlazada:
        carpas = ListaEnlazada()
        if usuario.ROL == ResponsableCarpa.ROL:
            repositorio = self.dashboard.repo_zonas
            repositorio.recargar()
            for zona in repositorio.zonas_de(usuario.usuario):
                if zona.tipo == "carpa":
                    carpas.insertar(zona)
        return carpas

    def inicializar(self, usuario: Usuario) -> None:
        """Prepara las lecturas al entrar si el usuario tiene una carpa asignada."""
        if self._carpas(usuario):
            self.dashboard.inicializar()

    def resumen(self, usuario: Usuario) -> list[dict]:
        """Las zonas del usuario con el mismo formato que DashboardController.resumen().

        Sensores de la carpa: temperatura, humedad, calidad del aire y luz.
        """
        return self.dashboard._resumen_zonas(self._carpas(usuario))

    def alertas(self, usuario: Usuario) -> list[dict]:
        """Alertas activas de sus zonas (DashboardController.alertas)."""
        ids = {zona.id for zona in self._carpas(usuario)}
        if not ids:
            return []
        return [alerta for alerta in self.dashboard.alertas(usuario) if alerta["zona"] in ids]

    def ventilador(self, usuario: Usuario, zona_id: str | None = None) -> dict | None:
        """{"zona": "Z1", "id": "A1", "nombre": "Ventilador", "encendido": False} o None si no tiene."""
        for zona in self._carpas(usuario):
            if zona_id is not None and zona.id != zona_id:
                continue
            ventilador = zona.actuadores.buscar(lambda actuador: actuador.tipo == "ventilador")
            if ventilador is not None:
                return {
                    "zona": zona.id, "id": ventilador.id, "nombre": ventilador.nombre,
                    "encendido": ventilador.encendido,
                }
        return None

    def cambiar_ventilador(self, usuario: Usuario, encendido: bool,
                          zona_id: str | None = None) -> str | None:
        """None si va bien, o el mensaje de error (usa ActuadoresController.cambiar)."""
        ventilador = self.ventilador(usuario, zona_id)
        if ventilador is None:
            return "No tienes un ventilador asignado en esa carpa"
        return self.actuadores.cambiar(ventilador["zona"], ventilador["id"], encendido, usuario)

    def actualizar(self) -> None:
        """Pide una ronda nueva (DashboardController.actualizar)."""
        self.dashboard.actualizar()
