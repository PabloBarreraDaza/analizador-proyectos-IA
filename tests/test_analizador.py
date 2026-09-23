"""
Tests de la parte determinista (analizador.py). A propósito, NINGUNO de
estos tests llama al LLM — son rápidos, gratis, y no dependen de que la
API esté disponible. Ejecutar con: pytest tests/
"""

import csv
import sys
from pathlib import Path

# Mismo motivo que en main.py: para que funcione tanto con pytest como
# ejecutando este archivo directamente.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.analizador import leer_tareas, detectar_tareas_en_riesgo, calcular_nivel_riesgo


@pytest.fixture
def csv_temporal(tmp_path: Path) -> Path:
    """Crea un CSV de prueba temporal, aislado de data/tareas_ejemplo.csv."""
    ruta = tmp_path / "tareas_test.csv"
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "nombre", "area", "dias_retraso"])
        writer.writerow(["T-1", "Tarea A", "Backend", "0"])
        writer.writerow(["T-2", "Tarea B", "QA", "5"])
        writer.writerow(["T-3", "Tarea C", "Infra", "8"])
    return ruta


def test_leer_tareas_convierte_dias_retraso_a_entero(csv_temporal):
    tareas = leer_tareas(csv_temporal)
    assert all(isinstance(t["dias_retraso"], int) for t in tareas)


def test_leer_tareas_archivo_inexistente_lanza_error():
    with pytest.raises(FileNotFoundError):
        leer_tareas("archivo/que/no/existe.csv")


def test_detectar_tareas_en_riesgo_filtra_por_umbral(csv_temporal):
    tareas = leer_tareas(csv_temporal)
    en_riesgo = detectar_tareas_en_riesgo(tareas, umbral_dias=1)
    assert len(en_riesgo) == 2  # T-2 y T-3, no T-1 (0 días)
    assert all(t["dias_retraso"] >= 1 for t in en_riesgo)


def test_detectar_tareas_en_riesgo_umbral_mas_estricto(csv_temporal):
    tareas = leer_tareas(csv_temporal)
    en_riesgo = detectar_tareas_en_riesgo(tareas, umbral_dias=6)
    assert len(en_riesgo) == 1  # solo T-3 (8 días)
    assert en_riesgo[0]["id"] == "T-3"


@pytest.mark.parametrize(
    "dias,nivel_esperado",
    [(0, "bajo"), (2, "bajo"), (3, "medio"), (5, "medio"), (6, "alto"), (10, "alto")],
)
def test_calcular_nivel_riesgo(dias, nivel_esperado):
    assert calcular_nivel_riesgo(dias) == nivel_esperado
