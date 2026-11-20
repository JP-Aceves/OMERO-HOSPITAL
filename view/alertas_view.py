"""Panel de alertas compartido por los perfiles de OMERO. Responsable: Medina (OME-60)."""
from datetime import datetime

import flet as ft

from controller.dashboard_controller import DashboardController
from model.usuario import Usuario
from service.estado import CRITICO
from view import tema


class AlertasView:

    def __init__(self, usuario: Usuario, controlador: DashboardController) -> None:
        self.usuario = usuario
        self.controlador = controlador
        self._cantidad = ft.Text(color=tema.TEXTO_SUAVE, size=13)
        self._lista = ft.ResponsiveRow(spacing=12, run_spacing=12)
        self._vacio = ft.Text(
            "No hay alertas activas en tus zonas.", size=14, color=tema.TEXTO_SUAVE,
        )
        self._error = ft.Text(
            "No se pudieron cargar las alertas. Vuelve a intentarlo.",
            size=14, color=tema.CRITICO, visible=False,
        )
        self._contenido = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            "Alertas activas", size=22, color=tema.TEXTO,
                            weight=ft.FontWeight.BOLD, font_family=tema.FUENTE_TITULOS,
                        ),
                        self._cantidad,
                    ],
                    spacing=12, wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self._error,
                self._lista,
                self._vacio,
            ],
            spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def construir(self) -> ft.Control:
        try:
            self.refrescar()
        except OSError:
            self._error.visible = True
            self._vacio.visible = False
        return self._contenido

    def refrescar(self) -> None:
        # El controlador decide qué zonas puede consultar el usuario.
        alertas = self.controlador.alertas(self.usuario)
        tarjetas = [self._tarjeta(alerta) for alerta in alertas]
        self._lista.controls = tarjetas
        self._vacio.visible = not alertas
        self._error.visible = False
        cantidad = len(alertas)
        self._cantidad.value = f"{cantidad} activa" if cantidad == 1 else f"{cantidad} activas"
        if self._contenido.page is not None:
            self._contenido.update()

    def _tarjeta(self, alerta: dict) -> ft.Control:
        nivel = alerta["nivel"]
        critico = nivel == CRITICO
        color = tema.CRITICO if critico else tema.AVISO
        numero = f"{alerta['valor']:g}".replace(".", ",")
        try:
            fecha = datetime.fromisoformat(alerta["fecha_hora"]).strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            fecha = alerta["fecha_hora"]
        return ft.Container(
            col={"xs": 12, "md": 6, "xl": 4},
            padding=16, border_radius=12, bgcolor=tema.TARJETA,
            border=ft.border.all(1, tema.BORDE),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.ERROR_OUTLINE if critico else ft.Icons.WARNING_AMBER_ROUNDED,
                                color=color, size=20,
                            ),
                            ft.Text(
                                alerta["zona_nombre"], size=14, color=tema.TEXTO,
                                weight=ft.FontWeight.BOLD, expand=True,
                            ),
                            tema.etiqueta_estado(nivel, "Crítico" if critico else "Aviso"),
                        ],
                        spacing=8, vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Text(alerta["sensor_nombre"], size=14, color=tema.TEXTO),
                    ft.Text(
                        f"{numero} {alerta['unidad']}", size=19,
                        color=color, weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(fecha, size=12, color=tema.TEXTO_SUAVE),
                ],
                spacing=6, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )
