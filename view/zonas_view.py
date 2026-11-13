"""Pantalla "Zonas y sensores" del jefe de sanidad (mockup 06). Responsable: JP (OME-35).

    ┌ Zonas y sensores ─────────────────── [+ Añadir sensor] [+ Nueva zona] ┐
    │ tarjetas de zonas  │ detalle de la zona elegida                       │
    │ (clic = elegirla)  │   nombre · tipo · responsable                    │
    │                    │   tabla de sensores (editar / eliminar)          │
    │                    │   tabla de actuadores (eliminar) + añadir        │
    │                    │   [Eliminar zona]            [Guardar cambios]   │
    └────────────────────┴──────────────────────────────────────────────────┘

MVC: esta vista no lee JSON ni valida nada. Todo se lo pide al ZonasController
(OME-32, de Rodas), que devuelve None si va bien o el texto del error, y la
vista solo enseña ese texto.
"""
import flet as ft

from controller.zonas_controller import ZonasController
from model.usuario import Usuario
from view import tema

NOMBRE_TIPO_ZONA = {"carpa": "Carpa", "zona_tecnica": "Zona técnica", "exterior": "Exterior"}
NOMBRE_TIPO_SENSOR = {
    "temperatura": "Temperatura",
    "humedad": "Humedad",
    "calidad_aire": "Calidad del aire",
    "luz": "Luz",
    "humo_gas": "Humo / gas",
    "nivel_deposito": "Nivel del depósito",
    "viento": "Viento",
}
NOMBRE_TIPO_ACTUADOR = {
    "ventilador": "Ventilador",
    "led_semaforo": "LED semáforo",
    "led_evacuacion": "LED de evacuación",
}
NOMBRE_ROL = {"responsable_carpa": "carpa", "tecnico_logistica": "logística"}
SIN_RESPONSABLE = "__sin_responsable__"


def resumen_zona(zona) -> str:
    """'4 sensores · 2 actuadores' (lo usan las tarjetas)."""
    return f"{len(zona.sensores)} sensores · {len(zona.actuadores)} actuadores"


def opciones(nombres: dict) -> list:
    """De {"carpa": "Carpa", ...} a las opciones de un desplegable."""
    return [ft.dropdown.Option(clave, texto) for clave, texto in nombres.items()]


class ZonasView:

    def __init__(self, usuario: Usuario, controlador: ZonasController) -> None:
        self.usuario = usuario
        self.controlador = controlador
        self.id_seleccionada: str | None = None
        self.dialogo: ft.AlertDialog | None = None   # el formulario abierto (también lo miran los tests)
        self.raiz: ft.Column | None = None
        # Controles que se rellenan en cada _refrescar()
        self.subtitulo = ft.Text("", color=tema.TEXTO_SUAVE)
        self.mensaje = ft.Text("", key="zonas_mensaje", visible=False, size=14)
        self.lista_zonas = ft.Column(spacing=12)
        self.detalle = ft.Column(spacing=18)
        self.boton_sensor = None
        self.campo_nombre = self.campo_tipo = self.campo_responsable = None

    # ================= construir y refrescar =================

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        self.boton_sensor = tema.boton_secundario("+ Añadir sensor", self._formulario_sensor, key="zonas_anadir_sensor")
        cabecera = ft.ResponsiveRow(
            [
                ft.Column(
                    [
                        ft.Text("Zonas y sensores", size=30, weight=ft.FontWeight.BOLD,
                                color=tema.TEXTO, font_family=tema.FUENTE_TITULOS),
                        self.subtitulo,
                    ],
                    spacing=4, col={"xs": 12, "md": 7},
                ),
                ft.Row(
                    [self.boton_sensor,
                     tema.boton_primario("+ Nueva zona", self._formulario_zona_nueva, key="zonas_nueva")],
                    alignment=ft.MainAxisAlignment.END, wrap=True, col={"xs": 12, "md": 5},
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        cuerpo = ft.ResponsiveRow(
            [
                ft.Container(self.lista_zonas, col={"xs": 12, "lg": 4}),
                ft.Container(self.detalle, col={"xs": 12, "lg": 8}, bgcolor=tema.TARJETA,
                             border=ft.border.all(1, tema.BORDE), border_radius=16, padding=24),
            ],
            spacing=24, run_spacing=24, vertical_alignment=ft.CrossAxisAlignment.START,
        )
        self.raiz = ft.Column([cabecera, self.mensaje, cuerpo], spacing=20)
        self._refrescar()
        return self.raiz

    def _refrescar(self) -> None:
        """Vuelve a pedir las zonas al controlador y repinta tarjetas y detalle."""
        zonas = self.controlador.listar(self.usuario)
        self.responsables = self.controlador.responsables_disponibles()

        if self._buscar(zonas, self.id_seleccionada) is None:
            primera = next(iter(zonas), None)          # si la elegida ya no existe, la primera
            self.id_seleccionada = primera.id if primera else None

        sensores = sum(len(zona.sensores) for zona in zonas)
        actuadores = sum(len(zona.actuadores) for zona in zonas)
        self.subtitulo.value = (f"{len(zonas)} zonas · {sensores} sensores · {actuadores} actuadores"
                                " · los cambios se guardan en JSON")

        self.lista_zonas.controls = [self._tarjeta(zona) for zona in zonas] or [
            ft.Text("Todavía no hay zonas. Crea la primera con «+ Nueva zona».", color=tema.TEXTO_SUAVE)]

        zona = self._buscar(zonas, self.id_seleccionada)
        self.detalle.controls = self._detalle(zona) if zona else [
            ft.Text("Elige una zona o crea una nueva.", color=tema.TEXTO_SUAVE)]
        self.boton_sensor.disabled = zona is None
        self._pintar()

    def _pintar(self) -> None:
        """update() solo funciona cuando la vista ya está en la ventana."""
        if self.raiz is not None and self.raiz.page is not None:
            self.raiz.update()

    @staticmethod
    def _buscar(zonas, id_zona):
        for zona in zonas:
            if zona.id == id_zona:
                return zona
        return None

    def _mostrar(self, texto: str, error: bool = False) -> None:
        self.mensaje.value = texto
        self.mensaje.color = tema.CRITICO if error else tema.NORMAL
        self.mensaje.visible = bool(texto)

    def _resultado(self, error: str | None, exito: str) -> None:
        """Enseña el error del controlador o el mensaje de éxito y repinta."""
        self._mostrar(error or exito, error=error is not None)
        self._refrescar()

    def _nombre_de(self, usuario: str | None) -> str:
        for persona in self.responsables:
            if persona.usuario == usuario:
                return persona.nombre
        return usuario or "sin asignar"

    # ================= columna izquierda: tarjetas =================

    def _tarjeta(self, zona) -> ft.Control:
        elegida = zona.id == self.id_seleccionada
        return ft.Container(
            key=f"zona_{zona.id}",
            content=ft.Column(
                [
                    ft.Text(zona.nombre, size=17, weight=ft.FontWeight.BOLD, color=tema.TEXTO),
                    ft.Text(resumen_zona(zona), size=13, color=tema.TEXTO_SUAVE),
                    ft.Text(f"Responsable: {self._nombre_de(zona.responsable)}", size=13, color=tema.TEXTO),
                ],
                spacing=4,
            ),
            bgcolor=ft.Colors.with_opacity(0.06, tema.PRIMARIO) if elegida else tema.TARJETA,
            border=ft.border.all(2 if elegida else 1, tema.PRIMARIO if elegida else tema.BORDE),
            border_radius=14,
            padding=18,
            # i=zona.id: guarda el id de ESTA tarjeta (igual que r=ruta en el panel lateral)
            on_click=lambda _evento, i=zona.id: self._seleccionar(i),
        )

    def _seleccionar(self, id_zona: str) -> None:
        self.id_seleccionada = id_zona
        self._mostrar("")
        self._refrescar()

    # ================= columna derecha: detalle =================

    def _detalle(self, zona) -> list:
        self.campo_nombre = tema.campo_texto("Nombre", value=zona.nombre, key="zonas_nombre",
                                             on_submit=self._guardar_zona)
        self.campo_tipo = ft.Dropdown(label="Tipo de zona", value=zona.tipo, key="zonas_tipo",
                                      options=opciones(NOMBRE_TIPO_ZONA), border_color=tema.BORDE)
        self.campo_responsable = ft.Dropdown(
            label="Responsable asignado", key="zonas_responsable",
            value=zona.responsable or SIN_RESPONSABLE, options=self._opciones_responsable(),
            border_color=tema.BORDE)

        eliminar_zona = ft.OutlinedButton(
            "Eliminar zona", key="zonas_eliminar", on_click=self._confirmar_eliminar_zona,
            style=ft.ButtonStyle(color=tema.CRITICO, side=ft.BorderSide(1, tema.CRITICO),
                                 shape=ft.RoundedRectangleBorder(radius=8)))
        return [
            ft.Text(zona.nombre, size=22, weight=ft.FontWeight.BOLD, color=tema.TEXTO),
            ft.ResponsiveRow(
                [
                    ft.Container(self.campo_nombre, col={"xs": 12, "md": 4}),
                    ft.Container(self.campo_tipo, col={"xs": 12, "md": 4}),
                    ft.Container(self.campo_responsable, col={"xs": 12, "md": 4}),
                ],
                spacing=12, run_spacing=12,
            ),
            ft.Text("Sensores y umbrales", size=16, weight=ft.FontWeight.BOLD, color=tema.TEXTO),
            self._tabla_sensores(zona),
            ft.Row(
                [ft.Text("Actuadores", size=16, weight=ft.FontWeight.BOLD, color=tema.TEXTO),
                 tema.boton_secundario("+ Añadir actuador", self._formulario_actuador, key="zonas_anadir_actuador")],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            self._tabla_actuadores(zona),
            ft.Row(
                [eliminar_zona, tema.boton_primario("Guardar cambios", self._guardar_zona, key="zonas_guardar")],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True,
            ),
        ]

    def _opciones_responsable(self) -> list:
        lista = [ft.dropdown.Option(SIN_RESPONSABLE, "Sin asignar")]
        for persona in self.responsables:
            rol = NOMBRE_ROL.get(persona.ROL, persona.ROL)
            lista.append(ft.dropdown.Option(persona.usuario, f"{persona.nombre} ({rol})"))
        return lista

    def _tabla_sensores(self, zona) -> ft.Control:
        filas = []
        for sensor in zona.sensores:
            filas.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(sensor.nombre)),
                ft.DataCell(ft.Text(NOMBRE_TIPO_SENSOR.get(sensor.TIPO, sensor.TIPO))),
                ft.DataCell(ft.Text(f"{sensor.umbral_aviso} {sensor.UNIDAD}")),
                ft.DataCell(ft.Text(f"{sensor.umbral_critico} {sensor.UNIDAD}")),
                ft.DataCell(ft.Row(
                    [
                        ft.TextButton("Editar", key=f"editar_{sensor.id}",
                                      on_click=lambda _evento, s=sensor: self._formulario_sensor(sensor=s)),
                        ft.TextButton("Eliminar", key=f"eliminar_{sensor.id}",
                                      style=ft.ButtonStyle(color=tema.CRITICO),
                                      on_click=lambda _evento, i=sensor.id: self._eliminar_sensor(i)),
                    ],
                    spacing=0,
                )),
            ]))
        if not filas:
            return ft.Text("Esta zona todavía no tiene sensores.", color=tema.TEXTO_SUAVE)
        tabla = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(titulo)) for titulo in ("Sensor", "Mide", "Aviso", "Crítico", "")],
            rows=filas, column_spacing=20,
            heading_text_style=ft.TextStyle(color=tema.TEXTO_SUAVE, weight=ft.FontWeight.BOLD),
        )
        return ft.Row([tabla], scroll=ft.ScrollMode.AUTO)   # scroll lateral con la ventana estrecha

    def _tabla_actuadores(self, zona) -> ft.Control:
        filas = []
        for actuador in zona.actuadores:
            filas.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(actuador.nombre)),
                ft.DataCell(ft.Text(NOMBRE_TIPO_ACTUADOR.get(actuador.tipo, actuador.tipo))),
                ft.DataCell(ft.Text("Encendido" if actuador.encendido else "Apagado")),
                ft.DataCell(ft.TextButton(
                    "Eliminar", key=f"eliminar_{actuador.id}", style=ft.ButtonStyle(color=tema.CRITICO),
                    on_click=lambda _evento, i=actuador.id: self._eliminar_actuador(i))),
            ]))
        if not filas:
            return ft.Text("Esta zona todavía no tiene actuadores.", color=tema.TEXTO_SUAVE)
        tabla = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(titulo)) for titulo in ("Actuador", "Tipo", "Estado", "")],
            rows=filas, column_spacing=20,
            heading_text_style=ft.TextStyle(color=tema.TEXTO_SUAVE, weight=ft.FontWeight.BOLD),
        )
        return ft.Row([tabla], scroll=ft.ScrollMode.AUTO)

    # ================= acciones directas =================

    def _guardar_zona(self, _evento=None) -> None:
        """Guarda nombre y tipo, y cambia el responsable si se ha tocado (HU-04)."""
        zona = self._buscar(self.controlador.listar(self.usuario), self.id_seleccionada)
        if zona is None:
            return
        nombre = self.campo_nombre.value or ""
        tipo = self.campo_tipo.value or ""
        nuevo = self.campo_responsable.value
        nuevo = None if nuevo in (None, SIN_RESPONSABLE) else nuevo

        error = self.controlador.editar_zona(zona.id, nombre, tipo, zona.responsable)
        if error is None and nuevo != zona.responsable:
            if nuevo is None:
                error = self.controlador.editar_zona(zona.id, nombre, tipo, None)
            else:
                error = self.controlador.asignar_responsable(zona.id, nuevo)
        self._resultado(error, "Cambios guardados.")

    def _eliminar_sensor(self, id_sensor: str) -> None:
        error = self.controlador.eliminar_sensor(self.id_seleccionada, id_sensor)
        self._resultado(error, "Sensor eliminado.")

    def _eliminar_actuador(self, id_actuador: str) -> None:
        error = self.controlador.eliminar_actuador(self.id_seleccionada, id_actuador)
        self._resultado(error, "Actuador eliminado.")

    # ================= formularios (diálogos) =================

    def _abrir(self, dialogo: ft.AlertDialog) -> None:
        self.dialogo = dialogo
        if self.raiz is not None and self.raiz.page is not None:
            self.raiz.page.open(dialogo)

    def _cerrar(self) -> None:
        if self.dialogo is not None and self.raiz is not None and self.raiz.page is not None:
            self.raiz.page.close(self.dialogo)
        self.dialogo = None

    def _formulario(self, titulo: str, campos: list, al_guardar, exito: str, nota: str | None = None,
                    texto_boton: str = "Guardar") -> None:
        """Diálogo genérico: al_guardar() devuelve None si va bien o el error del controlador.

        Si hay error, se enseña dentro del diálogo y se queda abierto. Enter en cualquier
        campo de texto equivale a pulsar Guardar.
        """
        aviso_error = ft.Text("", key="dialogo_error", color=tema.CRITICO, size=13, visible=False)

        def guardar(_evento=None):
            error = al_guardar()
            if error:
                aviso_error.value = error
                aviso_error.visible = True
                if aviso_error.page is not None:
                    aviso_error.update()
                return
            self._cerrar()
            self._resultado(None, exito)

        for campo in campos:
            if isinstance(campo, ft.TextField):
                campo.on_submit = guardar
        contenido = list(campos)
        if nota:
            contenido.append(ft.Text(nota, size=12, color=tema.TEXTO_SUAVE))
        contenido.append(aviso_error)
        self._abrir(ft.AlertDialog(
            modal=True,
            title=ft.Text(titulo, color=tema.TEXTO, font_family=tema.FUENTE_TITULOS),
            content=ft.Column(contenido, tight=True, spacing=12, width=420),
            actions=[
                ft.TextButton("Cancelar", key="dialogo_cancelar", on_click=lambda _evento: self._cerrar()),
                tema.boton_primario(texto_boton, guardar, key="dialogo_guardar"),
            ],
        ))

    def _formulario_zona_nueva(self, _evento=None) -> None:
        nombre = tema.campo_texto("Nombre", key="nueva_zona_nombre", autofocus=True)
        tipo = ft.Dropdown(label="Tipo de zona", key="nueva_zona_tipo", value="carpa",
                           options=opciones(NOMBRE_TIPO_ZONA))
        responsable = ft.Dropdown(label="Responsable", key="nueva_zona_responsable",
                                  value=SIN_RESPONSABLE, options=self._opciones_responsable())

        def crear():
            antes = {zona.id for zona in self.controlador.listar(self.usuario)}
            elegido = None if responsable.value in (None, SIN_RESPONSABLE) else responsable.value
            error = self.controlador.crear_zona(nombre.value or "", tipo.value or "", elegido)
            if error is None:   # selecciona la zona recién creada
                for zona in self.controlador.listar(self.usuario):
                    if zona.id not in antes:
                        self.id_seleccionada = zona.id
            return error

        self._formulario("Nueva zona", [nombre, tipo, responsable], crear, "Zona creada.", texto_boton="Crear")

    def _formulario_sensor(self, _evento=None, sensor=None) -> None:
        """Sin sensor: alta. Con sensor: edición (el tipo no se puede cambiar)."""
        id_zona = self.id_seleccionada
        if id_zona is None:
            return
        editando = sensor is not None
        nombre = tema.campo_texto("Nombre", key="sensor_nombre", autofocus=True,
                                  value=sensor.nombre if editando else "")
        tipo = ft.Dropdown(label="Qué mide", key="sensor_tipo", options=opciones(NOMBRE_TIPO_SENSOR),
                           value=sensor.TIPO if editando else "temperatura", disabled=editando)
        aviso = tema.campo_texto("Umbral de aviso", key="sensor_aviso",
                                 value=str(sensor.umbral_aviso) if editando else "")
        critico = tema.campo_texto("Umbral crítico", key="sensor_critico",
                                   value=str(sensor.umbral_critico) if editando else "")

        def guardar():
            if editando:
                return self.controlador.editar_sensor(id_zona, sensor.id, nombre.value or "",
                                                      aviso.value or "", critico.value or "")
            return self.controlador.anadir_sensor(id_zona, nombre.value or "", tipo.value or "",
                                                  aviso.value or "", critico.value or "")

        self._formulario(
            "Editar sensor" if editando else "Añadir sensor",
            [nombre, tipo, aviso, critico], guardar,
            "Sensor actualizado." if editando else "Sensor añadido.",
            nota="Umbrales según la tabla del README. En luz y depósito el aviso es mayor que el crítico (son malos si bajan).",
        )

    def _formulario_actuador(self, _evento=None) -> None:
        id_zona = self.id_seleccionada
        if id_zona is None:
            return
        nombre = tema.campo_texto("Nombre", key="actuador_nombre", autofocus=True)
        tipo = ft.Dropdown(label="Tipo", key="actuador_tipo", value="ventilador",
                           options=opciones(NOMBRE_TIPO_ACTUADOR))

        def guardar():
            return self.controlador.anadir_actuador(id_zona, nombre.value or "", tipo.value or "")

        self._formulario("Añadir actuador", [nombre, tipo], guardar, "Actuador añadido.")

    def _confirmar_eliminar_zona(self, _evento=None) -> None:
        id_zona = self.id_seleccionada
        if id_zona is None:
            return

        def eliminar():
            error = self.controlador.eliminar_zona(id_zona)
            if error is None:
                self.id_seleccionada = None
            return error

        self._formulario(
            "Eliminar zona", [ft.Text("Se borrará la zona con todos sus sensores y actuadores. ¿Seguro?")],
            eliminar, "Zona eliminada.", texto_boton="Eliminar",
        )
