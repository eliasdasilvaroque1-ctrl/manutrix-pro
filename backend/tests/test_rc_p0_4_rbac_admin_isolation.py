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

import server
from models import UserCreate, UserRole


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *args, **kwargs):
        return self

    async def to_list(self, limit):
        return self.docs[:limit]


class FakeCollection:
    def __init__(self, doc=None, docs=None):
        self.doc = doc
        self.docs = docs if docs is not None else ([doc] if doc else [])
        self.last_find_query = None
        self.last_update_query = None
        self.last_insert = None
        self.last_delete_query = None

    async def find_one(self, query, projection=None):
        self.last_find_query = query
        if self.doc and all(self.doc.get(k) == v for k, v in query.items() if not isinstance(v, dict)):
            return self.doc
        return None

    def find(self, query, projection=None):
        self.last_find_query = query
        return FakeCursor(self.docs)

    async def update_one(self, query, update):
        self.last_update_query = query

    async def insert_one(self, doc):
        self.last_insert = doc

    async def delete_one(self, query):
        self.last_delete_query = query


class FakeDB:
    def __init__(self, target=None):
        self.users = FakeCollection(target)
        self.knowledge_base = FakeCollection(docs=[{"id": "kb1", "organization_id": "org1"}])


def test_admin_update_user_cross_org_retorna_404(monkeypatch):
    monkeypatch.setattr(server, "db", FakeDB({"id": "u2", "organization_id": "org2", "deleted_at": None}))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(server.admin_update_user("u2", {"nome": "Outro"}, {"id": "admin", "role": "admin", "organization_id": "org1"}))

    assert exc.value.status_code == 404


def test_admin_reset_password_cross_org_retorna_404(monkeypatch):
    monkeypatch.setattr(server, "db", FakeDB({"id": "u2", "organization_id": "org2", "deleted_at": None}))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(server.admin_reset_password("u2", {"id": "admin", "role": "admin", "organization_id": "org1"}))

    assert exc.value.status_code == 404


def test_admin_delete_user_cross_org_retorna_404(monkeypatch):
    fake_db = FakeDB({"id": "u2", "organization_id": "org2", "deleted_at": None})
    monkeypatch.setattr(server, "db", fake_db)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(server.admin_delete_user("u2", {"id": "admin", "role": "admin", "organization_id": "org1"}))

    assert exc.value.status_code == 404
    assert fake_db.users.last_update_query is None


def test_admin_nao_cria_usuario_em_outra_empresa(monkeypatch):
    monkeypatch.setattr(server, "db", FakeDB())
    data = UserCreate(email="novo@teste.com", nome="Novo", password="123456", role=UserRole.TEC_MECANICO, organization_id="org2")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(server.admin_create_user(data, {"id": "admin", "role": "admin", "organization_id": "org1"}))

    assert exc.value.status_code == 403


def test_master_pode_criar_usuario_em_outra_empresa(monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(server, "db", fake_db)
    monkeypatch.setattr(server, "supabase_client", None)
    data = UserCreate(email="novo@teste.com", nome="Novo", password="123456", role=UserRole.TEC_MECANICO, organization_id="org2")

    created = asyncio.run(server.admin_create_user(data, {"id": "master", "role": "master", "organization_id": "org1"}))

    assert created["organization_id"] == "org2"
    assert created["active"] is True


def test_knowledge_base_list_filtra_empresa(monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(server, "db", fake_db)

    asyncio.run(server.list_knowledge(user={"id": "u1", "role": "admin", "organization_id": "org1"}))

    assert fake_db.knowledge_base.last_find_query["organization_id"] == "org1"
