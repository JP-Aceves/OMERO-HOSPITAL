"""Dashboard "Recursos" del técnico de logística (mockup 05). Responsable: Ivan (OME-63)."""
from datetime import datetime

import flet as ft

from controller.tecnico_controller import TecnicoController
from model.usuario import Usuario
from service.estado import AVISO, CRITICO, NORMAL
from service.prediccion import MINIMO_LECTURAS
from view import tema
from view.alertas_view import AlertasView

NOMBRE_ESTADO = {NORMAL: "Normal", AVISO: "Aviso", CRITICO: "Crítico"}
COLOR_ESTADO = {NORMAL: tema.NORMAL, AVISO: tema.AVISO, CRITICO: tema.CRITICO}
ALTO_DEPOSITO = 116  # alto interior del dibujo del depósito, en píxeles


def numero(valor: float) -> str:
    """31.4 -> "31,4" y 40.0 -> "40" (coma decimal, como en el resto de la app)."""
    return f"{round(valor, 1):g}".replace(".", ",")


def fecha_corta(fecha_hora: str) -> str:
    """"2026-11-25T20:54:00" -> "25/11 20:54"."""
    return datetime.fromisoformat(fecha_hora).strftime("%d/%m %H:%M")


def minutos_entre(desde: str, hasta: str) -> float:
    return (datetime.fromisoformat(hasta) - datetime.fromisoformat(desde)).total_seconds() / 60


def tiempo_restante(minutos: float) -> str:
    """545 -> "9 h 5 min"; 35 -> "35 min"; 8318 -> "5 d 18 h"."""
    horas, resto = divmod(max(0, round(minutos)), 60)
    if horas >= 24:
        return f"{horas // 24} d {horas % 24} h"
    return f"{horas} h {resto} min" if horas else f"{resto} min"


def momento_actualizacion(momento: datetime | None, hoy: datetime | None = None) -> str:
    """" · actualizado a las 19:09", con la fecha si las lecturas no son de hoy."""
    if momento is None:
        return " · sin lecturas todavía"
    hoy = hoy or datetime.now()
    if momento.date() == hoy.date():
        return f" · actualizado a las {momento:%H:%M}"
    return f" · actualizado el {momento:%d/%m} a las {momento:%H:%M}"


def tarjeta(titulo: str, chip: ft.Control | None, cuerpo: list[ft.Control], col: dict) -> ft.Container:
    cabecera = ft.Row(
        [ft.Text(titulo, size=15, color=tema.TEXTO, weight=ft.FontWeight.W_600, expand=True)]
        + ([chip] if chip is not None else []),
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Container(
        col=col, bgcolor=tema.TARJETA, border=ft.border.all(1, tema.BORDE),
        border_radius=12, padding=20,
        content=ft.Column([cabecera, *cuerpo], spacing=10),
    )


class DashboardTecnicoView:

    def __init__(self, usuario: Usuario, controlador: TecnicoController) -> None:
        self.usuario = usuario
        self.controlador = controlador

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        subtitulo = ft.Text(size=14, color=tema.TEXTO_SUAVE)
        chip_critico = ft.Container(visible=False)
        aviso = ft.Text(color=tema.CRITICO, visible=False)
        tarjetas = ft.ResponsiveRow(spacing=16, run_spacing=16)
        grafica = ft.Container()
        sin_zonas = ft.Text("No tienes ninguna zona asignada.", color=tema.TEXTO_SUAVE, visible=False)
        alertas = AlertasView(self.usuario, self.controlador)
        panel_alertas = ft.Column()

        def refrescar() -> None:
            if contenido.page is not None:
                contenido.update()

        def mostrar_error(mensaje: str | None) -> None:
            aviso.value = mensaje or ""
            aviso.visible = bool(mensaje)

        def mostrar_datos() -> None:
            zonas = self.controlador.resumen(self.usuario)
            deposito = self.controlador.deposito(self.usuario)

            sin_zonas.visible = not zonas
            boton_actualizar.disabled = not zonas
            nombres = " y ".join(zona["nombre"] for zona in zonas)
            subtitulo.value = nombres + momento_actualizacion(self.controlador.dashboard.ultima_actualizacion)

            criticos = [
                sensor["nombre"] for zona in zonas for sensor in zona["sensores"]
                if sensor["valor"] is not None and sensor["estado"] == CRITICO
            ]
            chip_critico.content = tema.etiqueta_estado(CRITICO, "Crítico: " + ", ".join(criticos))
            chip_critico.visible = bool(criticos)

            controles = []
            if deposito is not None:
                controles.append(self._tarjeta_deposito(deposito))
            for zona in zonas:
                for sensor in zona["sensores"]:
                    if sensor["tipo"] == "humo_gas":
                        # Cada tarjeta de humo controla el LED de su propia zona.
                        led = self.controlador.led_evacuacion(self.usuario, zona["id"])
                        controles.append(self._tarjeta_humo(sensor, led, cambiar_led))
                    elif sensor["tipo"] != "nivel_deposito":
                        controles.append(self._tarjeta_sensor(sensor))
            tarjetas.controls = controles
            grafica.content = self._grafica(deposito) if deposito is not None else None

        def mostrar_alertas() -> None:
            if panel_alertas.controls:
                alertas.refrescar()
            else:
                panel_alertas.controls.append(alertas.construir())

        def refrescar_datos() -> None:
            """OME-71: main.py la llama tras cada ronda de lecturas automática."""
            try:
                mostrar_datos()
                mostrar_alertas()
            except (OSError, ValueError):
                mostrar_error("No se pudieron actualizar las lecturas. Vuelve a intentarlo.")
            else:
                mostrar_error(None)
            refrescar()

        async def actualizar(_evento: ft.ControlEvent) -> None:
            try:
                self.controlador.actualizar()
            except (OSError, ValueError):
                mostrar_error("No se pudieron actualizar las lecturas. Vuelve a intentarlo.")
                refrescar()
                return
            refrescar_datos()

        self.refrescar = refrescar_datos

        async def cambiar_led(encendido: bool, zona_id: str) -> None:
            try:
                error = self.controlador.cambiar_led(self.usuario, encendido, zona_id)
                mostrar_datos()
            except (OSError, ValueError):
                error = "No se pudo cambiar el LED de evacuación. Vuelve a intentarlo."
            mostrar_error(error)
            refrescar()

        boton_actualizar = tema.boton_primario("Actualizar", actualizar, icono=ft.Icons.REFRESH)
        cabecera = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("Recursos y riesgos", size=30, color=tema.TEXTO,
                                font_family=tema.FUENTE_TITULOS),
                        subtitulo,
                    ],
                    spacing=2,
                ),
                ft.Row([chip_critico, boton_actualizar], spacing=12, wrap=True,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ],
            wrap=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        contenido = ft.Column(
            [cabecera, aviso, sin_zonas, tarjetas, grafica, panel_alertas],
            spacing=16, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        try:
            self.controlador.inicializar(self.usuario)
            mostrar_datos()
            mostrar_alertas()
        except (OSError, ValueError):
            mostrar_error("No se pudieron cargar los recursos. Pulsa Actualizar.")
        return contenido

    # ---------- tarjetas ----------

    @staticmethod
    def _tarjeta_deposito(deposito: dict) -> ft.Control:
        nivel = deposito["nivel"]
        estado = deposito["estado"]
        color = COLOR_ESTADO[estado]
        relleno = 0 if nivel is None else round(ALTO_DEPOSITO * max(0, min(nivel, 100)) / 100)
        dibujo = ft.Container(
            width=64, height=ALTO_DEPOSITO + 8, padding=2, border_radius=10,
            border=ft.border.all(2, tema.TEXTO_SUAVE),
            content=ft.Column(
                [ft.Container(height=relleno, bgcolor=color, border_radius=6)],
                alignment=ft.MainAxisAlignment.END, spacing=0,
            ),
        )

        if deposito["vaciado"] is not None:
            ultima = deposito["historico"][-1][0]
            restante = tiempo_restante(minutos_entre(ultima, deposito["vaciado"]))
            textos = [
                ft.Row(
                    [
                        ft.Text(restante, size=28, weight=ft.FontWeight.BOLD, color=tema.TEXTO,
                                key="tecnico_restante"),
                        ft.Text("restantes", size=14, color=tema.TEXTO_SUAVE),
                    ],
                    spacing=6, wrap=True, vertical_alignment=ft.CrossAxisAlignment.END,
                ),
                ft.Text(f"Se vaciará el {fecha_corta(deposito['vaciado'])}", size=13, color=tema.TEXTO),
                ft.Text(
                    f"Predicción por regresión lineal ({numero(deposito['pendiente'])} % por hora)",
                    size=13, color=tema.TEXTO_SUAVE,
                ),
            ]
        else:
            if nivel is None:
                motivo = "Todavía no hay lecturas del depósito."
            elif len(deposito["historico"]) < MINIMO_LECTURAS:
                motivo = f"Hacen falta {MINIMO_LECTURAS} lecturas desde el último rellenado."
            else:
                motivo = "El nivel no baja."
            textos = [
                ft.Text("Sin predicción", size=20, weight=ft.FontWeight.BOLD, color=tema.TEXTO,
                        key="tecnico_restante"),
                ft.Text(motivo, size=13, color=tema.TEXTO_SUAVE),
            ]

        chip = None if nivel is None else tema.etiqueta_estado(estado, f"{numero(nivel)} %")
        return tarjeta(
            "Depósito de agua", chip,
            [ft.Row([dibujo, ft.Column(textos, spacing=4, expand=True)], spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.END)],
            {"xs": 12, "md": 6, "xl": 4},
        )

    @staticmethod
    def _valor(sensor: dict) -> list[ft.Control]:
        valor = sensor["valor"]
        principal = (
            ft.Text("Sin lectura", size=22, color=tema.TEXTO_SUAVE) if valor is None
            else ft.Row(
                [
                    ft.Text(numero(valor), size=34, weight=ft.FontWeight.BOLD, color=tema.TEXTO),
                    ft.Text(sensor["unidad"], size=15, color=tema.TEXTO_SUAVE),
                ],
                spacing=6, vertical_alignment=ft.CrossAxisAlignment.END,
            )
        )
        umbrales = ft.Text(
            f"Aviso {numero(sensor['umbral_aviso'])} {sensor['unidad']} · "
            f"crítico {numero(sensor['umbral_critico'])} {sensor['unidad']}",
            size=13, color=tema.TEXTO_SUAVE,
        )
        return [principal, umbrales]

    @staticmethod
    def _chip(sensor: dict) -> ft.Control | None:
        if sensor["valor"] is None:
            return None
        return tema.etiqueta_estado(sensor["estado"], NOMBRE_ESTADO[sensor["estado"]])

    def _tarjeta_humo(self, sensor: dict, led: dict | None, cambiar_led) -> ft.Control:
        cuerpo = self._valor(sensor)
        if led is None:
            cuerpo.append(ft.Text("Esta zona no tiene LED de evacuación.", size=13, color=tema.TEXTO_SUAVE))
        else:
            encendido = led["encendido"]

            async def pulsar(_evento: ft.ControlEvent) -> None:
                await cambiar_led(not encendido, led["zona"])

            if encendido:
                boton = tema.boton_secundario("Desactivar evacuación", pulsar, key="tecnico_led")
            else:
                boton = ft.ElevatedButton(
                    text="Activar evacuación", on_click=pulsar, color=tema.TARJETA, bgcolor=tema.CRITICO,
                    height=48, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    key="tecnico_led",
                )
            cuerpo += [
                ft.Text(f"{led['nombre']}: {'encendidos' if encendido else 'apagados'}",
                        size=13, color=tema.TEXTO),
                boton,
            ]
        return tarjeta(sensor["nombre"], self._chip(sensor), cuerpo, {"xs": 12, "md": 6, "xl": 4})

    def _tarjeta_sensor(self, sensor: dict) -> ft.Control:
        return tarjeta(sensor["nombre"], self._chip(sensor), self._valor(sensor), {"xs": 12, "md": 6, "xl": 4})

    # ---------- gráfica ----------

    @staticmethod
    def _grafica(deposito: dict) -> ft.Control:
        titulo = ft.Text("Nivel del depósito (%) y predicción", size=15, color=tema.TEXTO,
                         weight=ft.FontWeight.W_600)
        historico = deposito["historico"]
        if len(historico) < 2:
            cuerpo = ft.Text("Aún no hay lecturas suficientes para la gráfica.", color=tema.TEXTO_SUAVE)
            return tarjeta("Nivel del depósito (%) y predicción", None, [cuerpo], {"xs": 12})

        inicio = historico[0][0]
        puntos = [(minutos_entre(inicio, fecha), nivel, fecha) for fecha, nivel in historico]
        ultimo_x, ultimo_nivel, _ = puntos[-1]
        series = [
            ft.LineChartData(
                data_points=[
                    ft.LineChartDataPoint(x, nivel, tooltip=f"{fecha_corta(fecha)}\n{numero(nivel)} %")
                    for x, nivel, fecha in puntos
                ],
                color=tema.PRIMARIO, stroke_width=2.5,
                below_line_bgcolor=ft.Colors.with_opacity(0.08, tema.PRIMARIO),
            ),
        ]
        etiquetas = [(0, inicio), (ultimo_x, historico[-1][0])]
        maximo_x = ultimo_x
        if deposito["vaciado"] is not None:
            vaciado_x = minutos_entre(inicio, deposito["vaciado"])
            maximo_x = max(ultimo_x, vaciado_x)
            # Predicción: de la última lectura hasta el 0 % en la hora de vaciado.
            series.append(ft.LineChartData(
                data_points=[
                    ft.LineChartDataPoint(ultimo_x, ultimo_nivel, show_tooltip=False),
                    ft.LineChartDataPoint(vaciado_x, 0,
                                          tooltip=f"Vacío el {fecha_corta(deposito['vaciado'])}"),
                ],
                color=tema.PRIMARIO, stroke_width=2, dash_pattern=[6, 4],
            ))
            etiquetas.append((vaciado_x, deposito["vaciado"]))
        maximo_x = max(maximo_x, 1)

        for valor, color in ((deposito["umbral_aviso"], tema.AVISO), (deposito["umbral_critico"], tema.CRITICO)):
            series.insert(0, ft.LineChartData(
                data_points=[ft.LineChartDataPoint(0, valor, show_tooltip=False),
                             ft.LineChartDataPoint(maximo_x, valor, show_tooltip=False)],
                color=color, stroke_width=1.5, dash_pattern=[6, 4],
            ))

        grafica = ft.LineChart(
            data_series=series, min_x=0, max_x=maximo_x, min_y=0, max_y=100,
            left_axis=ft.ChartAxis(labels_size=40, show_labels=True),
            bottom_axis=ft.ChartAxis(
                labels=[ft.ChartAxisLabel(value=x, label=ft.Text(fecha_corta(fecha), size=11,
                                                                  color=tema.TEXTO_SUAVE))
                        for x, fecha in etiquetas],
                labels_size=28,
            ),
            horizontal_grid_lines=ft.ChartGridLines(color=tema.BORDE, width=0.5),
            tooltip_bgcolor=ft.Colors.with_opacity(0.9, tema.PANEL),
            interactive=True, height=300,
        )
        leyenda = ft.Row(
            [
                ft.Text("Lecturas desde el último rellenado", size=12, color=tema.PRIMARIO),
                ft.Text("- - Predicción", size=12, color=tema.PRIMARIO),
                ft.Text(f"Aviso {numero(deposito['umbral_aviso'])} %", size=12, color=tema.AVISO),
                ft.Text(f"Crítico {numero(deposito['umbral_critico'])} %", size=12, color=tema.CRITICO),
            ],
            spacing=14, wrap=True,
        )
        return ft.Container(
            bgcolor=tema.TARJETA, border=ft.border.all(1, tema.BORDE), border_radius=12, padding=20,
            content=ft.Column(
                # Margen a la derecha para que no se corte la fecha de la última etiqueta del eje.
                [titulo, leyenda, ft.Container(grafica, padding=ft.padding.only(right=44))],
                spacing=10, key="tecnico_grafica",
            ),
        )