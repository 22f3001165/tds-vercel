import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin"],
)

DATA = json.loads((Path(__file__).parent / "q-vercel-latency.json").read_text())


class Query(BaseModel):
    regions: list[str]
    threshold_ms: float


def percentile(values, q):
    v = sorted(values)
    pos = (len(v) - 1) * q
    lo = int(pos)
    frac = pos - lo
    return v[lo] + frac * (v[lo + 1] - v[lo]) if lo + 1 < len(v) else v[lo]


@app.post("/api/latency")
def latency(q: Query):
    out = []
    for region in q.regions:
        rows = [r for r in DATA if r["region"] == region]
        lat = [r["latency_ms"] for r in rows]
        up = [r["uptime_pct"] for r in rows]
        out.append({
            "region": region,
            "avg_latency": round(sum(lat) / len(lat), 2),
            "p95_latency": round(percentile(lat, 0.95), 2),
            "avg_uptime": round(sum(up) / len(up), 3),
            "breaches": sum(1 for x in lat if x > q.threshold_ms),
        })
    return {"regions": out}
