"""Estado y controles de ventilación y evacuación para los dashboards."""
import flet as ft

from controller.actuadores_controller import ActuadoresController
from model.usuario import Usuario
from view import tema


class ActuadoresView(ft.Column):
    def __init__(self, usuario: Usuario, controlador: ActuadoresController) -> None:
        self.usuario = usuario
        self.controlador = controlador
        self._filas = ft.Column(spacing=6)
        self._mensaje = ft.Text(color=tema.CRITICO, visible=False)
        super().__init__(
            controls=[
                ft.Row(
                    [
                        ft.Text("Actuadores", size=18, weight=ft.FontWeight.BOLD, color=tema.TEXTO),
                        tema.boton_secundario("Actualizar estados", self._actualizar),
                    ],
                    wrap=True,
                ),
                self._filas,
                self._mensaje,
            ],
            spacing=8,
        )
        self.refrescar()

    def refrescar(self, error: str | None = None) -> None:
        try:
            filas = [
                self._fila(zona.id, zona.nombre, actuador.id, actuador.nombre,
                           actuador.encendido, puede_controlar)
                for zona, actuador, puede_controlar in self.controlador.listar(self.usuario)
            ]
        except (OSError, ValueError):
            filas = []
            error = "No se pudieron consultar los actuadores"
        self._filas.controls = filas
        self._mensaje.value = error or ""
        self._mensaje.visible = bool(error)
        self.visible = bool(filas or error)

    def _fila(
        self, id_zona: str, zona: str, id_actuador: str, nombre: str,
        encendido: bool, puede_controlar: bool,
    ) -> ft.Control:
        estado = "Encendido" if encendido else "Apagado"
        controles = [ft.Text(f"{zona} · {nombre} · {estado}", color=tema.TEXTO)]
        if puede_controlar:
            async def cambiar(_evento: ft.ControlEvent) -> None:
                error = self.controlador.cambiar(id_zona, id_actuador, not encendido, self.usuario)
                self.refrescar(error)
                if self.page is not None:
                    self.update()

            accion = "Apagar" if encendido else "Encender"
            controles.append(tema.boton_secundario(accion, cambiar, tooltip=f"{accion} {nombre}"))
        return ft.Row(controles, wrap=True, spacing=12, run_spacing=4)

    async def _actualizar(self, _evento: ft.ControlEvent) -> None:
        self.refrescar()
        if self.page is not None:
            self.update()
