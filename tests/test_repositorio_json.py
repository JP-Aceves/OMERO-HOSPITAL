"""Pruebas del repositorio de usuarios en JSON (OME-22)."""
import json

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