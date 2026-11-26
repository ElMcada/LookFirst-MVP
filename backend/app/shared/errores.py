"""Errores de dominio. La capa API los traduce a códigos HTTP; el dominio no conoce HTTP."""


class ErrorDominio(Exception):
    codigo_http = 400

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class EntradaInvalida(ErrorDominio):
    codigo_http = 422


class NoEncontrado(ErrorDominio):
    codigo_http = 404


class NoAutenticado(ErrorDominio):
    codigo_http = 401


class Prohibido(ErrorDominio):
    codigo_http = 403


class Conflicto(ErrorDominio):
    codigo_http = 409
