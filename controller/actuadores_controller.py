"""Encender y apagar los actuadores de una zona. Responsable: Rodas (OME-66).

En el S1 el estado se guarda en data/zonas.json; en el S2 la orden irá al ESP32.
Reglas:
- Ventilador: lo cambia el responsable de su carpa (y el jefe de sanidad).
- LED de evacuación: lo cambia a mano el técnico de su zona (y el jefe), y se
  enciende solo cuando hay una alerta crítica de humo/gas (OME-60).
- El estado de todos los actuadores lo ven todos los roles.
Devuelve None si va bien, o el mensaje de error (como el resto de controladores).
"""
from model.lista_enlazada import ListaEnlazada
from model.usuario import Usuario
from persistence.repositorio_zonas import RepositorioZonas


class ActuadoresController:

    def __init__(self, repo_zonas: RepositorioZonas) -> None:
        raise NotImplementedError("OME-66")

    def de_zona(self, id_zona: str) -> ListaEnlazada:
        """Los Actuador de la zona, con su estado."""
        raise NotImplementedError("OME-66")

    def cambiar(self, id_zona: str, id_actuador: str, encendido: bool, usuario: Usuario) -> str | None:
        """Cambio manual. Comprueba el permiso del usuario según el tipo de actuador y lo guarda."""
        raise NotImplementedError("OME-66")

    def aplicar_alertas(self, alertas: ListaEnlazada) -> None:
        """Enciende el LED de evacuación de las zonas con alerta crítica de humo/gas."""
        raise NotImplementedError("OME-66")
