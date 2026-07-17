"""MAINTRIX Sprint 1 — Corporate Library Versioning Tests
Tests full version governance for Procedimentos & Segurança:
- Create → v1
- Update → v2, v3
- List versions
- Restore → new version with old data
- RBAC (técnico blocked, PCM allowed)
- Unicode preservation across versioning
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


# ============== LOGIN ==============

class TestLogin:
    def test_master_login_with_org(self):
        token = get_token("master")
        assert token
        # auth/me returns user
        r = httpx.get(f"{API}/auth/me", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        assert r.json().get("email") == "master@maintrix.com"

    def test_all_users_login(self):
        for role in USERS:
            assert get_token(role)


# ============== PROCEDIMENTO FULL VERSIONING FLOW ==============

class TestProcedimentoVersioning:
    _proc_id = None

    def test_01_create_procedimento_v1(self):
        payload = {
            "nome": f"TEST_Proc_{uuid.uuid4().hex[:8]}",
            "codigo": "PRC-TEST-001",
            "tipo_atividade": "preventiva",
            "disciplina": "mecanica",
            "objetivo": "Objetivo v1",
            "etapas": [{"descricao": "Etapa 1 v1"}],
            "ferramentas": ["Chave 10mm"],
        }
        r = httpx.post(f"{API}/doc-config/procedimentos", headers=auth("master"), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["versao"] == 1
        assert data["status"] == "created"
        assert "id" in data
        TestProcedimentoVersioning._proc_id = data["id"]

        # Verify v1 archived
        v = httpx.get(f"{API}/doc-config/procedimentos/{data['id']}/versoes", headers=auth("master"), timeout=30)
        assert v.status_code == 200
        versions = v.json()
        assert len(versions) == 1
        assert versions[0]["versao"] == 1
        assert versions[0]["motivo"] == "Criação inicial"
        assert "snapshot" in versions[0]

    def test_02_update_to_v2(self):
        pid = TestProcedimentoVersioning._proc_id
        assert pid, "prior test must have created procedimento"
        payload = {
            "nome": f"TEST_Proc_v2",
            "codigo": "PRC-TEST-001",
            "objetivo": "Objetivo v2 atualizado",
            "etapas": [{"descricao": "Etapa 1 v2"}, {"descricao": "Etapa 2 v2"}],
            "ferramentas": ["Chave 10mm", "Torquimetro"],
            "motivo_alteracao": "Revisão para v2",
        }
        r = httpx.put(f"{API}/doc-config/procedimentos/{pid}", headers=auth("master"), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["versao"] == 2

    def test_03_update_to_v3(self):
        pid = TestProcedimentoVersioning._proc_id
        payload = {
            "nome": f"TEST_Proc_v3",
            "objetivo": "Objetivo v3",
            "etapas": [{"descricao": "Etapa 1 v3"}],
            "motivo_alteracao": "Revisão para v3",
        }
        r = httpx.put(f"{API}/doc-config/procedimentos/{pid}", headers=auth("master"), json=payload, timeout=30)
        assert r.status_code == 200
        assert r.json()["versao"] == 3

    def test_04_list_versions_returns_3_desc(self):
        pid = TestProcedimentoVersioning._proc_id
        r = httpx.get(f"{API}/doc-config/procedimentos/{pid}/versoes", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        versions = r.json()
        assert len(versions) == 3, f"Expected 3 versions, got {len(versions)}"
        # descending order
        assert versions[0]["versao"] == 3
        assert versions[1]["versao"] == 2
        assert versions[2]["versao"] == 1
        # each has snapshot and motivo
        for v in versions:
            assert "snapshot" in v and isinstance(v["snapshot"], dict)
            assert "motivo" in v
            assert v["snapshot"].get("nome") is not None

    def test_05_restore_v1_creates_v4(self):
        pid = TestProcedimentoVersioning._proc_id
        r = httpx.post(
            f"{API}/doc-config/procedimentos/{pid}/restaurar/1",
            headers=auth("master"),
            params={"motivo": "Reverter para inicial"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["nova_versao"] == 4
        assert data["versao_restaurada"] == 1
        assert data["status"] == "restored"

    def test_06_current_state_has_v1_data_and_v4_number(self):
        pid = TestProcedimentoVersioning._proc_id
        # There is no GET /procedimentos/{id} endpoint but we can list & find it
        r = httpx.get(f"{API}/doc-config/procedimentos", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        items = [x for x in r.json() if x["id"] == pid]
        assert items, "restored procedimento not found in list"
        item = items[0]
        assert item["versao"] == 4
        # The v1 data had objetivo "Objetivo v1"
        assert item["objetivo"] == "Objetivo v1"
        assert item["nome"].startswith("TEST_Proc_") and "v2" not in item["nome"] and "v3" not in item["nome"]

    def test_07_versoes_after_restore_has_4(self):
        pid = TestProcedimentoVersioning._proc_id
        r = httpx.get(f"{API}/doc-config/procedimentos/{pid}/versoes", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        versions = r.json()
        assert len(versions) == 4
        assert versions[0]["versao"] == 4
        assert "Restaurado" in (versions[0].get("motivo") or "")


# ============== SEGURANCA FULL FLOW ==============

class TestSegurancaVersioning:
    _seg_id = None

    def test_01_create_seguranca_v1(self):
        payload = {
            "nome": f"TEST_Seg_{uuid.uuid4().hex[:8]}",
            "codigo": "SEG-TEST-001",
            "riscos": [{"tipo": "eletrico", "nivel": "alto"}],
            "epis": ["Capacete", "Luva isolante"],
        }
        r = httpx.post(f"{API}/doc-config/seguranca", headers=auth("master"), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["versao"] == 1
        TestSegurancaVersioning._seg_id = data["id"]

    def test_02_update_v2_v3(self):
        sid = TestSegurancaVersioning._seg_id
        for i, motivo in [(2, "v2"), (3, "v3")]:
            payload = {
                "nome": f"TEST_Seg_v{i}",
                "riscos": [{"tipo": "mecanico", "nivel": "medio"}],
                "epis": [f"EPI-{i}"],
                "motivo_alteracao": motivo,
            }
            r = httpx.put(f"{API}/doc-config/seguranca/{sid}", headers=auth("master"), json=payload, timeout=30)
            assert r.status_code == 200
            assert r.json()["versao"] == i

    def test_03_list_versoes(self):
        sid = TestSegurancaVersioning._seg_id
        r = httpx.get(f"{API}/doc-config/seguranca/{sid}/versoes", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        versions = r.json()
        assert len(versions) == 3
        assert [v["versao"] for v in versions] == [3, 2, 1]

    def test_04_restore_v1(self):
        sid = TestSegurancaVersioning._seg_id
        r = httpx.post(
            f"{API}/doc-config/seguranca/{sid}/restaurar/1",
            headers=auth("master"),
            params={"motivo": "Reverter"},
            timeout=30,
        )
        assert r.status_code == 200
        assert r.json()["nova_versao"] == 4

        # Verify list now has 4 versions
        v = httpx.get(f"{API}/doc-config/seguranca/{sid}/versoes", headers=auth("master"), timeout=30)
        assert v.status_code == 200
        assert len(v.json()) == 4


# ============== RBAC ==============

class TestRBAC:
    def test_tecnico_cannot_create_procedimento(self):
        payload = {"nome": "TEST_Should_Fail"}
        r = httpx.post(f"{API}/doc-config/procedimentos", headers=auth("tecnico"), json=payload, timeout=30)
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"

    def test_tecnico_cannot_update_procedimento(self):
        # need a real id — use master to create then techie tries to update
        c = httpx.post(f"{API}/doc-config/procedimentos", headers=auth("master"),
                       json={"nome": "TEST_RBAC_Update"}, timeout=30)
        pid = c.json()["id"]
        r = httpx.put(f"{API}/doc-config/procedimentos/{pid}",
                      headers=auth("tecnico"), json={"nome": "hacked"}, timeout=30)
        assert r.status_code == 403

    def test_tecnico_cannot_delete_procedimento(self):
        c = httpx.post(f"{API}/doc-config/procedimentos", headers=auth("master"),
                       json={"nome": "TEST_RBAC_Delete"}, timeout=30)
        pid = c.json()["id"]
        r = httpx.delete(f"{API}/doc-config/procedimentos/{pid}", headers=auth("tecnico"), timeout=30)
        assert r.status_code == 403

    def test_tecnico_cannot_restore(self):
        c = httpx.post(f"{API}/doc-config/procedimentos", headers=auth("master"),
                       json={"nome": "TEST_RBAC_Restore"}, timeout=30)
        pid = c.json()["id"]
        r = httpx.post(f"{API}/doc-config/procedimentos/{pid}/restaurar/1",
                       headers=auth("tecnico"), timeout=30)
        assert r.status_code == 403

    def test_pcm_can_create_procedimento(self):
        payload = {"nome": f"TEST_PCM_{uuid.uuid4().hex[:8]}"}
        r = httpx.post(f"{API}/doc-config/procedimentos", headers=auth("pcm"), json=payload, timeout=30)
        assert r.status_code == 200
        assert r.json()["versao"] == 1

    def test_pcm_can_update_procedimento(self):
        c = httpx.post(f"{API}/doc-config/procedimentos", headers=auth("pcm"),
                       json={"nome": "TEST_PCM_Upd"}, timeout=30)
        assert c.status_code == 200
        pid = c.json()["id"]
        r = httpx.put(f"{API}/doc-config/procedimentos/{pid}",
                      headers=auth("pcm"),
                      json={"nome": "TEST_PCM_Upd_v2", "motivo_alteracao": "pcm edit"},
                      timeout=30)
        assert r.status_code == 200
        assert r.json()["versao"] == 2


# ============== UNICODE ==============

class TestUnicodeVersioning:
    def test_unicode_survives_create_update_restore(self):
        unicode_str = "µm °C Ω Ø ± ← → ✓"
        # Create
        r = httpx.post(f"{API}/doc-config/procedimentos", headers=auth("master"), json={
            "nome": f"TEST_UNI_{uuid.uuid4().hex[:6]}",
            "objetivo": unicode_str,
            "etapas": [{"descricao": f"medir {unicode_str}"}],
        }, timeout=30)
        assert r.status_code == 200
        pid = r.json()["id"]

        # Update
        r2 = httpx.put(f"{API}/doc-config/procedimentos/{pid}", headers=auth("master"), json={
            "nome": "TEST_UNI_v2",
            "objetivo": "changed",
            "motivo_alteracao": "test unicode",
        }, timeout=30)
        assert r2.status_code == 200

        # Verify v1 snapshot preserves unicode
        v = httpx.get(f"{API}/doc-config/procedimentos/{pid}/versoes", headers=auth("master"), timeout=30)
        assert v.status_code == 200
        versions = v.json()
        v1 = [x for x in versions if x["versao"] == 1][0]
        assert v1["snapshot"]["objetivo"] == unicode_str
        assert unicode_str in v1["snapshot"]["etapas"][0]["descricao"]

        # Restore v1
        r3 = httpx.post(f"{API}/doc-config/procedimentos/{pid}/restaurar/1", headers=auth("master"), timeout=30)
        assert r3.status_code == 200

        # Verify current has unicode
        lst = httpx.get(f"{API}/doc-config/procedimentos", headers=auth("master"), timeout=30).json()
        current = [x for x in lst if x["id"] == pid][0]
        assert current["objetivo"] == unicode_str
