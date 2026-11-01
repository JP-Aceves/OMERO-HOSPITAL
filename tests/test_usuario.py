import json

import pytest

from model.usuario import (
    JefeSanidad,
    ResponsableCarpa,
    TecnicoLogistica,
    Usuario,
    crear_usuario,
    hashear,
)


SALT = "00112233445566778899aabbccddeeff"
ROLES = [
    (JefeSanidad, "jefe_sanidad"),
    (ResponsableCarpa, "responsable_carpa"),
    (TecnicoLogistica, "tecnico_logistica"),
]


def test_la_misma_contrasena_recibe_sales_y_hashes_distintos():
    sal_a, hash_a = hashear("omero123")
    sal_b, hash_b = hashear("omero123")

    assert sal_a != sal_b
    assert hash_a != hash_b
    assert len(bytes.fromhex(sal_a)) == 16
    assert len(bytes.fromhex(hash_a)) == 32


@pytest.mark.parametrize(
    ("contrasena", "hash_esperado"),
    [
        (
            "omero123",
            "ca83396aa0b2c1d92e2843e0b9aafaf12947ace80362ecb37b29d1671fa5d6a2",
        ),
        (
            "contraseña-安全",
            "c590ad8064f0c55bb21c5e22a25f4b9dd37c1bc686899593fc2c75bae19b5e94",
        ),
    ],
)
def test_hashear_con_sal_fija_coincide_con_vector_pbkdf2(contrasena, hash_esperado):
    assert hashear(contrasena, SALT) == (SALT, hash_esperado)


@pytest.mark.parametrize(("clase", "rol"), ROLES)
def test_cada_rol_verifica_la_contrasena(clase, rol):
    sal, hash_contrasena = hashear("contraseña-安全", SALT)
    usuario = clase("María", "maria", hash_contrasena, sal)

    assert isinstance(usuario, Usuario)
    assert usuario.ROL == rol
    assert usuario.verificar_password("contraseña-安全") is True
    assert usuario.verificar_password("otra contraseña") is False


@pytest.mark.parametrize(("clase", "rol"), ROLES)
def test_serializar_y_reconstruir_json_preserva_rol_y_credenciales(clase, rol):
    sal, hash_contrasena = hashear("omero123", SALT)
    original = clase("María López", "maria", hash_contrasena, sal)

    datos = original.to_dict()
    assert datos == {
        "nombre": "María López",
        "usuario": "maria",
        "rol": rol,
        "sal": sal,
        "hash": hash_contrasena,
    }

    texto_json = json.dumps(datos, ensure_ascii=False)
    assert "omero123" not in texto_json
    reconstruido = crear_usuario(json.loads(texto_json))

    assert type(reconstruido) is clase
    assert reconstruido.to_dict() == datos
    assert reconstruido.verificar_password("omero123") is True
    assert reconstruido.verificar_password("incorrecta") is False


def test_crear_usuario_rechaza_un_rol_desconocido():
    datos = {
        "nombre": "Ana",
        "usuario": "ana",
        "rol": "administrador",
        "sal": SALT,
        "hash": "ca83396aa0b2c1d92e2843e0b9aafaf12947ace80362ecb37b29d1671fa5d6a2",
    }

    with pytest.raises(ValueError):
        crear_usuario(datos)


def test_usuario_base_no_se_puede_instanciar():
    with pytest.raises(TypeError):
        Usuario("Ana", "ana", "hash", SALT)
