"""Iteration 24 - MANUTRIX OMNI Phase 2 P0 tests:
- Inspection templates CRUD per equipment type
- Equipment types listing
- BOM (materiais) CRUD update endpoint
- Inspecao checklist completion with mixed item types (boolean, numerico, opcao, texto)
- OS create with executantes (equipe)
"""
import os
import uuid
import requests
import pytest

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        # Fallback: read from /app/frontend/.env
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip()
                        break
        except FileNotFoundError:
            pass
    if not url:
        raise RuntimeError("REACT_APP_BACKEND_URL not set")
    return url.rstrip("/") + "/api"

BASE = _load_backend_url()
ADMIN = {"email": "admin@manutrix.com", "password": "admin123"}
EXISTING_ATIVO = "435593b8-a66a-4ddd-a8c6-f4bcce70d4cd"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json=ADMIN)
    assert r.status_code == 200, f"Login failed: {r.text}"
    data = r.json()
    token = data.get("access_token") or data.get("token")
    if token:
        s.headers.update({"Authorization": f"Bearer {token}"})
    return s


# ============== INSPECTION TEMPLATES CRUD ==============

class TestInspectionTemplates:
    template_id = None

    def test_01_create_template(self, session):
        payload = {
            "nome": f"TEST_Alimentador_{uuid.uuid4().hex[:6]}",
            "tipo_equipamento": "ALIMENTADOR VIBRATÓRIO",
            "descricao": "Template teste iter24",
            "itens": [
                {"descricao": "Verificar molas", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Temperatura motor", "tipo": "numerico", "unidade": "°C", "obrigatorio": True},
                {"descricao": "Estado da calha", "tipo": "opcao", "obrigatorio": True},
            ],
        }
        r = session.post(f"{BASE}/inspection-templates", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["nome"] == payload["nome"]
        assert body["tipo_equipamento"] == payload["tipo_equipamento"]
        assert len(body["itens"]) == 3
        # All items get a uuid id
        for it in body["itens"]:
            assert it.get("id")
        TestInspectionTemplates.template_id = body["id"]

    def test_02_list_templates(self, session):
        r = session.get(f"{BASE}/inspection-templates")
        assert r.status_code == 200
        lst = r.json()
        assert isinstance(lst, list)
        assert any(t["id"] == TestInspectionTemplates.template_id for t in lst)

    def test_03_filter_by_tipo(self, session):
        r = session.get(f"{BASE}/inspection-templates", params={"tipo_equipamento": "ALIMENTADOR VIBRATÓRIO"})
        assert r.status_code == 200
        for t in r.json():
            assert t["tipo_equipamento"] == "ALIMENTADOR VIBRATÓRIO"

    def test_04_get_template(self, session):
        r = session.get(f"{BASE}/inspection-templates/{TestInspectionTemplates.template_id}")
        assert r.status_code == 200
        assert r.json()["id"] == TestInspectionTemplates.template_id

    def test_05_update_template(self, session):
        new_name = f"TEST_Edited_{uuid.uuid4().hex[:6]}"
        r = session.put(
            f"{BASE}/inspection-templates/{TestInspectionTemplates.template_id}",
            json={"nome": new_name},
        )
        assert r.status_code == 200, r.text
        # Verify with GET
        g = session.get(f"{BASE}/inspection-templates/{TestInspectionTemplates.template_id}")
        assert g.json()["nome"] == new_name

    def test_06_duplicate_template(self, session):
        r = session.post(f"{BASE}/inspection-templates/{TestInspectionTemplates.template_id}/duplicate")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "(Cópia)" in body["nome"]
        assert len(body["itens"]) == 3
        # cleanup
        session.delete(f"{BASE}/inspection-templates/{body['id']}")

    def test_07_delete_template(self, session):
        r = session.delete(f"{BASE}/inspection-templates/{TestInspectionTemplates.template_id}")
        assert r.status_code == 200
        # Verify deleted (404)
        g = session.get(f"{BASE}/inspection-templates/{TestInspectionTemplates.template_id}")
        assert g.status_code == 404


# ============== EQUIPMENT TYPES ==============

class TestEquipmentTypes:
    def test_list_equipment_types(self, session):
        r = session.get(f"{BASE}/equipment-types")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ============== BOM (MATERIAIS) ==============

class TestBOM:
    mat_id = None

    def test_01_create_material(self, session):
        payload = {
            "codigo": "TEST_ROL-22218",
            "nome": "Rolamento 22218",
            "quantidade": 2,
            "unidade": "UN",
            "observacoes": "Teste BOM"
        }
        r = session.post(f"{BASE}/ativos/{EXISTING_ATIVO}/materiais", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["codigo"] == payload["codigo"]
        assert body["quantidade"] == 2
        TestBOM.mat_id = body["id"]

    def test_02_list_materials(self, session):
        r = session.get(f"{BASE}/ativos/{EXISTING_ATIVO}/materiais")
        assert r.status_code == 200
        ids = [m["id"] for m in r.json()]
        assert TestBOM.mat_id in ids

    def test_03_update_material(self, session):
        payload = {
            "codigo": "TEST_ROL-22218",
            "nome": "Rolamento 22218 (atualizado)",
            "quantidade": 4,
            "unidade": "UN",
            "observacoes": "Updated"
        }
        r = session.put(f"{BASE}/ativos/{EXISTING_ATIVO}/materiais/{TestBOM.mat_id}", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["quantidade"] == 4
        assert "atualizado" in body["nome"]

    def test_04_delete_material(self, session):
        r = session.delete(f"{BASE}/ativos/{EXISTING_ATIVO}/materiais/{TestBOM.mat_id}")
        assert r.status_code == 200
        # Verify removed from list
        g = session.get(f"{BASE}/ativos/{EXISTING_ATIVO}/materiais")
        ids = [m["id"] for m in g.json()]
        assert TestBOM.mat_id not in ids


# ============== INSPECAO CHECKLIST BUG FIX ==============

class TestInspecaoChecklistMixed:
    """Bug fix: items with tipo=numerico and tipo=opcao must be acceptable on Concluir."""

    inspecao_id = None

    def test_01_create_inspecao_mecanica(self, session):
        # tipo=mecanica triggers the default checklist template that has booleans + numerico + opcao
        payload = {
            "ativo_id": EXISTING_ATIVO,
            "tipo": "mecanica",
            "data_inspecao": "2026-01-15T10:00:00Z",
            "observacoes": "TEST_iter24 mixed checklist",
        }
        r = session.post(f"{BASE}/inspecoes", json=payload)
        assert r.status_code in (200, 201), r.text
        body = r.json()
        TestInspecaoChecklistMixed.inspecao_id = body["id"]
        # Confirm itens include numerico + opcao + boolean (fetched via GET after iniciar in next test)
        # Items can be auto-populated either on create or on iniciar - just ensure inspecao was created
        assert body.get("id")

    def test_02_iniciar(self, session):
        r = session.post(f"{BASE}/inspecoes/{TestInspecaoChecklistMixed.inspecao_id}/iniciar")
        assert r.status_code == 200, r.text

    def test_03_concluir_with_mixed_filled_items(self, session):
        # Fetch inspecao to get current itens
        r = session.get(f"{BASE}/inspecoes/{TestInspecaoChecklistMixed.inspecao_id}")
        assert r.status_code == 200
        insp = r.json()
        itens = insp.get("itens") or []
        # Fill every item appropriately
        filled = []
        for it in itens:
            t = it.get("tipo", "boolean")
            entry = {**it}
            if t == "boolean":
                entry["conforme"] = True
            elif t in ("numerico", "numero", "temperatura", "vibracao"):
                entry["resultado"] = "50"
                entry["valor"] = 50
            elif t == "opcao":
                entry["resultado"] = "Bom"
            else:  # texto, observacao
                entry["resultado"] = "OK"
            filled.append(entry)
        payload = {"itens": filled, "observacoes_finais": "TEST iter24 concluido"}
        r = session.post(f"{BASE}/inspecoes/{TestInspecaoChecklistMixed.inspecao_id}/concluir", json=payload)
        # Should NOT return 400 'Preencha todos...'
        assert r.status_code in (200, 201), f"Concluir failed: {r.status_code} {r.text}"

    def test_04_cleanup(self, session):
        session.delete(f"{BASE}/inspecoes/{TestInspecaoChecklistMixed.inspecao_id}")


# ============== OS EXECUTANTES (equipe) ==============

class TestOSExecutantes:
    os_id = None

    def test_create_os_with_equipe(self, session):
        # Need user IDs for equipe
        users_r = session.get(f"{BASE}/users")
        users = users_r.json() if users_r.status_code == 200 else []
        equipe_ids = [u["id"] for u in users[:2]] if len(users) >= 2 else []
        payload = {
            "ativo_id": EXISTING_ATIVO,
            "titulo": "TEST_iter24 executantes",
            "tipo": "preventiva",
            "disciplina": "mecanica",
            "prioridade": "media",
            "descricao": "TEST_iter24 executantes",
            "equipe": equipe_ids,
        }
        r = session.post(f"{BASE}/ordens-servico", json=payload)
        assert r.status_code in (200, 201), r.text
        body = r.json()
        TestOSExecutantes.os_id = body["id"]
        # Verify equipe persisted
        g = session.get(f"{BASE}/ordens-servico/{body['id']}")
        assert g.status_code == 200
        assert g.json().get("equipe", []) == equipe_ids

    def test_cleanup(self, session):
        if TestOSExecutantes.os_id:
            session.delete(f"{BASE}/ordens-servico/{TestOSExecutantes.os_id}")
