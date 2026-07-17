"""MAINTRIX Sprint 2 — Biblioteca Corporativa (Checklists / Modelos Inspecao / Modelos OS)
Coverage:
- CRUD + auto-versioning (create → v1, update → v2, ...)
- List versions descending
- Restore old version (increments version number)
- Auto-snapshot: setting *_id populates *_snapshot from library
- Snapshot isolation: updates in the source library do NOT change already-snapshotted references
- RBAC: tecnico blocked (403), pcm allowed, master allowed
- Soft-delete with archive
"""
import pytest
import httpx
import os
import uuid

BASE = os.environ.get("TEST_API_URL", "https://procure-manutrix.preview.emergentagent.com")
API = f"{BASE}/api"
ORG = "9a232bf2-fc01-4253-813f-8df356be31c1"

USERS = {
    "master": ("master@maintrix.com", "master123"),
    "admin": ("test.admin@maintrix.com", "admin123"),
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


def auth(role):
    return {"Authorization": f"Bearer {get_token(role)}"}


# ============== LOGIN SMOKE ==============

class TestLogin:
    def test_all_logins(self):
        for role in USERS:
            assert get_token(role)


# ============== CHECKLISTS FULL LIFECYCLE ==============

class TestChecklistsCRUD:
    _cl_id = None

    def test_01_create_v1_with_items(self):
        payload = {
            "nome": f"TEST_CL_{uuid.uuid4().hex[:8]}",
            "descricao": "Checklist teste sprint2",
            "disciplina": "mecanica",
            "categoria": "inspecao_rotina",
            "itens": [
                {"descricao": "Verificar vibracao", "tipo": "medida", "tolerancia_min": 0, "tolerancia_max": 5.5, "unidade": "mm/s", "obrigatorio": True, "ordem": 1},
                {"descricao": "Verificar limpeza", "tipo": "sim_nao", "obrigatorio": True, "ordem": 2},
            ],
        }
        r = httpx.post(f"{API}/doc-config/checklists", headers=auth("master"), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["versao"] == 1
        assert data["status"] == "created"
        TestChecklistsCRUD._cl_id = data["id"]

        # Verify v1 in archive
        v = httpx.get(f"{API}/doc-config/checklists/{data['id']}/versoes", headers=auth("master"), timeout=30)
        assert v.status_code == 200
        versions = v.json()
        assert len(versions) == 1
        assert versions[0]["versao"] == 1
        assert versions[0]["motivo"] == "Criação inicial"
        snap = versions[0]["snapshot"]
        assert snap["nome"].startswith("TEST_CL_")
        assert len(snap["itens"]) == 2
        assert snap["itens"][0]["tolerancia_max"] == 5.5

    def test_02_get_item(self):
        cid = TestChecklistsCRUD._cl_id
        r = httpx.get(f"{API}/doc-config/checklists/{cid}", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        item = r.json()
        assert item["id"] == cid
        assert item["versao"] == 1
        assert "_id" not in item

    def test_03_update_to_v2(self):
        cid = TestChecklistsCRUD._cl_id
        payload = {
            "nome": "TEST_CL_v2",
            "disciplina": "mecanica",
            "itens": [
                {"descricao": "Item atualizado", "tipo": "sim_nao", "obrigatorio": True, "ordem": 1},
            ],
            "motivo_alteracao": "Revisao para v2",
        }
        r = httpx.put(f"{API}/doc-config/checklists/{cid}", headers=auth("master"), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["versao"] == 2

        # Verify motivo persisted in archive
        v = httpx.get(f"{API}/doc-config/checklists/{cid}/versoes", headers=auth("master"), timeout=30).json()
        v2 = [x for x in v if x["versao"] == 2][0]
        assert "v2" in (v2.get("motivo") or "").lower() or "Revisao" in (v2.get("motivo") or "")

    def test_04_update_to_v3(self):
        cid = TestChecklistsCRUD._cl_id
        r = httpx.put(f"{API}/doc-config/checklists/{cid}", headers=auth("master"),
                      json={"nome": "TEST_CL_v3", "itens": [], "motivo_alteracao": "v3"}, timeout=30)
        assert r.status_code == 200
        assert r.json()["versao"] == 3

    def test_05_list_versions_desc(self):
        cid = TestChecklistsCRUD._cl_id
        r = httpx.get(f"{API}/doc-config/checklists/{cid}/versoes", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        versions = r.json()
        assert [v["versao"] for v in versions] == [3, 2, 1]
        for v in versions:
            assert "snapshot" in v and isinstance(v["snapshot"], dict)

    def test_06_restore_v1_creates_v4(self):
        cid = TestChecklistsCRUD._cl_id
        r = httpx.post(f"{API}/doc-config/checklists/{cid}/restaurar/1",
                       headers=auth("master"), params={"motivo": "voltar ao inicial"}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["nova_versao"] == 4
        assert data["versao_restaurada"] == 1

        # Current state should have 2 itens (from v1)
        item = httpx.get(f"{API}/doc-config/checklists/{cid}", headers=auth("master"), timeout=30).json()
        assert item["versao"] == 4
        assert len(item["itens"]) == 2

    def test_07_soft_delete(self):
        cid = TestChecklistsCRUD._cl_id
        r = httpx.delete(f"{API}/doc-config/checklists/{cid}", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        # Archive should have a "Exclusão" motivo entry
        v = httpx.get(f"{API}/doc-config/checklists/{cid}/versoes", headers=auth("master"), timeout=30).json()
        motivos = [x.get("motivo") for x in v]
        assert any("Exclus" in (m or "") for m in motivos), f"Delete not archived: {motivos}"
        # Item should be gone from list
        lst = httpx.get(f"{API}/doc-config/checklists", headers=auth("master"), timeout=30).json()
        assert not any(x["id"] == cid for x in lst)
        # GET should 404
        g = httpx.get(f"{API}/doc-config/checklists/{cid}", headers=auth("master"), timeout=30)
        assert g.status_code == 404


# ============== MODELOS INSPECAO + AUTO-SNAPSHOT + ISOLATION ==============

class TestModelosInspecao:
    _mi_id = None
    _src_cl_id = None

    def test_01_seed_source_checklist(self):
        r = httpx.post(f"{API}/doc-config/checklists", headers=auth("master"), json={
            "nome": f"TEST_SRC_CL_{uuid.uuid4().hex[:6]}",
            "itens": [{"descricao": "item original v1", "tipo": "sim_nao", "ordem": 1}],
        }, timeout=30)
        assert r.status_code == 200
        TestModelosInspecao._src_cl_id = r.json()["id"]

    def test_02_create_mi_with_auto_snapshot(self):
        cl_id = TestModelosInspecao._src_cl_id
        payload = {
            "nome": f"TEST_MI_{uuid.uuid4().hex[:8]}",
            "tipo": "inspecao_rotina",
            "disciplina": "mecanica",
            "checklist_id": cl_id,
            # Note: NO checklist_snapshot passed — must be auto-resolved by backend
        }
        r = httpx.post(f"{API}/doc-config/modelos-inspecao", headers=auth("master"), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["versao"] == 1
        TestModelosInspecao._mi_id = data["id"]

        # Verify snapshot auto-populated
        mi = httpx.get(f"{API}/doc-config/modelos-inspecao/{data['id']}", headers=auth("master"), timeout=30).json()
        assert mi.get("checklist_id") == cl_id
        assert mi.get("checklist_snapshot") is not None, "auto-snapshot failed"
        assert mi["checklist_snapshot"].get("nome", "").startswith("TEST_SRC_CL_")
        assert mi["checklist_snapshot"]["itens"][0]["descricao"] == "item original v1"

    def test_03_snapshot_isolation_after_source_update(self):
        """CRITICAL: When source checklist is updated, the MI's snapshot must NOT change."""
        cl_id = TestModelosInspecao._src_cl_id
        mi_id = TestModelosInspecao._mi_id

        # Update source checklist → v2 with different item
        upd = httpx.put(f"{API}/doc-config/checklists/{cl_id}", headers=auth("master"), json={
            "nome": "TEST_SRC_CL_UPDATED",
            "itens": [{"descricao": "ITEM MUTATED V2", "tipo": "sim_nao", "ordem": 1}],
            "motivo_alteracao": "mutation test",
        }, timeout=30)
        assert upd.status_code == 200
        assert upd.json()["versao"] == 2

        # MI's snapshot must still hold ORIGINAL v1 data
        mi = httpx.get(f"{API}/doc-config/modelos-inspecao/{mi_id}", headers=auth("master"), timeout=30).json()
        assert mi["checklist_snapshot"]["itens"][0]["descricao"] == "item original v1", \
            f"SNAPSHOT LEAKED! got: {mi['checklist_snapshot']['itens']}"
        # Source name in snapshot should be original (starts with TEST_SRC_CL_)
        assert "UPDATED" not in mi["checklist_snapshot"].get("nome", "")

    def test_04_update_mi_to_v2(self):
        mi_id = TestModelosInspecao._mi_id
        r = httpx.put(f"{API}/doc-config/modelos-inspecao/{mi_id}", headers=auth("master"), json={
            "nome": "TEST_MI_v2",
            "campos_obrigatorios": ["hora_inicio"],
            "motivo_alteracao": "MI v2",
        }, timeout=30)
        assert r.status_code == 200
        assert r.json()["versao"] == 2

    def test_05_list_mi_versions(self):
        mi_id = TestModelosInspecao._mi_id
        r = httpx.get(f"{API}/doc-config/modelos-inspecao/{mi_id}/versoes", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        vs = r.json()
        assert len(vs) == 2
        assert [v["versao"] for v in vs] == [2, 1]

    def test_06_restore_mi_v1(self):
        mi_id = TestModelosInspecao._mi_id
        r = httpx.post(f"{API}/doc-config/modelos-inspecao/{mi_id}/restaurar/1",
                       headers=auth("master"), timeout=30)
        assert r.status_code == 200
        assert r.json()["nova_versao"] == 3


# ============== MODELOS OS FULL FLOW ==============

class TestModelosOS:
    _mo_id = None

    def test_01_create_mo_v1(self):
        payload = {
            "nome": f"TEST_MO_{uuid.uuid4().hex[:8]}",
            "tipo_os": "preventiva",
            "disciplina": "eletrica",
            "prioridade_padrao": "alta",
        }
        r = httpx.post(f"{API}/doc-config/modelos-os", headers=auth("master"), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["versao"] == 1
        TestModelosOS._mo_id = data["id"]

    def test_02_update_mo_v2_v3(self):
        mo_id = TestModelosOS._mo_id
        for i, m in [(2, "v2"), (3, "v3")]:
            r = httpx.put(f"{API}/doc-config/modelos-os/{mo_id}", headers=auth("master"), json={
                "nome": f"TEST_MO_v{i}",
                "prioridade_padrao": "media",
                "motivo_alteracao": m,
            }, timeout=30)
            assert r.status_code == 200
            assert r.json()["versao"] == i

    def test_03_list_versions(self):
        mo_id = TestModelosOS._mo_id
        r = httpx.get(f"{API}/doc-config/modelos-os/{mo_id}/versoes", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        assert [v["versao"] for v in r.json()] == [3, 2, 1]

    def test_04_restore_v1(self):
        mo_id = TestModelosOS._mo_id
        r = httpx.post(f"{API}/doc-config/modelos-os/{mo_id}/restaurar/1", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        assert r.json()["nova_versao"] == 4

    def test_05_delete_archived(self):
        mo_id = TestModelosOS._mo_id
        r = httpx.delete(f"{API}/doc-config/modelos-os/{mo_id}", headers=auth("master"), timeout=30)
        assert r.status_code == 200


# ============== RBAC ==============

class TestRBAC:
    def test_tecnico_blocked_on_checklists_post(self):
        r = httpx.post(f"{API}/doc-config/checklists", headers=auth("tecnico"),
                       json={"nome": "TEST_SHOULD_FAIL"}, timeout=30)
        assert r.status_code == 403

    def test_tecnico_blocked_on_modelos_inspecao_post(self):
        r = httpx.post(f"{API}/doc-config/modelos-inspecao", headers=auth("tecnico"),
                       json={"nome": "TEST_SHOULD_FAIL"}, timeout=30)
        assert r.status_code == 403

    def test_tecnico_blocked_on_modelos_os_post(self):
        r = httpx.post(f"{API}/doc-config/modelos-os", headers=auth("tecnico"),
                       json={"nome": "TEST_SHOULD_FAIL"}, timeout=30)
        assert r.status_code == 403

    def test_tecnico_blocked_put_delete_and_restore(self):
        # master creates
        c = httpx.post(f"{API}/doc-config/checklists", headers=auth("master"),
                       json={"nome": "TEST_RBAC_CL"}, timeout=30)
        cid = c.json()["id"]

        assert httpx.put(f"{API}/doc-config/checklists/{cid}", headers=auth("tecnico"),
                         json={"nome": "hack"}, timeout=30).status_code == 403
        assert httpx.delete(f"{API}/doc-config/checklists/{cid}", headers=auth("tecnico"),
                            timeout=30).status_code == 403
        assert httpx.post(f"{API}/doc-config/checklists/{cid}/restaurar/1",
                          headers=auth("tecnico"), timeout=30).status_code == 403

    def test_pcm_can_create_checklists(self):
        r = httpx.post(f"{API}/doc-config/checklists", headers=auth("pcm"),
                       json={"nome": f"TEST_PCM_CL_{uuid.uuid4().hex[:6]}", "itens": []}, timeout=30)
        assert r.status_code == 200
        assert r.json()["versao"] == 1

    def test_pcm_can_create_modelos_inspecao(self):
        r = httpx.post(f"{API}/doc-config/modelos-inspecao", headers=auth("pcm"),
                       json={"nome": f"TEST_PCM_MI_{uuid.uuid4().hex[:6]}"}, timeout=30)
        assert r.status_code == 200

    def test_pcm_can_create_modelos_os(self):
        r = httpx.post(f"{API}/doc-config/modelos-os", headers=auth("pcm"),
                       json={"nome": f"TEST_PCM_MO_{uuid.uuid4().hex[:6]}"}, timeout=30)
        assert r.status_code == 200

    def test_pcm_can_update_and_restore(self):
        c = httpx.post(f"{API}/doc-config/checklists", headers=auth("pcm"),
                       json={"nome": "TEST_PCM_RESTORE"}, timeout=30)
        cid = c.json()["id"]
        u = httpx.put(f"{API}/doc-config/checklists/{cid}", headers=auth("pcm"),
                      json={"nome": "TEST_PCM_RESTORE_v2", "motivo_alteracao": "pcm"}, timeout=30)
        assert u.status_code == 200
        assert u.json()["versao"] == 2
        r = httpx.post(f"{API}/doc-config/checklists/{cid}/restaurar/1", headers=auth("pcm"), timeout=30)
        assert r.status_code == 200
        assert r.json()["nova_versao"] == 3


# ============== 404 EDGE CASES ==============

class TestEdgeCases:
    def test_get_nonexistent_checklist_404(self):
        r = httpx.get(f"{API}/doc-config/checklists/nonexistent-xyz",
                      headers=auth("master"), timeout=30)
        assert r.status_code == 404

    def test_restore_nonexistent_version_404(self):
        c = httpx.post(f"{API}/doc-config/checklists", headers=auth("master"),
                       json={"nome": "TEST_EDGE_RESTORE"}, timeout=30)
        cid = c.json()["id"]
        r = httpx.post(f"{API}/doc-config/checklists/{cid}/restaurar/999",
                       headers=auth("master"), timeout=30)
        assert r.status_code == 404
