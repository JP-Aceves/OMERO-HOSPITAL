"""Punto de entrada de OMERO · Monitor de hospital de campaña."""
import flet as ft

from controller.login_controller import LoginController
from controller.registro_controller import RegistroController
from persistence.repositorio_json import RepositorioJSON
from view.login_view import LoginView
from view.registro_view import RegistroView


def main(page: ft.Page) -> None:
    page.title = "OMERO"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1000
    page.window.height = 650

    repositorio = RepositorioJSON()
    login = LoginController(repositorio)
    registro = RegistroController(repositorio)
    sesion = {"usuario": None}

    def al_entrar(usuario, contrasena):
        encontrado = login.login(usuario, contrasena)
        if encontrado is None:
            return "Usuario o contraseña incorrectos"
        sesion["usuario"] = encontrado
        page.go("/inicio")
        return None

    def al_registrar(nombre, usuario, contrasena, repetir, rol):
        error = registro.registrar(nombre, usuario, contrasena, repetir, rol)
        if error is None:
            page.go("/login")
        return error

    def cerrar_sesion(_):
        sesion["usuario"] = None
        page.go("/login")

    def vista_inicio():
        usuario = sesion["usuario"]
        return ft.View("/inicio", [
            ft.Text(f"Hola, {usuario.nombre}", size=28, weight=ft.FontWeight.BOLD),
            ft.Text(f"Rol: {usuario.ROL}"),
            ft.TextButton("Cerrar sesión", on_click=cerrar_sesion),
        ])

    def ruta_cambiada(_):
        page.views.clear()
        if page.route == "/registro":
            page.views.append(RegistroView(al_registrar, lambda: page.go("/login")).construir())
        elif page.route == "/inicio" and sesion["usuario"] is not None:
            page.views.append(vista_inicio())
        else:
            page.views.append(LoginView(al_entrar, lambda: page.go("/registro")).construir())
        page.update()

    page.on_route_change = ruta_cambiada
    page.go("/login")


if __name__ == "__main__":
    ft.app(target=main)