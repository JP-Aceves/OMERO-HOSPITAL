def test_los_modulos_se_importan():
    import controller.login_controller
    import controller.registro_controller
    import model.lista_enlazada
    import model.usuario
    import persistence.repositorio_json
    import view.login_view
    import view.registro_view  # noqa: F401
