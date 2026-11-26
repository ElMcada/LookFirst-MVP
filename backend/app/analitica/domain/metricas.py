"""Cálculo de los indicadores de éxito del proyecto (OE4, REQ-04). Funciones puras, sin BD."""
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime

LIMITE_LATENCIA_S = 6.0   # REQ-04
META_SATISFACCION = 8.0   # OE4: promedio superior a 8/10
META_REDUCCION = 0.40     # OE4: -40 % en tiempo de indecisión


@dataclass(frozen=True)
class FilaConsulta:
    id: object
    estado: str
    iniciada_en: datetime
    finalizada_en: datetime | None
    satisfaccion: int | None


@dataclass(frozen=True)
class FilaSimulacion:
    consulta_id: object
    origen: str
    modo: str
    latencia_ms: int
    estilo_nombre: str | None
    instruccion: str | None
    elegida_en: datetime | None


def _prom(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 2) if xs else None


def _p95(xs: list[float]) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    return round(s[min(len(s) - 1, math.ceil(0.95 * len(s)) - 1)], 2)


def calcular(consultas: list[FilaConsulta], sims: list[FilaSimulacion], tradicional_min: float = 0) -> dict:
    estados = Counter(c.estado for c in consultas)
    inicio = {c.id: c.iniciada_en for c in consultas}

    decisiones = [(s.elegida_en - inicio[s.consulta_id]).total_seconds() / 60
                  for s in sims if s.elegida_en and s.consulta_id in inicio]
    duraciones = [(c.finalizada_en - c.iniciada_en).total_seconds() / 60
                  for c in consultas if c.estado == "finalizada" and c.finalizada_en]
    notas = [c.satisfaccion for c in consultas if c.satisfaccion is not None]
    lat = [s.latencia_ms / 1000 for s in sims]
    cerradas = estados["finalizada"] + estados["cancelada"] + estados["expirada"]

    t_decision = _prom(decisiones)
    reduccion = round(1 - t_decision / tradicional_min, 3) if t_decision is not None and tradicional_min > 0 else None
    sat = _prom(notas)
    lat_prom = _prom(lat)

    elegidos = Counter(s.estilo_nombre or "Pedido libre (texto/voz)" for s in sims if s.elegida_en)
    return {
        "consultas": {"total": len(consultas), "activas": estados["activa"], "finalizadas": estados["finalizada"],
                      "canceladas": estados["cancelada"], "expiradas": estados["expirada"]},
        "decision": {
            "consultas_con_decision": len(decisiones),
            "tasa_decision": round(len(decisiones) / cerradas, 3) if cerradas else None,
            "tiempo_promedio_min": t_decision,
            "duracion_promedio_consulta_min": _prom(duraciones),
            "tiempo_tradicional_min": tradicional_min or None,
            "reduccion": reduccion,
            "cumple_kpi": None if reduccion is None else reduccion >= META_REDUCCION,
        },
        "satisfaccion": {"respuestas": len(notas), "promedio": sat,
                         "cumple_kpi": None if sat is None else sat > META_SATISFACCION},
        "latencia": {
            "simulaciones": len(lat), "promedio_s": lat_prom, "p95_s": _p95(lat),
            "dentro_limite": round(sum(x <= LIMITE_LATENCIA_S for x in lat) / len(lat), 3) if lat else None,
            "limite_s": LIMITE_LATENCIA_S, "cumple_kpi": None if lat_prom is None else lat_prom <= LIMITE_LATENCIA_S,
        },
        "simulaciones": {
            "promedio_por_consulta": round(len(sims) / len(consultas), 2) if consultas else None,
            "por_origen": dict(Counter(s.origen for s in sims)),
            "por_modo": dict(Counter(s.modo for s in sims)),
        },
        "looks_mas_elegidos": [{"nombre": n, "veces": v} for n, v in elegidos.most_common(5)],
    }
