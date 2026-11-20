"""Dashboard "Estado global" del jefe de sanidad (mockup 03). Responsable: Medina (OME-40)."""
import asyncio
from datetime import datetime

import flet as ft

from controller.dashboard_controller import DashboardController
from model.usuario import Usuario
from service.estado import AVISO, CRITICO, NORMAL
from view import tema
from view.alertas_view import AlertasView


_ESTADOS = {
    NORMAL: ("normal", "normales", tema.NORMAL),
    AVISO: ("aviso", "avisos", tema.AVISO),
    CRITICO: ("crítico", "críticos", tema.CRITICO),
}


def _punto_estado(estado: str, *, activo: bool = True, diametro: int = 10) -> ft.Control:
    color = _ESTADOS[estado][2]
    return ft.Container(
        width=diametro, height=diametro, border_radius=diametro,
        bgcolor=color if activo else ft.Colors.with_opacity(0.15, color),
        border=ft.border.all(1, color if activo else tema.BORDE),
        tooltip=_ESTADOS[estado][0].capitalize(),
    )


def _indicador_estado(estado: str) -> ft.Control:
    return ft.Row(
        [
            _punto_estado(estado),
            ft.Text(_ESTADOS[estado][0].capitalize(), size=12, color=_ESTADOS[estado][2]),
        ],
        spacing=5, tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _semaforo_zona(estado: str) -> ft.Control:
    return ft.Column(
        [
            ft.Container(
                content=ft.Row(
                    [_punto_estado(nivel, activo=nivel == estado, diametro=13) for nivel in _ESTADOS],
                    spacing=5, tight=True,
                ),
                padding=6, border_radius=12, bgcolor=tema.FONDO,
                border=ft.border.all(1, tema.BORDE),
                tooltip=f"Estado de la zona: {_ESTADOS[estado][0]}",
            ),
            ft.Text(
                _ESTADOS[estado][0].capitalize(), size=12,
                weight=ft.FontWeight.W_600, color=_ESTADOS[estado][2],
            ),
        ],
        spacing=3, tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _leyenda_estados() -> ft.Control:
    colores = {NORMAL: "Verde", AVISO: "Amarillo", CRITICO: "Rojo"}
    return ft.Row(
        [
            ft.Text("Semáforo", size=13, color=tema.TEXTO_SUAVE),
            *[
                ft.Row(
                    [
                        _punto_estado(estado),
                        ft.Text(
                            f"{colores[estado]} · {_ESTADOS[estado][0].capitalize()}",
                            size=13, color=tema.TEXTO,
                        ),
                    ],
                    spacing=6, tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
                for estado in _ESTADOS
            ],
        ],
        spacing=16, run_spacing=8, wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


class _TiempoActualizacion(ft.Text):
    def __init__(self) -> None:
        super().__init__(size=13, color=tema.TEXTO_SUAVE)
        self._momento: datetime | None = None
        self._tarea = None

    def fijar(self, momento: datetime | None) -> None:
        self._momento = momento
        self.value = self._texto()

    def _texto(self) -> str:
        if self._momento is None:
            return "Sin lecturas todavía"
        segundos = max(0, int((datetime.now() - self._momento).total_seconds()))
        if segundos < 60:
            return f"Actualizado hace {segundos} s"
        if segundos < 3600:
            return f"Actualizado hace {segundos // 60} min"
        if segundos < 86400:
            return f"Actualizado hace {segundos // 3600} h"
        return f"Actualizado hace {segundos // 86400} d"

    def did_mount(self) -> None:
        if self.page is not None:
            self._tarea = self.page.run_task(self._avanzar)

    def will_unmount(self) -> None:
        if self._tarea is not None:
            self._tarea.cancel()
            self._tarea = None

    async def _avanzar(self) -> None:
        while True:
            await asyncio.sleep(1)
            if self._tarea is None or self.page is None:
                return
            texto = self._texto()
            if texto != self.value:
                self.value = texto
                try:
                    self.update()
                except (AssertionError, RuntimeError):
                    # La navegación puede desmontar el control durante el refresco.
                    if self._tarea is not None and self.page is not None:
                        raise
                    return


class DashboardJefeView:

    def __init__(self, usuario: Usuario, controlador: DashboardController) -> None:
        self.usuario = usuario
        self.controlador = controlador

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        tiempo = _TiempoActualizacion()
        contadores = ft.Row(wrap=True, spacing=8, run_spacing=8)
        tarjetas = ft.ResponsiveRow(spacing=14, run_spacing=14)
        aviso = ft.Text(visible=False, color=tema.CRITICO, size=14)
        sin_zonas = ft.Text("Todavía no hay zonas configuradas.", color=tema.TEXTO_SUAVE)
        alertas = AlertasView(self.usuario, self.controlador)

        def mostrar_resumen() -> None:
            zonas = self.controlador.resumen()
            cantidades = self.controlador.contadores(zonas)
            tiempo.fijar(self.controlador.ultima_actualizacion)
            etiquetas = []
            for estado, (singular, plural, _) in _ESTADOS.items():
                cantidad = cantidades[estado]
                etiqueta = singular if cantidad == 1 else plural
                etiquetas.append(tema.etiqueta_estado(estado, f"{cantidad} {etiqueta}"))
            contadores.controls = etiquetas
            tarjetas.controls = [self._tarjeta(zona) for zona in zonas]
            sin_zonas.visible = not zonas
            alertas.refrescar()

        def mostrar_error() -> None:
            aviso.value = "No se pudieron actualizar las lecturas. Vuelve a intentarlo."
            aviso.visible = True

        async def actualizar(_evento: ft.ControlEvent) -> None:
            try:
                self.controlador.actualizar()
                mostrar_resumen()
            except OSError:
                mostrar_error()
            else:
                aviso.visible = False
            if contenido.page is not None:
                contenido.update()

        cabecera = ft.Column(
            [
                ft.Text(
                    "Estado global del campamento",
                    size=30, color=tema.TEXTO, weight=ft.FontWeight.BOLD,
                    font_family=tema.FUENTE_TITULOS,
                ),
                tiempo,
            ],
            spacing=4,
        )
        contenido = ft.Column(
            [
                ft.Row(
                    [cabecera, tema.boton_primario("Actualizar", actualizar, icono=ft.Icons.REFRESH)],
                    wrap=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER, run_spacing=12,
                ),
                contadores,
                _leyenda_estados(),
                aviso,
                tarjetas,
                sin_zonas,
                alertas.construir(),
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        try:
            self.controlador.inicializar()
            mostrar_resumen()
        except OSError:
            mostrar_error()
        return contenido

    def _tarjeta(self, zona: dict) -> ft.Control:
        estado = zona["estado"]
        sensores = [self._sensor(sensor) for sensor in zona["sensores"]]
        if not sensores:
            sensores = [ft.Text("Sin sensores", size=13, color=tema.TEXTO_SUAVE)]

        return ft.Container(
            col={"xs": 12, "sm": 6, "md": 4},
            bgcolor=tema.TARJETA,
            border=ft.border.all(1, tema.BORDE),
            border_radius=14,
            padding=16,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                zona["nombre"], expand=True, size=17,
                                color=tema.TEXTO, weight=ft.FontWeight.BOLD,
                            ),
                            _semaforo_zona(estado),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Text(
                        f"Responsable: {zona['responsable'] or 'Sin asignar'}",
                        size=13, color=tema.TEXTO_SUAVE,
                    ),
                    ft.Divider(height=12, color=tema.BORDE),
                    *sensores,
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

    def _sensor(self, sensor: dict) -> ft.Control:
        valor = sensor["valor"]
        if valor is None:
            lectura = ft.Text("Sin lectura", size=13, color=tema.TEXTO_SUAVE)
        else:
            numero = f"{valor:g}".replace(".", ",")
            lectura = ft.Column(
                [
                    ft.Text(
                        f"{numero} {sensor['unidad']}", size=15,
                        color=tema.TEXTO, weight=ft.FontWeight.BOLD,
                    ),
                    _indicador_estado(sensor["estado"]),
                ],
                spacing=1,
                horizontal_alignment=ft.CrossAxisAlignment.END,
            )

        return ft.Row(
            [ft.Text(sensor["nombre"], expand=True, size=13, color=tema.TEXTO), lectura],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
