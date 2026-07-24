from types import SimpleNamespace

import pytest

from procedure_catalog import (
    CORPORATE_SOURCE,
    LEGACY_SOURCE,
    build_procedure_catalog,
    find_active_procedure,
    is_corporate_procedure,
    matches_search,
    normalize_corporate_procedure,
)


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    async def to_list(self, _limit):
        return self.documents


class FakeCollection:
    def __init__(self, documents):
        self.documents = documents
        self.queries = []

    def find(self, query, _projection=None):
        self.queries.append(query)
        documents = [
            item for item in self.documents
            if item.get("organization_id") == query.get("organization_id")
            and item.get("deleted_at") is None
        ]
        return FakeCursor(documents)

    async def find_one(self, query, _projection=None):
        self.queries.append(query)
        for item in self.documents:
            if all(item.get(key) == value for key, value in query.items()):
                return item
        return None


def make_database(corporate=None, legacy=None):
    return SimpleNamespace(
        documentos_corporativos=FakeCollection(corporate or []),
        procedimentos=FakeCollection(legacy or []),
    )


@pytest.mark.asyncio
async def test_catalog_uses_corporate_documents_without_creating_duplicates():
    corporate = [
        {
            "id": "doc-1",
            "organization_id": "org-a",
            "title": "Procedimento de manutenção ALIMENTADORES VIBRATÓRIOS",
            "code": "PM-001",
            "document_type": "procedimento_manutencao",
            "status": "publicado",
            "is_active": True,
            "version": 4,
            "updated_at": "2026-07-24T12:00:00+00:00",
            "deleted_at": None,
        },
        {
            "id": "doc-2",
            "organization_id": "org-a",
            "title": "PROCEDIMENTO DE MANUTENÇÃO ELÉTRICA",
            "document_type": {"value": "procedimento_operacional", "label": "Procedimento"},
            "status": {"value": "publicado"},
            "is_active": True,
            "version": 2,
            "deleted_at": None,
        },
        {
            "id": "draft-1",
            "organization_id": "org-a",
            "title": "Rascunho",
            "document_type": "procedimento_manutencao",
            "status": "rascunho",
            "is_active": True,
            "deleted_at": None,
        },
        {
            "id": "manual-1",
            "organization_id": "org-a",
            "title": "Manual",
            "document_type": "manual",
            "status": "publicado",
            "is_active": True,
            "deleted_at": None,
        },
        {
            "id": "foreign-1",
            "organization_id": "org-b",
            "title": "Outro cliente",
            "document_type": "procedimento_operacional",
            "status": "publicado",
            "is_active": True,
            "deleted_at": None,
        },
    ]
    legacy = [
        {
            "id": "legacy-1",
            "organization_id": "org-a",
            "nome": "Procedimento legado aprovado",
            "status": "aprovado",
            "deleted_at": None,
        },
        {
            "id": "legacy-shadow",
            "source_id": "doc-1",
            "organization_id": "org-a",
            "nome": "Cópia antiga",
            "status": "aprovado",
            "deleted_at": None,
        },
    ]
    database = make_database(corporate, legacy)

    result = await build_procedure_catalog(
        database,
        "org-a",
        {"role": "admin", "organization_id": "org-a"},
    )

    items_by_id = {item["id"]: item for item in result["items"]}
    assert set(items_by_id) == {"doc-1", "doc-2", "legacy-1"}
    assert items_by_id["doc-1"]["source"] == CORPORATE_SOURCE
    assert items_by_id["doc-1"]["versao"] == 4
    assert items_by_id["legacy-1"]["source"] == LEGACY_SOURCE
    assert result["totals"] == {
        "total": 4,
        "published": 3,
        "draft": 1,
        "archived": 0,
        "filtered": 3,
        "corporate": 3,
        "legacy": 1,
        "by_status": {"publicado": 2, "rascunho": 1, "aprovado": 1},
    }
    assert database.documentos_corporativos.queries[0]["organization_id"] == "org-a"
    assert database.procedimentos.queries[0]["organization_id"] == "org-a"


@pytest.mark.asyncio
async def test_catalog_search_and_archive_filter_share_the_list_count():
    corporate = [
        {
            "id": "doc-1",
            "organization_id": "org-a",
            "title": "Manutenção elétrica",
            "code": "ELE-9",
            "document_type": "procedimento_manutencao",
            "discipline": "elétrica",
            "applicable_areas": ["Britagem"],
            "tags": ["alimentador"],
            "description": "Bloqueio e teste",
            "status": "publicado",
            "is_active": True,
            "deleted_at": None,
        },
        {
            "id": "doc-2",
            "organization_id": "org-a",
            "title": "Procedimento arquivado",
            "document_type": "procedimento_operacional",
            "status": "arquivado",
            "is_active": False,
            "deleted_at": None,
        },
    ]
    database = make_database(corporate, [])
    user = {"role": "admin", "organization_id": "org-a"}

    searched = await build_procedure_catalog(database, "org-a", user, search="ALIMENTADOR")
    archived = await build_procedure_catalog(database, "org-a", user, status="arquivado")

    assert [item["id"] for item in searched["items"]] == ["doc-1"]
    assert searched["totals"]["filtered"] == len(searched["items"]) == 1
    assert [item["id"] for item in archived["items"]] == ["doc-2"]
    assert archived["totals"]["filtered"] == len(archived["items"]) == 1


def test_legacy_object_fields_are_normalized_for_type_status_and_search():
    document = {
        "id": "doc-object",
        "title": "Procedimento hidráulico",
        "document_type": {"value": "procedimento_manutencao"},
        "status": {"label": "Publicado", "value": "publicado"},
        "discipline": {"label": "Mecânica"},
        "tags": [{"label": "Prensa"}],
    }

    assert is_corporate_procedure(document)
    item = normalize_corporate_procedure(document)
    assert item["status"] == "publicado"
    assert matches_search(item, "prensa")
    assert matches_search(item, "mecanica")


@pytest.mark.asyncio
async def test_active_lookup_is_tenant_scoped_and_preserves_corporate_id():
    database = make_database([{
        "id": "doc-1",
        "organization_id": "org-a",
        "title": "Procedimento",
        "document_type": "procedimento_operacional",
        "status": "publicado",
        "is_active": True,
        "deleted_at": None,
    }], [])

    own = await find_active_procedure(database, "doc-1", "org-a")
    foreign = await find_active_procedure(database, "doc-1", "org-b")

    assert own["id"] == "doc-1"
    assert own["source"] == CORPORATE_SOURCE
    assert foreign is None


@pytest.mark.asyncio
async def test_field_user_only_receives_published_and_authorized_documents():
    database = make_database([
        {
            "id": "published",
            "organization_id": "org-a",
            "title": "Publicado",
            "document_type": "procedimento_operacional",
            "status": "publicado",
            "is_active": True,
            "deleted_at": None,
        },
        {
            "id": "draft",
            "organization_id": "org-a",
            "title": "Rascunho",
            "document_type": "procedimento_operacional",
            "status": "rascunho",
            "is_active": True,
            "deleted_at": None,
        },
        {
            "id": "restricted",
            "organization_id": "org-a",
            "title": "Restrito",
            "document_type": "procedimento_operacional",
            "status": "publicado",
            "is_active": True,
            "security_classification": "restrito",
            "deleted_at": None,
        },
    ], [
        {
            "id": "legacy-draft",
            "organization_id": "org-a",
            "nome": "Legado rascunho",
            "status": "rascunho",
            "deleted_at": None,
        },
        {
            "id": "restricted-shadow",
            "source_id": "restricted",
            "organization_id": "org-a",
            "nome": "Cópia do restrito",
            "status": "aprovado",
            "deleted_at": None,
        },
    ])

    result = await build_procedure_catalog(
        database,
        "org-a",
        {"role": "tec_eletrico", "organization_id": "org-a"},
        status="todos",
    )

    assert [item["id"] for item in result["items"]] == ["published"]
