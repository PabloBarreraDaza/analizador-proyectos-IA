"""
Analizador de Proyectos — Proyecto 2

Uso:
    python -m src.main --csv data/tareas_ejemplo.csv
    python -m src.main --csv data/tareas_ejemplo.csv --umbral-dias 3 --output output/informe.json

Ejecutar desde la raíz del proyecto (analizador-proyectos/).
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.analizador import leer_tareas, detectar_tareas_en_riesgo
from src.llm_client import crear_cliente, generar_informe

load_dotenv()  # carga GEMINI_API_KEY desde .env si existe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analiza un CSV de tareas y genera un informe de riesgos con IA.")
    parser.add_argument("--csv", required=True, help="Ruta al CSV de tareas.")
    parser.add_argument("--umbral-dias", type=int, default=1, help="Días de retraso mínimos para considerar riesgo (default: 1).")
    parser.add_argument("--output", default="output/informe.json", help="Ruta de salida del informe JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(f"Leyendo tareas de {args.csv}...")
    try:
        tareas = leer_tareas(args.csv)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    en_riesgo = detectar_tareas_en_riesgo(tareas, umbral_dias=args.umbral_dias)
    print(f"{len(tareas)} tareas totales, {len(en_riesgo)} en riesgo (umbral: {args.umbral_dias}+ días).")

    if not en_riesgo:
        print(" No hay tareas en riesgo con el umbral indicado. No se llama al LLM (ahorro de coste).")
        return

    print("Generando informe con IA...")
    client = crear_cliente()
    informe = generar_informe(client, en_riesgo, total_tareas=len(tareas))

    ruta_salida = Path(args.output)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    ruta_salida.write_text(informe.model_dump_json(indent=2), encoding="utf-8")

    print(f"\n--- RESUMEN EJECUTIVO ---\n{informe.resumen_ejecutivo}\n")
    print("--- RIESGOS DETECTADOS ---")
    for r in informe.riesgos:
        print(f"[{r.nivel.upper()}] {r.tarea_id} ({r.area_afectada}): {r.descripcion}")

    print(f"\n Informe completo guardado en {ruta_salida}")


if __name__ == "__main__":
    main()
