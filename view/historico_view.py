"""Pantalla "Histórico y estadísticas" (mockup 07). Responsable: JP (OME-70).

Filtro por zona, sensor y fechas; tarjetas con media, máximo, mínimo y número de
lecturas; gráfica de la evolución con las líneas de aviso y crítico, y tabla con
las últimas lecturas. La vista no toca el modelo: todo llega del controlador.
"""
from datetime import datetime

import flet as ft

from controller.historico_controller import HistoricoController
from model.usuario import Usuario
from service.estado import AVISO, CRITICO, NORMAL
from view import tema

ULTIMAS_LECTURAS = 8
ETIQUETAS_EJE_X = 5
COLOR_ESTADO = {NORMAL: tema.NORMAL, AVISO: tema.AVISO, CRITICO: tema.CRITICO}
NOMBRE_ESTADO = {NORMAL: "Normal", AVISO: "Aviso", CRITICO: "Crítico"}


def numero(valor: float) -> str:
    """31.4 -> "31,4" (coma decimal, como en el resto de la app)."""
    return f"{valor:.1f}".replace(".", ",")


def fecha_corta(fecha_hora: str) -> str:
    """"2026-11-23T18:30:00" -> "23/11 18:30"."""
    return datetime.fromisoformat(fecha_hora).strftime("%d/%m %H:%M")


def tarjeta(contenido: ft.Control, col: dict) -> ft.Container:
    return ft.Container(
        content=contenido, col=col, padding=18, bgcolor=tema.TARJETA, border_radius=12,
        border=ft.border.all(1, tema.BORDE),
    )


class HistoricoView:

    def __init__(self, usuario: Usuario, controlador: HistoricoController) -> None:
        self.usuario = usuario
        self.controlador = controlador

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        zonas = self.controlador.zonas(self.usuario)
        self.campo_zona = ft.Dropdown(
            label="Zona", key="historico_zona", border_color=tema.BORDE, expand=True,
            options=[ft.dropdown.Option(zona["id"], zona["nombre"]) for zona in zonas],
            value=zonas[0]["id"] if zonas else None, on_change=self._al_cambiar_zona,
        )
        self.campo_sensor = ft.Dropdown(label="Sensor", key="historico_sensor",
                                        border_color=tema.BORDE, expand=True)
        self.campo_desde = tema.campo_texto("Desde", key="historico_desde", hint_text="dd/mm/aaaa hh:mm",
                                            on_submit=self._aplicar)
        self.campo_hasta = tema.campo_texto("Hasta", key="historico_hasta", hint_text="dd/mm/aaaa hh:mm",
                                            on_submit=self._aplicar)
        self.error = ft.Text(visible=False, color=tema.CRITICO, size=14, key="historico_error")
        self.resultado = ft.Column(spacing=16)
        self._cargar_sensores()

        filtro = tarjeta(
            ft.Column([
                ft.ResponsiveRow(
                    [
                        ft.Container(self.campo_zona, col={"xs": 12, "md": 6, "xl": 3}),
                        ft.Container(self.campo_sensor, col={"xs": 12, "md": 6, "xl": 3}),
                        ft.Container(self.campo_desde, col={"xs": 12, "md": 4, "xl": 2}),
                        ft.Container(self.campo_hasta, col={"xs": 12, "md": 4, "xl": 2}),
                        ft.Container(
                            tema.boton_primario("Aplicar filtro", self._aplicar, key="historico_aplicar"),
                            col={"xs": 12, "md": 4, "xl": 2}, alignment=ft.alignment.center_left,
                        ),
                    ],
                    spacing=12, run_spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text("Deja las fechas vacías para ver todas las lecturas.", size=12,
                        color=tema.TEXTO_SUAVE),
                self.error,
            ], spacing=8),
            col={"xs": 12},
        )

        subtitulo = ("Consulta las lecturas pasadas de todas las zonas"
                     if self.usuario.ROL == "jefe_sanidad"
                     else "Consulta las lecturas pasadas de las zonas que tienes asignadas")
        self.contenido = ft.Column(
            [
                ft.Text("Histórico y estadísticas", size=30, color=tema.TEXTO, weight=ft.FontWeight.BOLD,
                        font_family=tema.FUENTE_TITULOS),
                ft.Text(subtitulo, size=15, color=tema.TEXTO_SUAVE),
                ft.ResponsiveRow([filtro]),
                self.resultado,
            ],
            spacing=14, scroll=ft.ScrollMode.AUTO, expand=True,
        )
        if not zonas:
            self.resultado.controls = [ft.Text("Todavía no tienes zonas asignadas.", color=tema.TEXTO_SUAVE)]
        else:
            self._mostrar()
        return self.contenido

    # ---------- eventos ----------

    def _al_cambiar_zona(self, _evento=None) -> None:
        self._cargar_sensores()
        self._mostrar()
        self._refrescar()

    def _aplicar(self, _evento=None) -> None:
        self._mostrar()
        self._refrescar()

    # ---------- lógica de pantalla ----------

    def _cargar_sensores(self) -> None:
        sensores = self.controlador.sensores(self.usuario, self.campo_zona.value) if self.campo_zona.value else []
        self.campo_sensor.options = [ft.dropdown.Option(s["id"], s["nombre"]) for s in sensores]
        self.campo_sensor.value = sensores[0]["id"] if sensores else None

    def _mostrar(self) -> None:
        datos = self.controlador.consultar(self.usuario, self.campo_zona.value, self.campo_sensor.value,
                                           self.campo_desde.value, self.campo_hasta.value)
        if isinstance(datos, str):
            self.error.value = datos
            self.error.visible = True
            return
        self.error.visible = False
        if datos["total"] == 0:
            self.resultado.controls = [ft.Text("No hay lecturas de ese sensor en el periodo elegido.",
                                               color=tema.TEXTO_SUAVE, key="historico_vacio")]
            return
        self.resultado.controls = [self._tarjetas(datos), self._cuerpo(datos)]

    def _refrescar(self) -> None:
        if getattr(self, "contenido", None) is not None and self.contenido.page is not None:
            self.contenido.update()

    # ---------- piezas ----------

    def _tarjetas(self, datos: dict) -> ft.ResponsiveRow:
        unidad = datos["unidad"]

        def cifra(titulo: str, valor: str, detalle: str, clave: str) -> ft.Container:
            return tarjeta(
                ft.Column([
                    ft.Text(titulo, size=14, color=tema.TEXTO_SUAVE),
                    ft.Text(valor, size=28, color=tema.TEXTO, weight=ft.FontWeight.BOLD,
                            font_family=tema.FUENTE_TITULOS, key=clave),
                    ft.Text(detalle, size=13, color=tema.TEXTO_SUAVE),
                ], spacing=4),
                col={"xs": 6, "lg": 3},
            )

        maximo, minimo = datos["maximo"], datos["minimo"]
        return ft.ResponsiveRow([
            cifra("Media", f"{numero(datos['media'])} {unidad}", "periodo filtrado", "historico_media"),
            cifra("Máximo", f"{numero(maximo['valor'])} {unidad}", fecha_corta(maximo["fecha_hora"]),
                  "historico_maximo"),
            cifra("Mínimo", f"{numero(minimo['valor'])} {unidad}", fecha_corta(minimo["fecha_hora"]),
                  "historico_minimo"),
            cifra("Lecturas", str(datos["total"]), "en el periodo", "historico_total"),
        ], spacing=14, run_spacing=14)

    def _cuerpo(self, datos: dict) -> ft.ResponsiveRow:
        return ft.ResponsiveRow([
            tarjeta(self._grafica(datos), col={"xs": 12, "xl": 8}),
            tarjeta(self._ultimas(datos), col={"xs": 12, "xl": 4}),
        ], spacing=14, run_spacing=14)

    def _grafica(self, datos: dict) -> ft.Control:
        puntos = datos["grafica"]
        unidad = datos["unidad"]
        valores = [p["valor"] for p in puntos] + [datos["umbral_aviso"], datos["umbral_critico"]]
        margen = max(1.0, (max(valores) - min(valores)) * 0.1)
        ultimo = len(puntos) - 1

        serie = ft.LineChartData(
            data_points=[
                ft.LineChartDataPoint(i, p["valor"], tooltip=f"{fecha_corta(p['fecha_hora'])}\n"
                                                             f"{numero(p['valor'])} {unidad}")
                for i, p in enumerate(puntos)
            ],
            color=tema.PRIMARIO, stroke_width=2.5, curved=False,
            below_line_bgcolor=ft.Colors.with_opacity(0.08, tema.PRIMARIO),
        )

        def linea_umbral(valor: float, color: str) -> ft.LineChartData:
            return ft.LineChartData(
                data_points=[ft.LineChartDataPoint(0, valor, show_tooltip=False),
                             ft.LineChartDataPoint(max(ultimo, 1), valor, show_tooltip=False)],
                color=color, stroke_width=1.5, dash_pattern=[6, 4],
            )

        etiquetas = []
        if ultimo > 0:
            pasos = min(ETIQUETAS_EJE_X - 1, ultimo)
            posiciones = sorted({round(ultimo * k / pasos) for k in range(pasos + 1)})
            etiquetas = [
                ft.ChartAxisLabel(value=pos, label=ft.Text(fecha_corta(puntos[pos]["fecha_hora"]), size=11,
                                                           color=tema.TEXTO_SUAVE))
                for pos in posiciones
            ]

        grafica = ft.LineChart(
            data_series=[linea_umbral(datos["umbral_critico"], tema.CRITICO),
                         linea_umbral(datos["umbral_aviso"], tema.AVISO), serie],
            min_x=0, max_x=max(ultimo, 1),
            min_y=min(valores) - margen, max_y=max(valores) + margen,
            left_axis=ft.ChartAxis(labels_size=44, show_labels=True),
            bottom_axis=ft.ChartAxis(labels=etiquetas, labels_size=28),
            horizontal_grid_lines=ft.ChartGridLines(color=tema.BORDE, width=0.5),
            tooltip_bgcolor=ft.Colors.with_opacity(0.9, tema.PANEL),
            interactive=True, height=320,
        )
        self.grafica = grafica
        leyenda = ft.Row([
            ft.Text(f"Aviso {numero(datos['umbral_aviso'])} {unidad}", size=12, color=tema.AVISO),
            ft.Text(f"Crítico {numero(datos['umbral_critico'])} {unidad}", size=12, color=tema.CRITICO),
            ft.Text("(malo si baja)" if datos["inverso"] else "(malo si sube)", size=12, color=tema.TEXTO_SUAVE),
        ], spacing=14, wrap=True)
        return ft.Column([
            ft.Text(f"{datos['sensor']} · {datos['zona']}", size=15, color=tema.TEXTO, weight=ft.FontWeight.W_600),
            leyenda,
            grafica,
        ], spacing=10)

    def _ultimas(self, datos: dict) -> ft.Control:
        filas = []
        for lectura in reversed(datos["lecturas"][-ULTIMAS_LECTURAS:]):
            filas.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(fecha_corta(lectura["fecha_hora"]), size=13, color=tema.TEXTO)),
                ft.DataCell(ft.Text(f"{numero(lectura['valor'])} {datos['unidad']}", size=13, color=tema.TEXTO,
                                    weight=ft.FontWeight.W_600)),
                ft.DataCell(tema.etiqueta_estado(lectura["estado"], NOMBRE_ESTADO[lectura["estado"]])),
            ]))
        tabla = ft.DataTable(
            columns=[ft.DataColumn(ft.Text("Fecha y hora", size=13, color=tema.TEXTO_SUAVE)),
                     ft.DataColumn(ft.Text("Valor", size=13, color=tema.TEXTO_SUAVE)),
                     ft.DataColumn(ft.Text("Nivel", size=13, color=tema.TEXTO_SUAVE))],
            rows=filas, column_spacing=18, horizontal_margin=4, data_row_min_height=44,
        )
        self.tabla = tabla
        return ft.Column([
            ft.Text("Últimas lecturas", size=15, color=tema.TEXTO, weight=ft.FontWeight.W_600),
            tabla,
        ], spacing=8)
