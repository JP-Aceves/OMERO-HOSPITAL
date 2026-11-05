def test_los_modulos_se_importan():
    import controller.dashboard_controller
    import controller.login_controller
    import controller.navegacion
    import controller.registro_controller
    import controller.usuarios_controller
    import controller.zonas_controller
    import model.actuador
    import model.lectura
    import model.lista_enlazada
    import model.sensor
    import model.usuario
    import model.zona
    import persistence.repositorio_json
    import persistence.repositorio_lecturas
    import persistence.repositorio_zonas
    import service.estado
    import service.simulador
    import view.dashboard_jefe_view
    import view.inicio_view
    import view.login_view
    import view.registro_view
    import view.shell_view
    import view.tema
    import view.usuarios_view
    import view.zonas_view  # noqa: F401


def test_cada_sensor_define_tipo_unidad_y_rango():
    from model.sensor import Sensor

    tipos = {clase.TIPO for clase in Sensor.__subclasses__()}
    assert tipos == {"temperatura", "humedad", "calidad_aire", "luz",
                     "humo_gas", "nivel_deposito", "viento"}
    for clase in Sensor.__subclasses__():
        assert clase.UNIDAD and clase.MODELO
        assert clase.RANGO[0] < clase.RANGO[1]


def test_todos_los_roles_tienen_menu():
    from controller.navegacion import MENU_POR_ROL

    assert set(MENU_POR_ROL) == {"administrador", "jefe_sanidad",
                                 "responsable_carpa", "tecnico_logistica"}


def test_solo_luz_y_deposito_son_inversos():
    from model.sensor import Sensor

    inversos = {clase.TIPO for clase in Sensor.__subclasses__() if clase.INVERSO}
    assert inversos == {"luz", "nivel_deposito"}


def test_unidades_acordadas():
    from model.sensor import Sensor

    unidades = {clase.TIPO: clase.UNIDAD for clase in Sensor.__subclasses__()}
    assert unidades == {"temperatura": "°C", "humedad": "%", "calidad_aire": "%",
                        "luz": "%", "humo_gas": "%", "nivel_deposito": "%",
                        "viento": "km/h"}
