"""
Lógica de negocio PURA: sin llamadas a ningún LLM. Esto es a propósito —
la detección de "¿esta tarea es un riesgo?" es una regla determinista
(días de retraso >= umbral), no algo que necesite inteligencia artificial.
Reservamos el LLM solo para la parte que de verdad lo necesita: redactar
el análisis en lenguaje natural.

Ventaja práctica: estas funciones se pueden testear sin gastar tokens ni
depender de que la API esté disponible.
"""

import csv
from pathlib import Path


def leer_tareas(ruta_csv: str | Path) -> list[dict]:
    """Lee el CSV de tareas y devuelve una lista de diccionarios."""
    ruta_csv = Path(ruta_csv)
    if not ruta_csv.exists():
        raise FileNotFoundError(f"No se encontró el archivo de tareas: {ruta_csv}")

    with open(ruta_csv, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    for fila in filas:
        fila["dias_retraso"] = int(fila["dias_retraso"])

    return filas


def detectar_tareas_en_riesgo(tareas: list[dict], umbral_dias: int = 1) -> list[dict]:
    """Filtra las tareas con retraso igual o mayor al umbral.

    Esta es la parte "Python detecta retrasos/riesgos" de la que habla el
    roadmap — una regla simple y determinista, no una llamada a un LLM.
    """
    return [t for t in tareas if t["dias_retraso"] >= umbral_dias]


def calcular_nivel_riesgo(dias_retraso: int) -> str:
    """Clasifica el nivel de riesgo según los días de retraso.

    Umbrales elegidos de forma razonable para este proyecto:
    1-2 días = bajo, 3-5 = medio, 6+ = alto. Ajustables según el contexto real.
    """
    if dias_retraso >= 6:
        return "alto"
    if dias_retraso >= 3:
        return "medio"
    return "bajo"
