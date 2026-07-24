"""Unified read model for operational procedures.

Corporate documents are the source of truth. Legacy ``procedimentos`` records
remain readable for backwards compatibility, but are never copied into the
corporate documents collection.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional
import unicodedata


CORPORATE_SOURCE = "biblioteca_corporativa"
LEGACY_SOURCE = "procedimento_legado"
EDITOR_ROLES = {"master", "admin", "pcm"}
FIELD_ROLES = {"tecnico", "tec_mecanico", "tec_eletrico", "instrumentista", "lubrificador", "inspetor", "operador"}
PUBLISHED_STATUSES = {"publicado", "aprovado"}
ARCHIVED_STATUSES = {"arquivado", "obsoleto", "inativo"}


def scalar_value(value: Any) -> str:
    """Return a stable string for legacy fields that may contain an object."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("value", "id", "key", "slug", "name", "nome", "label", "type", "tipo", "status"):
            if key in value:
                resolved = scalar_value(value.get(key))
                if resolved:
                    return resolved
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(filter(None, (scalar_value(item) for item in value)))
    return str(value).strip()


def normalized_token(value: Any) -> str:
    text = scalar_value(value).casefold()
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )
    return "_".join(text.replace("-", " ").replace("/", " ").split())


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, (list, tuple, set)) else [value]
    return [resolved for item in values if (resolved := scalar_value(item))]


def normalized_status(value: Any) -> str:
    status = normalized_token(value)
    aliases = {
        "published": "publicado",
        "active": "aprovado",
        "ativo": "aprovado",
        "approved": "aprovado",
        "draft": "rascunho",
        "in_review": "em_revisao",
        "em_revisao": "em_revisao",
        "archived": "arquivado",
        "obsolete": "obsoleto",
        "inactive": "inativo",
    }
    return aliases.get(status, status or "rascunho")


def boolean_value(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return normalized_token(value) not in {"false", "0", "nao", "no", "inativo", "inactive"}
    return bool(value)


def is_corporate_procedure(document: Dict) -> bool:
    candidates = (
        document.get("document_type"),
        document.get("type"),
        document.get("tipo"),
        document.get("category"),
        document.get("categoria"),
    )
    return any(
        normalized_token(value).startswith(("procedimento", "procedure"))
        for value in candidates
        if scalar_value(value)
    )


def can_view_document_security(document: Dict, user: Dict) -> bool:
    role = normalized_token(user.get("role"))
    allowed_roles = document.get("allowed_roles") or document.get("permitted_roles")
    explicitly_allowed = False
    if allowed_roles:
        if isinstance(allowed_roles, str):
            allowed_roles = [allowed_roles]
        normalized_roles = {normalized_token(item) for item in allowed_roles}
        if role not in normalized_roles and role not in EDITOR_ROLES:
            return False
        explicitly_allowed = role in normalized_roles

    classification = normalized_token(
        document.get("security_classification")
        or document.get("access_level")
        or document.get("visibility")
    )
    if classification in {"restrito", "restricted"} and role not in EDITOR_ROLES and not explicitly_allowed:
        return False

    return True


def can_view_corporate_document(document: Dict, user: Dict) -> bool:
    """Apply tenant-independent visibility rules after the DB org filter."""
    role = normalized_token(user.get("role"))
    status = normalized_status(document.get("status"))
    active = boolean_value(document.get("is_active"), True)

    # Field users only receive current published documents.
    if role in FIELD_ROLES and (status != "publicado" or not active):
        return False

    return can_view_document_security(document, user)


def normalize_corporate_procedure(document: Dict) -> Dict:
    status = normalized_status(document.get("status"))
    return {
        "id": document.get("id"),
        "source": CORPORATE_SOURCE,
        "codigo": scalar_value(document.get("code")),
        "nome": scalar_value(document.get("title")),
        "descricao": scalar_value(document.get("description")),
        "revisao": scalar_value(document.get("revision")) or "01",
        "versao": document.get("version") or 1,
        "status": status,
        "is_active": boolean_value(document.get("is_active"), True),
        "document_type": scalar_value(document.get("document_type") or document.get("type")),
        "category": scalar_value(document.get("category")),
        "discipline": scalar_value(document.get("discipline")),
        "department": scalar_value(document.get("department")),
        "areas": string_list(document.get("applicable_areas")),
        "asset_types": string_list(document.get("applicable_asset_types")),
        "asset_ids": string_list(document.get("applicable_asset_ids")),
        "tags": string_list(document.get("tags")),
        "safety_document": bool(document.get("safety_document", False)),
        "requires_acknowledgement": bool(document.get("requires_acknowledgement", False)),
        "content": document.get("content") or "",
        "file_url": document.get("file_url"),
        "file_name": document.get("file_name"),
        "file_type": document.get("file_type"),
        "file_size": document.get("file_size"),
        "effective_date": document.get("effective_date"),
        "expiration_date": document.get("expiration_date"),
        "published_at": document.get("published_at") or (
            document.get("updated_at") if status == "publicado" else None
        ),
        "updated_at": document.get("updated_at"),
        "created_at": document.get("created_at"),
        "responsavel": (
            document.get("responsible_name")
            or document.get("owner_name")
            or document.get("updated_by_name")
            or document.get("created_by_name")
            or document.get("updated_by")
            or document.get("created_by")
        ),
        "tempo_estimado_minutos": None,
        "observacoes": "",
        "etapas": [],
    }


def normalize_legacy_procedure(document: Dict) -> Dict:
    normalized = {
        key: value for key, value in document.items()
        if key not in {"_id", "organization_id", "deleted_at", "deleted_by"}
    }
    normalized.update({
        "id": document.get("id"),
        "source": LEGACY_SOURCE,
        "codigo": scalar_value(document.get("codigo") or document.get("code")),
        "nome": scalar_value(document.get("nome") or document.get("title")),
        "descricao": scalar_value(document.get("descricao") or document.get("description")),
        "revisao": scalar_value(document.get("revisao") or document.get("revision")) or "01",
        "versao": document.get("versao") or document.get("version") or 1,
        "status": normalized_status(document.get("status")),
        "is_active": boolean_value(document.get("is_active"), True),
        "document_type": scalar_value(document.get("document_type") or document.get("tipo")) or "procedimento_legado",
        "discipline": scalar_value(document.get("discipline") or document.get("disciplina")),
        "areas": string_list(document.get("areas") or document.get("applicable_areas")),
        "asset_types": string_list(document.get("asset_types") or document.get("applicable_asset_types")),
        "tags": string_list(document.get("tags")),
        "safety_document": bool(document.get("safety_document", False)),
        "content": document.get("content") or "",
        "file_url": document.get("file_url"),
        "file_name": document.get("file_name"),
        "published_at": document.get("published_at") or document.get("updated_at"),
        "updated_at": document.get("updated_at"),
        "created_at": document.get("created_at"),
        "responsavel": document.get("updated_by_name") or document.get("created_by_name") or document.get("created_by"),
        "etapas": document.get("etapas") or [],
    })
    return normalized


def is_published_active(item: Dict) -> bool:
    return normalized_status(item.get("status")) in PUBLISHED_STATUSES and boolean_value(item.get("is_active"), True)


def can_view_legacy_procedure(document: Dict, user: Dict) -> bool:
    role = normalized_token(user.get("role"))
    if role in FIELD_ROLES:
        return is_published_active(normalize_legacy_procedure(document))
    return True


def matches_status(item: Dict, requested_status: Optional[str]) -> bool:
    requested = normalized_status(requested_status) if requested_status else ""
    if not requested:
        return is_published_active(item)
    if requested == "todos":
        return True
    if requested == "publicado":
        return is_published_active(item)
    return normalized_status(item.get("status")) == requested


def matches_search(item: Dict, search: Optional[str]) -> bool:
    query = normalized_token(search)
    if not query:
        return True
    values: Iterable[Any] = (
        item.get("nome"),
        item.get("codigo"),
        item.get("document_type"),
        item.get("discipline"),
        item.get("department"),
        item.get("areas"),
        item.get("asset_types"),
        item.get("tags"),
        item.get("descricao"),
    )
    return query in normalized_token(list(values))


def linked_corporate_id(document: Dict) -> str:
    for key in ("document_id", "library_item_id", "source_id", "corporate_document_id"):
        value = scalar_value(document.get(key))
        if value:
            return value
    return ""


async def build_procedure_catalog(
    database,
    org_id: str,
    user: Dict,
    *,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> Dict:
    """Build a tenant-scoped catalog without persisting or duplicating data."""
    corporate_docs = await database.documentos_corporativos.find(
        {"organization_id": org_id, "deleted_at": None},
        {"_id": 0},
    ).to_list(1000)
    legacy_docs = await database.procedimentos.find(
        {"organization_id": org_id, "deleted_at": None},
        {"_id": 0},
    ).to_list(1000)

    corporate_procedure_docs = [
        document for document in corporate_docs
        if is_corporate_procedure(document)
    ]
    corporate_ids = {
        document.get("id") for document in corporate_procedure_docs
        if document.get("id")
    }
    corporate = [
        normalize_corporate_procedure(document)
        for document in corporate_procedure_docs
        if can_view_corporate_document(document, user)
    ]

    legacy = []
    for document in legacy_docs:
        legacy_id = document.get("id")
        source_id = linked_corporate_id(document)
        if legacy_id in corporate_ids or (source_id and source_id in corporate_ids):
            continue
        if not can_view_legacy_procedure(document, user):
            continue
        legacy.append(normalize_legacy_procedure(document))

    all_items = corporate + legacy
    filtered = [
        item for item in all_items
        if matches_status(item, status) and matches_search(item, search)
    ]
    filtered.sort(
        key=lambda item: (
            scalar_value(item.get("updated_at") or item.get("created_at")),
            scalar_value(item.get("nome")),
        ),
        reverse=True,
    )

    status_counts: Dict[str, int] = {}
    for item in all_items:
        item_status = normalized_status(item.get("status"))
        status_counts[item_status] = status_counts.get(item_status, 0) + 1

    return {
        "items": filtered,
        "totals": {
            "total": len(all_items),
            "published": sum(1 for item in all_items if is_published_active(item)),
            "draft": sum(1 for item in all_items if normalized_status(item.get("status")) in {"rascunho", "em_revisao"}),
            "archived": sum(1 for item in all_items if normalized_status(item.get("status")) in ARCHIVED_STATUSES),
            "filtered": len(filtered),
            "corporate": len(corporate),
            "legacy": len(legacy),
            "by_status": status_counts,
        },
    }


async def find_active_procedure(database, proc_id: str, org_id: str, user: Optional[Dict] = None) -> Optional[Dict]:
    """Resolve an active procedure ID from either source, preferring corporate."""
    corporate = await database.documentos_corporativos.find_one(
        {
            "id": proc_id,
            "organization_id": org_id,
            "deleted_at": None,
            "status": "publicado",
            "is_active": True,
        },
        {"_id": 0},
    )
    if (
        corporate
        and is_corporate_procedure(corporate)
        and (not user or can_view_document_security(corporate, user))
    ):
        return normalize_corporate_procedure(corporate)

    legacy = await database.procedimentos.find_one(
        {
            "id": proc_id,
            "organization_id": org_id,
            "deleted_at": None,
            "status": "aprovado",
        },
        {"_id": 0},
    )
    return normalize_legacy_procedure(legacy) if legacy else None


async def find_procedure(database, proc_id: str, org_id: str, user: Optional[Dict] = None) -> Optional[Dict]:
    """Resolve a procedure for historical reads, including archived records."""
    corporate = await database.documentos_corporativos.find_one(
        {"id": proc_id, "organization_id": org_id, "deleted_at": None},
        {"_id": 0},
    )
    if (
        corporate
        and is_corporate_procedure(corporate)
        and (not user or can_view_document_security(corporate, user))
    ):
        return normalize_corporate_procedure(corporate)

    legacy = await database.procedimentos.find_one(
        {"id": proc_id, "organization_id": org_id, "deleted_at": None},
        {"_id": 0},
    )
    return normalize_legacy_procedure(legacy) if legacy else None
