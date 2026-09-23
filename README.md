# Analizador de Proyectos (PMO + IA)

CLI que analiza un CSV de tareas de proyecto, detecta cuáles están en
riesgo por retraso, y genera un informe ejecutivo redactado por IA,
validado contra un esquema estructurado.

## Por qué existe

En un rol de PMO, generar un informe de estado a partir de un export de
tareas (Jira, Excel...) es una tarea manual y repetitiva. Este proyecto
automatiza la parte de detección + redacción, dejando la decisión final
al humano.

## Arquitectura

```
CSV de tareas
      │
      ▼
┌─────────────────────┐
│  analizador.py       │  lógica PURA Python (sin IA):
│  - leer_tareas()      │  leer CSV, filtrar por umbral de retraso,
│  - detectar_riesgo()  │  clasificar nivel de riesgo
└──────────┬───────────┘
           │ solo las tareas en riesgo pasan al LLM
           ▼
┌─────────────────────┐
│  llm_client.py        │  Gemini 3.6 Flash + structured output
│  - generar_informe()  │  (Pydantic), reintentos ante 503, logging
└──────────┬───────────┘  de cada llamada (coste, tokens, latencia)
           ▼
   output/informe.json   (informe validado y guardado)
```

**Decisión clave de diseño:** la detección de "¿es esto un riesgo?" es una
regla determinista (Python puro, sin LLM) — solo se llama a la IA para la
parte que de verdad la necesita: redactar el análisis en lenguaje natural.
Esto reduce coste (si no hay riesgos, no se llama a la API en absoluto) y
hace que el 80% de la lógica sea testeable sin gastar tokens.

## Instalación

```bash
git clone <este-repo>
cd analizador-proyectos
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # y rellena tu GEMINI_API_KEY
```

## Uso

```bash
python -m src.main --csv data/tareas_ejemplo.csv
python -m src.main --csv data/tareas_ejemplo.csv --umbral-dias 3 --output output/informe.json
```

## Tests

```bash
pytest tests/ -v
```
Los tests cubren la lógica determinista (`analizador.py`) sin llamar a la
API — rápidos y gratis de ejecutar en cada cambio.

## Coste aproximado

Con `gemini-3.6-flash` y `thinking_level="low"`, cada informe de ~5 tareas
en riesgo cuesta del orden de $0.0005-0.001 (fracciones de céntimo). El
coste real se registra por llamada en `output/llm_calls.jsonl`.

## Problemas encontrados durante el desarrollo (y cómo se resolvieron)

Esta sección documenta bugs reales, no hipotéticos — todos aparecieron
construyendo las versiones previas de este proyecto:

- **Modelos deprecados sin aviso previo**: `gemini-2.5-flash` dejó de estar
  disponible para cuentas nuevas a mitad de desarrollo. Solución: el
  nombre del modelo vive en una única constante (`MODELO` en
  `llm_client.py`), no repetido por el código.
- **Tokens de "pensamiento" no visibles en la respuesta pero sí en el
  coste**: mitigado con `thinking_level="low"` para tareas de extracción
  simples, y logging explícito de `tokens_pensamiento` para poder
  auditarlo.
- **Respuestas cortadas por `max_output_tokens` insuficiente**: el logging
  registra `finish_reason` y avisa automáticamente si una respuesta se
  cortó, en vez de depender de notarlo a simple vista.
- **Rutas relativas rotas** según desde dónde se ejecuta el script:
  resuelto usando rutas basadas en la ubicación del archivo, no en el
  directorio de trabajo actual.
- **Rol incorrecto (`"tool"` en vez de `"user"`)** al devolver resultados
  de función a la API de Gemini — documentado para no repetir el error
  al extender el proyecto con tool calling en el futuro.

## Qué mejoraría con más tiempo

- Evals automatizados: un set de CSVs de prueba con riesgos esperados,
  para detectar regresiones de calidad si cambio el prompt o de modelo.
- Umbral de similitud/confianza antes de llamar al LLM en casos límite.
- Soporte para leer directamente de Jira vía su API, no solo CSV exportado
  a mano.
- Generar también una versión en Markdown/PDF del informe, no solo JSON.
