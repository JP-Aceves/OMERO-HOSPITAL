"""Dashboard "Mi carpa" del responsable de carpa (mockup 04). Responsable: Rodas (OME-62)."""
import flet as ft

from controller.carpa_controller import CarpaController
from model.usuario import Usuario
from service.estado import CRITICO
from view import tema
from view.alertas_view import AlertasView


class DashboardCarpaView:

    def __init__(self, usuario: Usuario, controlador: CarpaController) -> None:
        self.usuario = usuario
        self.controlador = controlador

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        carpas = ft.Column(spacing=16, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        sin_carpa = ft.Text("No tienes ninguna carpa asignada.", color=tema.TEXTO_SUAVE, visible=False)
        aviso = ft.Text(color=tema.CRITICO, visible=False)
        alertas = AlertasView(self.usuario, self.controlador)
        panel_alertas = ft.Column()

        def mostrar_error(mensaje: str | None) -> None:
            aviso.value = mensaje or ""
            aviso.visible = bool(mensaje)

        def mostrar_carpas() -> None:
            zonas = self.controlador.resumen(self.usuario)
            carpas.controls = [tarjeta_carpa(zona) for zona in zonas]
            sin_carpa.visible = not zonas
            boton_actualizar.disabled = not zonas

        def mostrar_alertas() -> None:
            if panel_alertas.controls:
                alertas.refrescar()
            else:
                panel_alertas.controls.append(alertas.construir())

        def refrescar() -> None:
            """OME-71: main.py la llama tras cada ronda de lecturas automática."""
            try:
                mostrar_carpas()
                mostrar_alertas()
            except (OSError, ValueError):
                mostrar_error("No se pudieron actualizar las lecturas. Vuelve a intentarlo.")
            else:
                mostrar_error(None)
            if contenido.page is not None:
                contenido.update()

        async def actualizar(_evento: ft.ControlEvent) -> None:
            try:
                self.controlador.actualizar()
            except (OSError, ValueError):
                mostrar_error("No se pudieron actualizar las lecturas. Vuelve a intentarlo.")
                if contenido.page is not None:
                    contenido.update()
                return
            refrescar()

        self.refrescar = refrescar

        def tarjeta_carpa(zona: dict) -> ft.Control:
            sensores = [self._sensor(sensor) for sensor in zona["sensores"]]
            lecturas = (
                ft.ResponsiveRow(sensores, spacing=12, run_spacing=12)
                if sensores else ft.Text("Sin sensores configurados.", color=tema.TEXTO_SUAVE)
            )
            ventilador = self.controlador.ventilador(self.usuario, zona["id"])
            if ventilador is None:
                ventilacion = ft.Text("Esta carpa no tiene ventilador.", color=tema.TEXTO_SUAVE)
            else:
                encendido = ventilador["encendido"]
                accion = "Apagar" if encendido else "Encender"
                estado = "Encendido" if encendido else "Apagado"

                async def cambiar(_evento: ft.ControlEvent) -> None:
                    try:
                        error = self.controlador.cambiar_ventilador(
                            self.usuario, not encendido, zona["id"],
                        )
                        mostrar_carpas()
                    except (OSError, ValueError):
                        error = "No se pudo consultar el estado del ventilador. Vuelve a intentarlo."
                    mostrar_error(error)
                    if contenido.page is not None:
                        contenido.update()

                ventilacion = ft.Row(
                    [
                        ft.Text(f"{ventilador['nombre']} · {estado}", color=tema.TEXTO),
                        tema.boton_secundario(f"{accion} ventilador", cambiar),
                    ],
                    wrap=True, spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            return ft.Column(
                [
                    ft.Text(
                        zona["nombre"], size=22, color=tema.TEXTO, font_family=tema.FUENTE_TITULOS,
                    ),
                    lecturas,
                    ventilacion,
                ],
                spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            )

        boton_actualizar = tema.boton_primario("Actualizar", actualizar, icono=ft.Icons.REFRESH)
        cabecera = ft.Row(
            [
                ft.Text("Mi carpa", size=30, color=tema.TEXTO, font_family=tema.FUENTE_TITULOS),
                boton_actualizar,
            ],
            wrap=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        contenido = ft.Column(
            [cabecera, aviso, carpas, sin_carpa, panel_alertas],
            spacing=16, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        try:
            self.controlador.inicializar(self.usuario)
            mostrar_carpas()
            mostrar_alertas()
        except (OSError, ValueError):
            mostrar_error("No se pudieron cargar los datos de la carpa. Pulsa Actualizar.")
        return contenido

    @staticmethod
    def _sensor(sensor: dict) -> ft.Control:
        valor = sensor["valor"]
        texto = (
            "Sin lectura" if valor is None
            else f"{valor:g}".replace(".", ",") + f" {sensor['unidad']}"
        )
        controles = [
            ft.Text(sensor["nombre"], size=14, color=tema.TEXTO),
            ft.Text(texto, size=22, weight=ft.FontWeight.BOLD, color=tema.TEXTO),
        ]
        if valor is not None:
            estado = sensor["estado"]
            controles.append(tema.etiqueta_estado(estado, "Crítico" if estado == CRITICO else None))
        return ft.Container(
            col={"xs": 12, "sm": 6, "lg": 3},
            bgcolor=tema.TARJETA, border=ft.border.all(1, tema.BORDE),
            border_radius=12, padding=16,
            content=ft.Column(controles, spacing=8),
        )
