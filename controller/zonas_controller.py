"""CRUD de zonas, sensores y actuadores y asignación de responsable. Responsable: Rodas (OME-32).

Igual que RegistroController: cada método devuelve None si va bien o el mensaje de error.
"""
import math

from model.actuador import Actuador
from model.lista_enlazada import ListaEnlazada
from model.sensor import crear_sensor
from model.usuario import TecnicoLogistica, Usuario, ResponsableCarpa, JefeSanidad
from model.zona import Zona
from persistence.repositorio_json import RepositorioJSON
from persistence.repositorio_zonas import RepositorioZonas


class ZonasController:

    def __init__(self, repo_zonas: RepositorioZonas, repo_usuarios: RepositorioJSON) -> None:
        self.repo_zonas = repo_zonas
        self.repo_usuarios = repo_usuarios

    def listar(self, usuario: Usuario) -> ListaEnlazada:
        """Jefe de sanidad: todas. Responsable de carpa y técnico: solo las suyas."""
        if usuario.ROL == JefeSanidad.ROL:
            return self.repo_zonas.listar()
        if usuario.ROL in (ResponsableCarpa.ROL, TecnicoLogistica.ROL):
            return self.repo_zonas.zonas_de(usuario.usuario)
        return ListaEnlazada()

    def crear_zona(self, nombre: str, tipo: str, responsable: str | None) -> str | None:
        nombre = (nombre or "").strip()
        if not nombre:
            return "El nombre de la zona es obligatorio"
        if tipo not in Zona.TIPOS:
            return "Selecciona un tipo de zona válido"

        responsable = self._normalizar_responsable(responsable)
        error = self._validar_responsable(responsable)
        if error:
            return error

        zona = Zona(self.repo_zonas.siguiente_id("Z"), nombre, tipo, responsable)
        try:
            self.repo_zonas.anadir(zona)
        except ValueError:
            return "No se pudo crear la zona porque su identificador ya existe"
        return None

    def editar_zona(self, id_zona: str, nombre: str, tipo: str, responsable: str | None) -> str | None:
        zona = self.repo_zonas.buscar(id_zona)
        if zona is None:
            return "La zona no existe"

        nombre = (nombre or "").strip()
        if not nombre:
            return "El nombre de la zona es obligatorio"
        if tipo not in Zona.TIPOS:
            return "Selecciona un tipo de zona válido"

        responsable = self._normalizar_responsable(responsable)
        error = self._validar_responsable(responsable)
        if error:
            return error

        zona.nombre = nombre
        zona.tipo = tipo
        zona.responsable = responsable
        try:
            self.repo_zonas.actualizar(zona)
        except ValueError:
            return "La zona no existe"
        return None

    def eliminar_zona(self, id_zona: str) -> str | None:
        if not self.repo_zonas.eliminar(id_zona):
            return "La zona no existe"
        return None

    def anadir_sensor(
        self, id_zona: str, nombre: str, tipo: str, umbral_aviso: str, umbral_critico: str
    ) -> str | None:
        zona = self.repo_zonas.buscar(id_zona)
        if zona is None:
            return "La zona no existe"
        nombre = (nombre or "").strip()
        if not nombre:
            return "El nombre del sensor es obligatorio"

        aviso = self._convertir_umbral(umbral_aviso)
        critico = self._convertir_umbral(umbral_critico)
        if aviso is None or critico is None:
            return "Los umbrales deben ser números válidos"

        try:
            sensor = crear_sensor({
                "id": self.repo_zonas.siguiente_id("S"),
                "nombre": nombre,
                "tipo": tipo,
                "umbral_aviso": aviso,
                "umbral_critico": critico,
            })
        except (KeyError, ValueError):
            return "Selecciona un tipo de sensor válido"

        try:
            zona.anadir_sensor(sensor)
            self.repo_zonas.actualizar(zona)
        except ValueError:
            return "No se pudo añadir el sensor porque su identificador ya existe"
        return None

    def editar_sensor(
        self, id_zona: str, id_sensor: str, nombre: str, umbral_aviso: str, umbral_critico: str
    ) -> str | None:
        zona = self.repo_zonas.buscar(id_zona)
        if zona is None:
            return "La zona no existe"
        sensor = zona.buscar_sensor(id_sensor)
        if sensor is None:
            return "El sensor no existe en esa zona"

        nombre = (nombre or "").strip()
        if not nombre:
            return "El nombre del sensor es obligatorio"
        aviso = self._convertir_umbral(umbral_aviso)
        critico = self._convertir_umbral(umbral_critico)
        if aviso is None or critico is None:
            return "Los umbrales deben ser números válidos"

        sensor.nombre = nombre
        sensor.umbral_aviso = aviso
        sensor.umbral_critico = critico
        try:
            self.repo_zonas.actualizar(zona)
        except ValueError:
            return "La zona no existe"
        return None

    def eliminar_sensor(self, id_zona: str, id_sensor: str) -> str | None:
        zona = self.repo_zonas.buscar(id_zona)
        if zona is None:
            return "La zona no existe"
        if not zona.eliminar_sensor(id_sensor):
            return "El sensor no existe en esa zona"
        try:
            self.repo_zonas.actualizar(zona)
        except ValueError:
            return "La zona no existe"
        return None

    def anadir_actuador(self, id_zona: str, nombre: str, tipo: str) -> str | None:
        zona = self.repo_zonas.buscar(id_zona)
        if zona is None:
            return "La zona no existe"
        nombre = (nombre or "").strip()
        if not nombre:
            return "El nombre del actuador es obligatorio"
        if tipo not in Actuador.TIPOS:
            return "Selecciona un tipo de actuador válido"

        actuador = Actuador(self.repo_zonas.siguiente_id("A"), nombre, tipo)
        try:
            zona.anadir_actuador(actuador)
            self.repo_zonas.actualizar(zona)
        except ValueError:
            return "No se pudo añadir el actuador porque su identificador ya existe"
        return None

    def eliminar_actuador(self, id_zona: str, id_actuador: str) -> str | None:
        zona = self.repo_zonas.buscar(id_zona)
        if zona is None:
            return "La zona no existe"
        if not zona.eliminar_actuador(id_actuador):
            return "El actuador no existe en esa zona"
        try:
            self.repo_zonas.actualizar(zona)
        except ValueError:
            return "La zona no existe"
        return None

    def asignar_responsable(self, id_zona: str, usuario: str) -> str | None:
        zona = self.repo_zonas.buscar(id_zona)
        if zona is None:
            return "La zona no existe"
        nombre_usuario = self._normalizar_responsable(usuario)
        if nombre_usuario is None:
            return "Indica un usuario responsable"
        error = self._validar_responsable(nombre_usuario)
        if error:
            return error

        zona.responsable = nombre_usuario
        try:
            self.repo_zonas.actualizar(zona)
        except ValueError:
            return "La zona no existe"
        return None

    def responsables_disponibles(self) -> ListaEnlazada:
        """Usuarios responsables de carpa o técnicos de logística."""
        disponibles = ListaEnlazada()
        for usuario in self.repo_usuarios.cargar():
            if usuario.ROL in (ResponsableCarpa.ROL, TecnicoLogistica.ROL):
                disponibles.insertar(usuario)
        return disponibles

    @staticmethod
    def _normalizar_responsable(usuario: str | None) -> str | None:
        if usuario is None:
            return None
        usuario = usuario.strip()
        return usuario or None

    def _validar_responsable(self, nombre_usuario: str | None) -> str | None:
        if nombre_usuario is None:
            return None
        cuenta = self.repo_usuarios.buscar_por_usuario(nombre_usuario)
        if cuenta is None:
            return "El usuario responsable no existe"
        if cuenta.ROL not in (ResponsableCarpa.ROL, TecnicoLogistica.ROL):
            return "Solo se puede asignar a responsables de carpa o técnicos de logística"
        return None

    @staticmethod
    def _convertir_umbral(valor: str) -> float | None:
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return None
        return numero if math.isfinite(numero) else None
