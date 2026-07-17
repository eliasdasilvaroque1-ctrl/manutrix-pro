"""MAINTRIX RC Visual Constructor - Wave 1
Tests for LayoutDocumento with blocks[], validators, publish/duplicate/preview endpoints.
Run: cd /app/backend && python -m pytest tests/test_rc_visual_wave1.py -v
"""
import pytest
import httpx
import os
import time
import uuid

BASE = os.environ.get("TEST_API_URL", "https://procure-manutrix.preview.emergentagent.com")
API = f"{BASE}/api"
ORG = "9a232bf2-fc01-4253-813f-8df356be31c1"

USERS = {
    "master": ("master@maintrix.com", "master123"),
    "pcm": ("test.pcm@maintrix.com", "pcm123"),
    "tecnico": ("test.mec@maintrix.com", "tec123"),
}

_token_cache = {}


def get_token(role):
    if role in _token_cache:
        return _token_cache[role]
    email, pwd = USERS[role]
    payload = {"email": email, "password": pwd}
    if role == "master":
        payload["organization_id"] = ORG
    r = httpx.post(f"{API}/auth/login", json=payload, timeout=30)
    assert r.status_code == 200, f"Login {role} failed: {r.text}"
    _token_cache[role] = r.json()["access_token"]
    return _token_cache[role]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# Track for cleanup
_created_layouts = []


def _new_layout_payload(nome=None, tipo="os_corretiva", blocks=None):
    if blocks is None:
        blocks = [
            {"type": "header", "order": 0, "visible": True, "settings": {}},
            {"type": "equipment", "order": 1, "visible": True, "settings": {}},
            {"type": "description", "order": 2, "visible": True, "settings": {}},
            {"type": "footer", "order": 3, "visible": True, "settings": {}},
        ]
    return {
        "nome": nome or f"WV1_LAY_{uuid.uuid4().hex[:6]}",
        "tipo_documento": tipo,
        "orientacao": "retrato",
        "tamanho_pagina": "A4",
        "schema_version": 1,
        "blocks": blocks,
    }


# ============== 1. CREATE LAYOUT WITH BLOCKS ==============

class TestCreateLayoutBlocks:
    def test_create_layout_with_blocks(self):
        token = get_token("master")
        payload = _new_layout_payload()
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("status") == "created"
        assert "id" in data
        _created_layouts.append(data["id"])
        # Verify GET
        r = httpx.get(f"{API}/doc-config/layouts/{data['id']}", headers=auth(token), timeout=30)
        assert r.status_code == 200
        doc = r.json()
        assert doc.get("schema_version") == 1
        assert len(doc.get("blocks", [])) == 4
        # Auto-assigned block IDs
        for b in doc["blocks"]:
            assert b.get("id"), "Block id should be auto-generated"
            assert b.get("type") in ("header", "equipment", "description", "footer")


# ============== 2. BLOCK VALIDATION ==============

class TestBlockValidation:
    def test_invalid_block_type(self):
        token = get_token("master")
        payload = _new_layout_payload(blocks=[
            {"type": "not_a_real_type", "order": 0, "visible": True, "settings": {}},
        ])
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token), json=payload, timeout=30)
        assert r.status_code == 422, f"expected 422 got {r.status_code}: {r.text}"

    def test_duplicate_block_ids(self):
        token = get_token("master")
        dup_id = str(uuid.uuid4())
        payload = _new_layout_payload(blocks=[
            {"id": dup_id, "type": "equipment", "order": 0, "visible": True, "settings": {}},
            {"id": dup_id, "type": "description", "order": 1, "visible": True, "settings": {}},
        ])
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token), json=payload, timeout=30)
        assert r.status_code == 422, f"expected 422 got {r.status_code}: {r.text}"

    def test_max_one_header(self):
        token = get_token("master")
        payload = _new_layout_payload(blocks=[
            {"type": "header", "order": 0, "visible": True, "settings": {}},
            {"type": "header", "order": 1, "visible": True, "settings": {}},
        ])
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token), json=payload, timeout=30)
        assert r.status_code == 422, f"expected 422 got {r.status_code}: {r.text}"

    def test_max_one_footer(self):
        token = get_token("master")
        payload = _new_layout_payload(blocks=[
            {"type": "footer", "order": 0, "visible": True, "settings": {}},
            {"type": "footer", "order": 1, "visible": True, "settings": {}},
        ])
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token), json=payload, timeout=30)
        assert r.status_code == 422, r.text


# ============== 3. PUBLICATION FLOW ==============

class TestPublicationFlow:
    def test_publish_layout(self):
        token = get_token("master")
        # Create tipo_documento unique for isolation
        tipo = f"os_test_{uuid.uuid4().hex[:6]}"
        p = _new_layout_payload(tipo=tipo)
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token), json=p, timeout=30)
        assert r.status_code == 200
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        r = httpx.post(f"{API}/doc-config/layouts/{lay_id}/publicar", headers=auth(token), timeout=30)
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "published"
        # Verify status
        r = httpx.get(f"{API}/doc-config/layouts/{lay_id}", headers=auth(token), timeout=30)
        assert r.json().get("publication_status") == "publicado"

    def test_publish_deactivates_others_same_tipo(self):
        token = get_token("master")
        tipo = f"os_wv1_{uuid.uuid4().hex[:6]}"
        # Create first + publish
        r1 = httpx.post(f"{API}/doc-config/layouts", headers=auth(token),
                        json=_new_layout_payload(tipo=tipo), timeout=30)
        id1 = r1.json()["id"]
        _created_layouts.append(id1)
        httpx.post(f"{API}/doc-config/layouts/{id1}/publicar", headers=auth(token), timeout=30)
        # Create second + publish
        r2 = httpx.post(f"{API}/doc-config/layouts", headers=auth(token),
                        json=_new_layout_payload(tipo=tipo), timeout=30)
        id2 = r2.json()["id"]
        _created_layouts.append(id2)
        r = httpx.post(f"{API}/doc-config/layouts/{id2}/publicar", headers=auth(token), timeout=30)
        assert r.status_code == 200
        # First should now be inativo
        r = httpx.get(f"{API}/doc-config/layouts/{id1}", headers=auth(token), timeout=30)
        assert r.json().get("publication_status") == "inativo", \
            f"Expected id1 to be inativo, got {r.json().get('publication_status')}"
        r = httpx.get(f"{API}/doc-config/layouts/{id2}", headers=auth(token), timeout=30)
        assert r.json().get("publication_status") == "publicado"

    def test_publish_already_published_fails(self):
        token = get_token("master")
        tipo = f"os_pub2_{uuid.uuid4().hex[:6]}"
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token),
                       json=_new_layout_payload(tipo=tipo), timeout=30)
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        httpx.post(f"{API}/doc-config/layouts/{lay_id}/publicar", headers=auth(token), timeout=30)
        r = httpx.post(f"{API}/doc-config/layouts/{lay_id}/publicar", headers=auth(token), timeout=30)
        assert r.status_code == 400


# ============== 4. DUPLICATE LAYOUT ==============

class TestDuplicateLayout:
    def test_duplicate_creates_draft_new_block_ids(self):
        token = get_token("master")
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token),
                       json=_new_layout_payload(), timeout=30)
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        # Publish so source is not rascunho
        httpx.post(f"{API}/doc-config/layouts/{lay_id}/publicar", headers=auth(token), timeout=30)
        # Duplicate
        r = httpx.post(f"{API}/doc-config/layouts/{lay_id}/duplicar", headers=auth(token), timeout=30)
        assert r.status_code == 200, r.text
        new_id = r.json()["id"]
        _created_layouts.append(new_id)
        # Verify dup is rascunho
        r = httpx.get(f"{API}/doc-config/layouts/{new_id}", headers=auth(token), timeout=30)
        dup = r.json()
        assert dup.get("publication_status") == "rascunho"
        assert "(Cópia)" in dup.get("nome", "")
        # Verify original blocks fetched
        r = httpx.get(f"{API}/doc-config/layouts/{lay_id}", headers=auth(token), timeout=30)
        orig_blocks = r.json().get("blocks", [])
        dup_blocks = dup.get("blocks", [])
        assert len(orig_blocks) == len(dup_blocks) > 0
        orig_ids = {b["id"] for b in orig_blocks}
        dup_ids = {b["id"] for b in dup_blocks}
        assert orig_ids.isdisjoint(dup_ids), "Duplicate should have new block IDs"


# ============== 5. PREVIEW DATA ==============

class TestPreviewData:
    def test_preview_data_returns_resolved_blocks(self):
        token = get_token("master")
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token),
                       json=_new_layout_payload(), timeout=30)
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        r = httpx.get(f"{API}/doc-config/layouts/{lay_id}/preview-data",
                      headers=auth(token), timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "layout" in data
        assert "resolved_blocks" in data
        assert len(data["resolved_blocks"]) == 4


# ============== 6. GET PUBLISHED ==============

class TestGetPublished:
    def test_get_published_layout(self):
        token = get_token("master")
        tipo = f"os_gp_{uuid.uuid4().hex[:6]}"
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token),
                       json=_new_layout_payload(tipo=tipo), timeout=30)
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        httpx.post(f"{API}/doc-config/layouts/{lay_id}/publicar", headers=auth(token), timeout=30)
        r = httpx.get(f"{API}/doc-config/layouts/publicado/{tipo}", headers=auth(token), timeout=30)
        assert r.status_code == 200
        pub = r.json()
        assert pub is not None
        assert pub.get("id") == lay_id
        assert pub.get("publication_status") == "publicado"

    def test_get_published_none_for_unknown_tipo(self):
        token = get_token("master")
        r = httpx.get(f"{API}/doc-config/layouts/publicado/absolutely_no_such_tipo_xyz",
                      headers=auth(token), timeout=30)
        assert r.status_code == 200
        assert r.json() is None


# ============== 7. VERSIONING ==============

class TestVersioning:
    def test_versioning_and_list_versions(self):
        token = get_token("master")
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token),
                       json=_new_layout_payload(), timeout=30)
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        # Update to v2
        p2 = _new_layout_payload()
        p2["motivo_alteracao"] = "Added new block"
        p2["blocks"].append({"type": "safety", "order": 4, "visible": True, "settings": {}})
        r = httpx.put(f"{API}/doc-config/layouts/{lay_id}", headers=auth(token), json=p2, timeout=30)
        assert r.status_code == 200
        assert r.json().get("versao") == 2
        # List versions
        r = httpx.get(f"{API}/doc-config/layouts/{lay_id}/versoes", headers=auth(token), timeout=30)
        assert r.status_code == 200
        versions = r.json()
        assert len(versions) >= 2


# ============== 8. RESTORE ==============

class TestRestore:
    def test_restore_v1_creates_v3(self):
        token = get_token("master")
        p1 = _new_layout_payload()
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token), json=p1, timeout=30)
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        # Update v2
        p2 = _new_layout_payload()
        p2["motivo_alteracao"] = "v2"
        p2["blocks"] = [{"type": "equipment", "order": 0, "visible": True, "settings": {}}]
        r = httpx.put(f"{API}/doc-config/layouts/{lay_id}", headers=auth(token), json=p2, timeout=30)
        assert r.status_code == 200
        # Restore v1
        r = httpx.post(f"{API}/doc-config/layouts/{lay_id}/restaurar/1?motivo=rollback",
                       headers=auth(token), timeout=30)
        assert r.status_code == 200, r.text
        assert r.json().get("nova_versao") == 3
        # Verify v3 has v1's blocks
        r = httpx.get(f"{API}/doc-config/layouts/{lay_id}", headers=auth(token), timeout=30)
        cur = r.json()
        assert cur.get("versao") == 3
        assert len(cur.get("blocks", [])) == 4  # v1 had 4 blocks


# ============== 9. RBAC ==============

class TestRBAC:
    def test_tecnico_cannot_create(self):
        token = get_token("tecnico")
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token),
                       json=_new_layout_payload(), timeout=30)
        assert r.status_code == 403

    def test_tecnico_cannot_update(self):
        token_m = get_token("master")
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token_m),
                       json=_new_layout_payload(), timeout=30)
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        token = get_token("tecnico")
        r = httpx.put(f"{API}/doc-config/layouts/{lay_id}", headers=auth(token),
                      json=_new_layout_payload(), timeout=30)
        assert r.status_code == 403

    def test_tecnico_cannot_publish(self):
        token_m = get_token("master")
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token_m),
                       json=_new_layout_payload(), timeout=30)
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        token = get_token("tecnico")
        r = httpx.post(f"{API}/doc-config/layouts/{lay_id}/publicar", headers=auth(token), timeout=30)
        assert r.status_code == 403

    def test_tecnico_cannot_delete(self):
        token_m = get_token("master")
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token_m),
                       json=_new_layout_payload(), timeout=30)
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        token = get_token("tecnico")
        r = httpx.delete(f"{API}/doc-config/layouts/{lay_id}", headers=auth(token), timeout=30)
        assert r.status_code == 403

    def test_tecnico_cannot_duplicate(self):
        token_m = get_token("master")
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token_m),
                       json=_new_layout_payload(), timeout=30)
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        token = get_token("tecnico")
        r = httpx.post(f"{API}/doc-config/layouts/{lay_id}/duplicar", headers=auth(token), timeout=30)
        assert r.status_code == 403

    def test_tecnico_can_read_layouts(self):
        token = get_token("tecnico")
        r = httpx.get(f"{API}/doc-config/layouts", headers=auth(token), timeout=30)
        assert r.status_code == 200


# ============== 10. CROSS-TENANT ==============

class TestCrossTenant:
    def test_publish_with_invalid_library_ref_blocked(self):
        token = get_token("master")
        # Reference an id that does NOT exist for this org
        fake_ref = str(uuid.uuid4())
        p = _new_layout_payload(blocks=[
            {"type": "procedure", "order": 0, "visible": True, "settings": {},
             "library_ref_id": fake_ref, "library_ref_type": "procedimentos_padrao"},
        ])
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token), json=p, timeout=30)
        assert r.status_code == 200
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        r = httpx.post(f"{API}/doc-config/layouts/{lay_id}/publicar", headers=auth(token), timeout=30)
        assert r.status_code == 400, f"Expected 400 for invalid ref, got {r.status_code}: {r.text}"
        assert "referência" in r.json().get("detail", "").lower() or "referencia" in r.json().get("detail", "").lower() or "empresa" in r.json().get("detail", "").lower()


# ============== 11. BACKWARD COMPAT ==============

class TestBackwardCompat:
    def test_old_layout_without_blocks_still_works(self):
        token = get_token("master")
        # Create layout with no blocks
        p = _new_layout_payload(blocks=[])
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token), json=p, timeout=30)
        assert r.status_code == 200
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        r = httpx.get(f"{API}/doc-config/layouts/{lay_id}", headers=auth(token), timeout=30)
        assert r.status_code == 200
        assert r.json().get("blocks") == []

    def test_os_without_layout_generates_pdf(self):
        token = get_token("master")
        # Get an existing OS
        r = httpx.get(f"{API}/ordens-servico?status=programada", headers=auth(token), timeout=30)
        items = r.json() if isinstance(r.json(), list) else []
        if items:
            os_id = items[0]["id"]
            r = httpx.get(f"{API}/ordens-servico/{os_id}/pdf", headers=auth(token), timeout=60)
            assert r.status_code == 200


# ============== 12. 50-BLOCK STRESS ==============

class TestStress:
    def test_50_blocks_created(self):
        token = get_token("master")
        # 50 blocks: 1 header + 48 mixed + 1 footer
        types_cycle = ["equipment", "info", "description", "team", "dates",
                       "procedure", "safety", "checklist", "photos", "materials",
                       "indicators", "history", "custom_fields", "free_text",
                       "separator", "page_break", "observations"]
        blocks = [{"type": "header", "order": 0, "visible": True, "settings": {}}]
        for i in range(48):
            blocks.append({"type": types_cycle[i % len(types_cycle)],
                          "order": i + 1, "visible": True, "settings": {}})
        blocks.append({"type": "footer", "order": 49, "visible": True, "settings": {}})
        p = _new_layout_payload(blocks=blocks)
        start = time.time()
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth(token), json=p, timeout=30)
        elapsed = time.time() - start
        assert r.status_code == 200, r.text
        lay_id = r.json()["id"]
        _created_layouts.append(lay_id)
        assert elapsed < 3.0, f"Create 50-block layout took {elapsed:.2f}s (>3s)"
        r = httpx.get(f"{API}/doc-config/layouts/{lay_id}", headers=auth(token), timeout=30)
        assert r.status_code == 200
        assert len(r.json().get("blocks", [])) == 50


# ============== CLEANUP ==============

@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    token = get_token("master")
    for lid in _created_layouts:
        try:
            httpx.delete(f"{API}/doc-config/layouts/{lid}", headers=auth(token), timeout=15)
        except Exception:
            pass
