"""Pruebas del repositorio de usuarios en JSON (OME-22)."""
import json

import pytest

from model.lista_enlazada import ListaEnlazada
from model.usuario import JefeSanidad, ResponsableCarpa, TecnicoLogistica, hashear
from persistence.repositorio_json import RepositorioJSON


def nuevo_usuario(clase, usuario, contrasena="omero123"):
    sal, contrasena_hash = hashear(contrasena)
    return clase("Prueba", usuario, contrasena_hash, sal)


def tres_usuarios():
    usuarios = ListaEnlazada()
    usuarios.insertar(nuevo_usuario(JefeSanidad, "ana"))
    usuarios.insertar(nuevo_usuario(ResponsableCarpa, "luis"))
    usuarios.insertar(nuevo_usuario(TecnicoLogistica, "marta", "secreta"))
    return usuarios


def test_sin_fichero_la_lista_esta_vacia(tmp_path):
    repositorio = RepositorioJSON(tmp_path / "usuarios.json")

    usuarios = repositorio.cargar()

    assert isinstance(usuarios, ListaEnlazada)
    assert len(usuarios) == 0


def test_guardar_y_volver_a_cargar_conserva_los_usuarios(tmp_path):
    ruta = tmp_path / "usuarios.json"
    RepositorioJSON(ruta).guardar(tres_usuarios())

    usuarios = RepositorioJSON(ruta).cargar()

    assert len(usuarios) == 3
    assert ",".join(u.usuario for u in usuarios) == "ana,luis,marta"


def test_al_cargar_cada_usuario_recupera_su_rol_y_su_contrasena(tmp_path):
    ruta = tmp_path / "usuarios.json"
    RepositorioJSON(ruta).guardar(tres_usuarios())

    ana, luis, marta = RepositorioJSON(ruta).cargar()

    assert isinstance(ana, JefeSanidad)
    assert isinstance(luis, ResponsableCarpa)
    assert isinstance(marta, TecnicoLogistica)
    assert marta.verificar_password("secreta")
    assert not marta.verificar_password("otra")


def test_el_json_no_guarda_la_contrasena_en_claro(tmp_path):
    ruta = tmp_path / "usuarios.json"
    RepositorioJSON(ruta).guardar(tres_usuarios())

    texto = ruta.read_text(encoding="utf-8")
    datos = json.loads(texto)

    assert datos[0]["usuario"] == "ana"
    assert datos[0]["rol"] == "jefe_sanidad"
    assert "omero123" not in texto
    assert "secreta" not in texto


def test_guardar_crea_la_carpeta_si_no_existe(tmp_path):
    ruta = tmp_path / "data" / "usuarios.json"

    RepositorioJSON(ruta).guardar(tres_usuarios())

    assert ruta.exists()


def test_un_usuario_anadido_sigue_ahi_al_reabrir(tmp_path):
    # Simula registrar un usuario, cerrar la app y volver a abrirla.
    ruta = tmp_path / "usuarios.json"
    RepositorioJSON(ruta).anadir(nuevo_usuario(JefeSanidad, "ana"))

    reabierto = RepositorioJSON(ruta)

    assert reabierto.buscar_por_usuario("ana") is not None
    assert reabierto.buscar_por_usuario("ana").verificar_password("omero123")


def test_buscar_usuario_inexistente_devuelve_none(tmp_path):
    repositorio = RepositorioJSON(tmp_path / "usuarios.json")
    repositorio.anadir(nuevo_usuario(JefeSanidad, "ana"))

    assert repositorio.buscar_por_usuario("nadie") is None


def test_buscar_devuelve_el_mismo_objeto_que_se_anadio(tmp_path):
    # El login (OME-23) comprueba con "is" que recibe el mismo objeto.
    repositorio = RepositorioJSON(tmp_path / "usuarios.json")
    ana = nuevo_usuario(JefeSanidad, "ana")
    repositorio.anadir(ana)

    assert repositorio.buscar_por_usuario("ana") is ana


def test_anadir_un_usuario_repetido_lanza_value_error(tmp_path):
    ruta = tmp_path / "usuarios.json"
    repositorio = RepositorioJSON(ruta)
    repositorio.anadir(nuevo_usuario(JefeSanidad, "ana"))

    with pytest.raises(ValueError):
        repositorio.anadir(nuevo_usuario(TecnicoLogistica, "ana"))

    assert len(RepositorioJSON(ruta).cargar()) == 1