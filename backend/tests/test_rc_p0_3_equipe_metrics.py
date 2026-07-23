import os
import sys
import asyncio
from pathlib import Path

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("JWT_SECRET", "test-secret")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi import HTTPException

from routes import events


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    async def to_list(self, limit):
        return self.docs[:limit]


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []
        self.last_query = None

    def find(self, query, projection=None):
        self.last_query = query
        return FakeCursor(self.docs)


class FakeDB:
    def __init__(self, users=None, dailies=None, monthlies=None):
        self.users = FakeCollection(users)
        self.metricas_diarias = FakeCollection(dailies)
        self.metricas_mensais = FakeCollection(monthlies)


def test_metricas_equipe_inclui_tecnicos_ativos_sem_metrica(monkeypatch):
    fake_db = FakeDB(users=[
        {"id": "u1", "nome": "Mecânico", "role": "tec_mecanico"},
        {"id": "u2", "nome": "Supervisor", "role": "supervisor"},
    ], monthlies=[
        {"user_id": "u1", "os_total": 2, "hh_liquida_min": 90, "os_por_tipo": {"corretiva": 2}},
    ])
    monkeypatch.setattr(events, "db", fake_db)

    result = asyncio.run(events.get_team_metrics("mes", {"organization_id": "org1", "role": "admin"}))

    by_user = {m["user_id"]: m for m in result}
    assert by_user["u1"]["os_total"] == 2
    assert by_user["u1"]["hh_liquida_min"] == 90
    assert by_user["u2"]["os_total"] == 0
    assert by_user["u2"]["hh_liquida_min"] == 0
    assert fake_db.users.last_query["active"] == {"$ne": False}
    assert "tec_mecanico" in fake_db.users.last_query["role"]["$in"]


def test_metricas_equipe_suporta_hoje_semana_mes_ano(monkeypatch):
    fake_db = FakeDB(users=[{"id": "u1", "nome": "Técnico", "role": "tec_eletrico"}], dailies=[
        {"user_id": "u1", "os_total": 1, "hh_liquida_min": 30, "os_por_tipo": {"preventiva": 1}},
    ], monthlies=[
        {"user_id": "u1", "os_total": 3, "hh_liquida_min": 120, "os_por_tipo": {"corretiva": 3}},
    ])
    monkeypatch.setattr(events, "db", fake_db)

    for periodo in ("hoje", "semana", "mes", "ano"):
        result = asyncio.run(events.get_team_metrics(periodo, {"organization_id": "org1", "role": "admin"}))
        assert len(result) == 1
        assert result[0]["user_id"] == "u1"


def test_metricas_equipe_periodo_invalido_retorna_400(monkeypatch):
    fake_db = FakeDB(users=[{"id": "u1", "nome": "Técnico", "role": "tecnico"}])
    monkeypatch.setattr(events, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(events.get_team_metrics("quinzena", {"organization_id": "org1", "role": "admin"}))

    assert exc.value.status_code == 400
