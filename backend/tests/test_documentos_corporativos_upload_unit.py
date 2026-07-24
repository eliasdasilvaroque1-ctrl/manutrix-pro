import sys
from types import SimpleNamespace

import pytest

from routes import documentos_corporativos as route


class FakeCollection:
    def __init__(self, find_result=None):
        self.find_result = find_result
        self.updates = []
        self.inserts = []

    async def find_one(self, *_args, **_kwargs):
        return self.find_result

    async def update_one(self, *args, **kwargs):
        self.updates.append((args, kwargs))

    async def insert_one(self, document):
        self.inserts.append(document)


class FakeObjectStore:
    def is_available(self):
        return True

    def upload_file(self, entity_type, entity_id, filename, content, content_type):
        assert entity_type == "docs"
        assert entity_id == "org-1"
        assert filename.startswith("doc-1_")
        assert content == b"%PDF-test"
        assert content_type == "application/pdf"
        return "manutrix/docs/org-1/private-file.pdf"


class FakeUpload:
    filename = "procedimento.pdf"
    content_type = "application/pdf"

    async def read(self):
        return b"%PDF-test"


@pytest.mark.asyncio
async def test_upload_registers_private_file_for_document_organization(monkeypatch, tmp_path):
    document = {
        "id": "doc-1",
        "organization_id": "org-1",
        "deleted_at": None,
    }
    fake_db = SimpleNamespace(
        documentos_corporativos=FakeCollection(find_result=document),
        documentos_file_history=FakeCollection(),
        file_registry=FakeCollection(),
        audit_logs=FakeCollection(),
    )
    fake_server = SimpleNamespace(objstore=FakeObjectStore(), UPLOAD_DIR=tmp_path)

    monkeypatch.setattr(route, "db", fake_db)
    monkeypatch.setitem(sys.modules, "server", fake_server)

    result = await route.upload_document_file(
        "doc-1",
        FakeUpload(),
        {"id": "user-1", "role": "admin", "organization_id": "org-1"},
    )

    assert result["status"] == "uploaded"
    assert result["file_url"] == "/api/storage/manutrix/docs/org-1/private-file.pdf"

    (args, kwargs), = fake_db.file_registry.updates
    assert args[0] == {"url": result["file_url"]}
    assert args[1]["$set"]["organization_id"] == "org-1"
    assert args[1]["$set"]["document_id"] == "doc-1"
    assert args[1]["$set"]["is_public"] is False
    assert kwargs["upsert"] is True
