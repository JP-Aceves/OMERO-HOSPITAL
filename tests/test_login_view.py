from view.login_view import LoginView
from view.tema import FUENTE_TITULOS, registrar_fuentes


def _campos_formulario(vista):
    def recorrer(controles):
        for control in controles:
            yield control
            yield from recorrer(getattr(control, "controls", None) or [])
            contenido = getattr(control, "content", None)
            if contenido is not None:
                yield from recorrer([contenido])

    return {
        control.key: control
        for control in recorrer(vista.controls)
        if getattr(control, "key", None)
    }


def test_enter_en_usuario_enfoca_contrasena_y_enter_en_contrasena_inicia_login():
    llamadas = []
    vista = LoginView(lambda usuario, clave: llamadas.append((usuario, clave)), lambda: None).construir()
    controles = _campos_formulario(vista)
    campo_usuario = controles["test:login_usuario"]
    campo_contrasena = controles["test:login_contrasena"]

    assert campo_usuario.on_submit is not None
    assert campo_contrasena.on_submit is not None
    assert campo_usuario.on_submit.__name__ == "pasar_a_contrasena"
    campo_usuario.value = "ana"
    campo_contrasena.value = "secreto"
    campo_contrasena.on_submit(None)

    assert llamadas == [("ana", "secreto")]


def test_registra_clash_display_en_los_recursos_de_page():
    from types import SimpleNamespace

    page = SimpleNamespace(fonts={"Otra fuente": "fonts/otra.ttf"})

    registrar_fuentes(page)

    assert page.fonts == {
        "Otra fuente": "fonts/otra.ttf",
        FUENTE_TITULOS: "fonts/ClashDisplay-Semibold.ttf",
    }
