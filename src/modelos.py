"""Esquemas de datos (structured output) para el informe de riesgos."""

from pydantic import BaseModel


class Riesgo(BaseModel):
    tarea_id: str
    tarea_nombre: str
    dias_retraso: int
    nivel: str  # "bajo", "medio", "alto"
    descripcion: str
    area_afectada: str


class InformeRiesgos(BaseModel):
    total_tareas_analizadas: int
    total_tareas_en_riesgo: int
    riesgos: list[Riesgo]
    resumen_ejecutivo: str
