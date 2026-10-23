"""Punto de entrada de OMERO · Monitor de hospital de campaña."""
import flet as ft


def main(page: ft.Page) -> None:
    page.title = "OMERO"
    page.window.width = 1000
    page.window.height = 650
    page.add(
        ft.Text("OMERO", size=32, weight=ft.FontWeight.BOLD),
        ft.Text("Monitor de hospital de campaña"),
    )


if __name__ == "__main__":
    ft.app(target=main)
