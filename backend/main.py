"""Punto de entrada: uvicorn main:app --reload --port 8000"""
from app.bootstrap import create_app

app = create_app()
