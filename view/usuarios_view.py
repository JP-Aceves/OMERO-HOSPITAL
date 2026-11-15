"""Gestión de usuarios del administrador. Responsable: Medina (OME-57)."""
import flet as ft

from controller.usuarios_controller import UsuariosController
from model.usuario import Usuario
from view import tema


_ROLES = {
    "administrador": "Administrador",
    "jefe_sanidad": "Jefe de sanidad",
    "responsable_carpa": "Responsable de carpa",
    "tecnico_logistica": "Técnico de logística",
}


class UsuariosView:

    def __init__(self, usuario: Usuario, controlador: UsuariosController) -> None:
        self.usuario = usuario
        self.controlador = controlador

    def _cuentas_y_administrador(self):
        if self.usuario.ROL != "administrador":
            return (), None

        cuentas = self.controlador.listar()
        for cuenta in cuentas:
            if cuenta.usuario == self.usuario.usuario and cuenta.ROL == "administrador":
                return cuentas, cuenta
        return (), None

    def construir(self) -> ft.Control:
        """Devuelve el contenido; main.py lo mete dentro de ShellView."""
        mensaje = ft.Text(visible=False, color=tema.TEXTO)
        tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(titulo))
                for titulo in ("Nombre", "Usuario", "Rol", "Acciones")
            ],
            heading_text_style=ft.TextStyle(color=tema.TEXTO, weight=ft.FontWeight.BOLD),
            data_text_style=ft.TextStyle(color=tema.TEXTO),
            heading_row_color=tema.FONDO,
            bgcolor=tema.TARJETA,
            border=ft.border.all(1, tema.BORDE),
            border_radius=8,
            column_spacing=24,
            # Filas más altas que las 48 px por defecto para que el desplegable de rol
            # quepa dentro de su fila y no pise las líneas.
            data_row_min_height=68,
            data_row_max_height=68,
        )
        tabla_desplazable = ft.Row([tabla], scroll=ft.ScrollMode.AUTO)
        contenido = ft.Column(
            [
                ft.Text(
                    "Gestión de usuarios", size=26, color=tema.TEXTO,
                    font_family=tema.FUENTE_TITULOS, weight=ft.FontWeight.BOLD,
                ),
                # Sin ft.Semantics: envolver un texto oculto con Semantics hace que
                # Flet dibuje un recuadro gris en lugar de la pantalla.
                mensaje,
                tabla_desplazable,
            ],
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        def refrescar(error: str | None = None, exito: str | None = None) -> None:
            cuentas, administrador = self._cuentas_y_administrador()
            tabla.rows = [fila(cuenta) for cuenta in cuentas]
            tabla_desplazable.visible = administrador is not None
            if administrador is None:
                error = "Solo un administrador puede gestionar usuarios."

            mensaje.value = error or exito or ""
            mensaje.color = tema.CRITICO if error else tema.NORMAL
            mensaje.visible = bool(mensaje.value)
            if contenido.page is not None:
                contenido.update()

        def cambiar_rol(nombre_usuario: str, evento: ft.ControlEvent) -> None:
            _, administrador = self._cuentas_y_administrador()
            if administrador is None:
                refrescar()
                return

            rol = evento.control.value
            if rol not in _ROLES:
                refrescar(error="Selecciona un rol válido.")
                return

            error = self.controlador.cambiar_rol(nombre_usuario, rol)
            refrescar(error=error, exito="Rol actualizado.")

        def solicitar_eliminacion(nombre_usuario: str, evento: ft.ControlEvent) -> None:
            _, administrador = self._cuentas_y_administrador()
            if administrador is None:
                refrescar()
                return
            if nombre_usuario == administrador.usuario:
                refrescar(error="No puedes eliminar tu propia cuenta.")
                return

            pagina = evento.page

            async def confirmar(_evento: ft.ControlEvent) -> None:
                pagina.close(dialogo)
                _, administrador_actual = self._cuentas_y_administrador()
                if administrador_actual is None:
                    refrescar()
                    return

                error = self.controlador.eliminar(nombre_usuario, administrador_actual)
                refrescar(error=error, exito="Usuario eliminado.")

            dialogo = ft.AlertDialog(
                modal=True,
                title=ft.Text(
                    "Eliminar usuario", color=tema.TEXTO,
                    font_family=tema.FUENTE_TITULOS,
                ),
                content=ft.Text(f"¿Quieres eliminar la cuenta «{nombre_usuario}»?"),
                actions=[
                    ft.TextButton(
                        "Cancelar", autofocus=True,
                        style=ft.ButtonStyle(color=tema.PRIMARIO),
                        on_click=lambda _: pagina.close(dialogo),
                    ),
                    ft.ElevatedButton(
                        "Eliminar", on_click=confirmar,
                        style=ft.ButtonStyle(bgcolor=tema.CRITICO, color=tema.TARJETA),
                    ),
                ],
            )
            pagina.open(dialogo)

        def fila(cuenta: Usuario) -> ft.DataRow:
            nombre_usuario = cuenta.usuario
            es_propia = nombre_usuario == self.usuario.usuario

            # Flet despacha los callbacks síncronos en hilos. Estos se ejecutan
            # en el mismo bucle, sin ceder entre verificar permisos y actuar.
            async def al_cambiar_rol(evento: ft.ControlEvent) -> None:
                cambiar_rol(nombre_usuario, evento)

            async def al_solicitar_eliminacion(evento: ft.ControlEvent) -> None:
                solicitar_eliminacion(nombre_usuario, evento)

            rol = ft.Dropdown(
                # Sin label: la cabecera de la columna ya dice "Rol" y el label flotante
                # se salía de la fila. tooltip mantiene a quién pertenece el desplegable.
                tooltip=f"Rol de {nombre_usuario}",
                value=cuenta.ROL,
                options=[ft.dropdown.Option(clave, titulo) for clave, titulo in _ROLES.items()],
                width=260,
                color=tema.TEXTO,
                border_color=tema.BORDE,
                focused_border_color=tema.PRIMARIO,
                on_change=al_cambiar_rol,
            )
            eliminar = ft.OutlinedButton(
                "Eliminar",
                disabled=es_propia,
                tooltip=(
                    "No puedes eliminar tu propia cuenta" if es_propia
                    else f"Eliminar la cuenta de {nombre_usuario}"
                ),
                style=ft.ButtonStyle(color=tema.CRITICO),
                on_click=al_solicitar_eliminacion,
            )
            return ft.DataRow(cells=[
                ft.DataCell(ft.Text(cuenta.nombre)),
                ft.DataCell(ft.Text(nombre_usuario)),
                ft.DataCell(rol),
                ft.DataCell(eliminar),
            ])

        refrescar()
        return contenido
