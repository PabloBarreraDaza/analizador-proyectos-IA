"""
Todo lo relacionado con el LLM vive aquí, separado de la lógica de negocio
(analizador.py) y del punto de entrada (main.py). Si mañana cambias de
proveedor (Gemini -> Claude -> OpenAI), este es el único archivo que
tocarías.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import types, errors
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.modelos import InformeRiesgos

MODELO = "gemini-3.6-flash"
RUTA_LOG = Path(__file__).parent.parent / "output" / "llm_calls.jsonl"


def crear_cliente() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta la variable de entorno GEMINI_API_KEY. "
            "Copia .env.example a .env y añade tu key, o expórtala en tu terminal."
        )
    return genai.Client(api_key=api_key)


def _registrar_llamada(respuesta, duracion_seg: float) -> None:
    """Log en JSONL — pilar 1 de LLMOps, ver bloque 7 del roadmap."""
    uso = respuesta.usage_metadata
    entrada = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modelo": MODELO,
        "duracion_seg": round(duracion_seg, 2),
        "tokens_input": uso.prompt_token_count or 0,
        "tokens_output": uso.candidates_token_count or 0,
        "tokens_pensamiento": uso.thoughts_token_count or 0,
        "tokens_total": uso.total_token_count,
        "finish_reason": respuesta.candidates[0].finish_reason.name,
    }
    RUTA_LOG.parent.mkdir(exist_ok=True)
    with open(RUTA_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")

    if entrada["finish_reason"] == "MAX_TOKENS":
        print("⚠️  Respuesta cortada por límite de tokens — considera subir max_output_tokens.")


@retry(
    retry=retry_if_exception_type(errors.ServerError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
)
def generar_informe(client: genai.Client, tareas_en_riesgo: list[dict], total_tareas: int) -> InformeRiesgos:
    """Le pide al LLM que redacte el análisis y lo devuelve ya validado
    contra el esquema InformeRiesgos (structured output)."""

    contexto = "\n".join(
        f"- {t['id']} ({t['nombre']}, área: {t.get('area', 'N/D')}): {t['dias_retraso']} días de retraso"
        for t in tareas_en_riesgo
    )

    prompt = (
        f"Aquí tienes {len(tareas_en_riesgo)} tareas de un proyecto que están "
        f"retrasadas, de un total de {total_tareas} tareas:\n\n{contexto}\n\n"
        "Para cada una, redacta una descripción breve del riesgo concreto que "
        "supone y clasifica su nivel de urgencia (bajo, medio, alto) según el "
        "retraso. Termina con un resumen ejecutivo de 2-3 frases sobre el "
        "estado global del proyecto. Usa EXCLUSIVAMENTE los datos proporcionados."
    )

    inicio = time.perf_counter()
    respuesta = client.models.generate_content(
        model=MODELO,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=InformeRiesgos,
            thinking_config=types.ThinkingConfig(thinking_level="low"),
            max_output_tokens=1500,
        ),
    )
    duracion = time.perf_counter() - inicio
    _registrar_llamada(respuesta, duracion)

    return respuesta.parsed
