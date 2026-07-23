import os
import sys
from pathlib import Path

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("JWT_SECRET", "test-secret")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
import asyncio
from fastapi import HTTPException

from routes import procedimentos


class FakeCollection:
    def __init__(self, count=0, doc=None):
        self.count = count
        self.calls = 0
        self.doc = doc
        self.updated = False

    async def count_documents(self, query):
        if isinstance(self.count, list):
            value = self.count[self.calls] if self.calls < len(self.count) else 0
            self.calls += 1
            return value
        return self.count

    async def find_one(self, query, projection=None):
        return self.doc

    async def update_one(self, query, update):
        self.updated = True

    async def insert_one(self, doc):
        self.doc = doc


class FakeDB:
    def __init__(self, proc_doc=None, usages=None):
        usages = usages or {}
        self.procedimentos = FakeCollection(doc=proc_doc)
        self.ordens_servico = FakeCollection(count=usages.get("ordens_servico", [0, 0]))
        self.procedimento_execucoes = FakeCollection(count=usages.get("procedimento_execucoes", 0))
        self.modelos_os = FakeCollection(count=usages.get("modelos_os", 0))
        self.modelos_inspecao = FakeCollection(count=usages.get("modelos_inspecao", 0))
        self.documentos_corporativos = FakeCollection(count=usages.get("documentos_corporativos", 0))
        self.audit_logs = FakeCollection(count=usages.get("audit_logs", 0))


def test_delete_procedimento_sem_vinculo_exclui(monkeypatch):
    fake_db = FakeDB(proc_doc={"id": "p1", "organization_id": "org1", "codigo": "P1", "nome": "Livre"})
    monkeypatch.setattr(procedimentos, "db", fake_db)

    result = asyncio.run(procedimentos.delete_procedimento("p1", {"id": "u1", "role": "admin", "organization_id": "org1"}))

    assert result == {"status": "deleted"}
    assert fake_db.procedimentos.updated is True


def test_delete_procedimento_com_os_retorna_409(monkeypatch):
    fake_db = FakeDB(
        proc_doc={"id": "p1", "organization_id": "org1", "codigo": "P1", "nome": "Usado"},
        usages={"ordens_servico": [3, 0]},
    )
    monkeypatch.setattr(procedimentos, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(procedimentos.delete_procedimento("p1", {"id": "u1", "role": "admin", "organization_id": "org1"}))

    assert exc.value.status_code == 409
    assert "3 Ordens de Serviço" in exc.value.detail["msg"]
    assert fake_db.procedimentos.updated is False


def test_delete_procedimento_inexistente_retorna_404(monkeypatch):
    fake_db = FakeDB(proc_doc=None)
    monkeypatch.setattr(procedimentos, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(procedimentos.delete_procedimento("missing", {"id": "u1", "role": "admin", "organization_id": "org1"}))

    assert exc.value.status_code == 404


def test_delete_procedimento_sem_permissao_retorna_403(monkeypatch):
    fake_db = FakeDB(proc_doc={"id": "p1", "organization_id": "org1"})
    monkeypatch.setattr(procedimentos, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(procedimentos.delete_procedimento("p1", {"id": "u1", "role": "visualizador", "organization_id": "org1"}))

    assert exc.value.status_code == 403


def test_delete_procedimento_multiempresa_retorna_404(monkeypatch):
    fake_db = FakeDB(proc_doc={"id": "p1", "organization_id": "org2"})
    monkeypatch.setattr(procedimentos, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(procedimentos.delete_procedimento("p1", {"id": "u1", "role": "pcm", "organization_id": "org1"}))

    assert exc.value.status_code == 404


def test_delete_procedimento_com_execucao_snapshot_documento_modelo_e_historico_retorna_409(monkeypatch):
    fake_db = FakeDB(
        proc_doc={"id": "p1", "organization_id": "org1"},
        usages={
            "procedimento_execucoes": 1,
            "ordens_servico": [2, 2],
            "modelos_os": 1,
            "modelos_inspecao": 1,
            "documentos_corporativos": 1,
            "audit_logs": 1,
        },
    )
    monkeypatch.setattr(procedimentos, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(procedimentos.delete_procedimento("p1", {"id": "u1", "role": "admin", "organization_id": "org1"}))

    assert exc.value.status_code == 409
    references = {item["tipo"]: item["quantidade"] for item in exc.value.detail["references"]}
    assert references["Ordens de Serviço"] == 2
    assert references["Snapshots de OS"] == 2
    assert references["Execuções"] == 1
    assert references["Modelos"] == 2
    assert references["Documentos"] == 1
    assert references["Histórico"] == 1
