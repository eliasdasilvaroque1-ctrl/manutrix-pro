"""MAINTRIX Sprint 3 — Personalização Corporativa
Coverage:
- Campos Personalizados (17 types, validators, unique identificador, immutable ident)
- Cabeçalhos/Rodapés
- Blocos Assinatura
- Layouts Documento (auto-snapshot of cabecalho/rodape)
- Full version lifecycle for all 4 modules
- RBAC (técnico blocked, pcm allowed)
- Snapshot isolation on layouts
- Validation errors (422)
- Soft-delete
- GET /doc-config/campos/por-modulo/{modulo}?tipo=
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


def _ident():
    return "test_" + uuid.uuid4().hex[:8]


# ============== LOGIN SMOKE ==============

class TestLogin:
    def test_all_logins(self):
        for role in USERS:
            assert get_token(role)


# ============== CAMPOS PERSONALIZADOS ==============

TIPOS_CAMPO = [
    "texto_curto", "texto_longo", "numero", "decimal", "data", "hora", "data_hora",
    "selecao_unica", "multipla_selecao", "checkbox", "sim_nao",
    "foto", "assinatura", "qr_code", "url", "email", "telefone",
]


class TestCamposCreateAllTypes:
    """Ensure all 17 types can be persisted."""
    def test_create_all_17_types(self):
        created = []
        for t in TIPOS_CAMPO:
            payload = {
                "nome": f"TEST_C_{t}",
                "identificador_tecnico": _ident(),
                "tipo": t,
                "aplicacao_modulos": ["os"],
            }
            r = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json=payload, timeout=30)
            assert r.status_code == 200, f"tipo {t} failed: {r.text}"
            data = r.json()
            assert data["versao"] == 1
            created.append(data["id"])
        assert len(created) == 17


class TestCamposValidation:
    def test_invalid_tipo_422(self):
        r = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json={
            "nome": "TEST_BAD", "identificador_tecnico": _ident(), "tipo": "not_a_type",
        }, timeout=30)
        assert r.status_code == 422, r.text

    def test_invalid_identificador_uppercase_422(self):
        r = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json={
            "nome": "TEST_BAD", "identificador_tecnico": "BadIdent", "tipo": "texto_curto",
        }, timeout=30)
        assert r.status_code == 422, r.text

    def test_invalid_identificador_starts_with_digit_422(self):
        r = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json={
            "nome": "TEST_BAD", "identificador_tecnico": "1abc", "tipo": "texto_curto",
        }, timeout=30)
        assert r.status_code == 422, r.text

    def test_invalid_identificador_dashes_422(self):
        r = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json={
            "nome": "TEST_BAD", "identificador_tecnico": "bad-ident", "tipo": "texto_curto",
        }, timeout=30)
        assert r.status_code == 422, r.text

    def test_invalid_modulo_422(self):
        r = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json={
            "nome": "TEST_BAD", "identificador_tecnico": _ident(), "tipo": "texto_curto",
            "aplicacao_modulos": ["not_a_module"],
        }, timeout=30)
        assert r.status_code == 422, r.text


class TestCamposDuplicateIdent:
    def test_duplicate_identificador_returns_409(self):
        ident = _ident()
        payload = {"nome": "TEST_DUP1", "identificador_tecnico": ident, "tipo": "texto_curto"}
        r1 = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json=payload, timeout=30)
        assert r1.status_code == 200
        r2 = httpx.post(f"{API}/doc-config/campos", headers=auth("master"),
                        json={**payload, "nome": "TEST_DUP2"}, timeout=30)
        assert r2.status_code == 409, r2.text


class TestCamposLifecycle:
    _cid = None
    _ident_original = None

    def test_01_create_v1(self):
        TestCamposLifecycle._ident_original = _ident()
        payload = {
            "nome": "TEST_LC_CAMPO",
            "identificador_tecnico": TestCamposLifecycle._ident_original,
            "tipo": "numero",
            "obrigatorio": True,
            "aplicacao_modulos": ["os"],
            "aplicacao_tipos": ["corretiva"],
        }
        r = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["versao"] == 1
        TestCamposLifecycle._cid = data["id"]

        # GET to verify persistence
        g = httpx.get(f"{API}/doc-config/campos/{data['id']}", headers=auth("master"), timeout=30).json()
        assert g["nome"] == "TEST_LC_CAMPO"
        assert g["identificador_tecnico"] == TestCamposLifecycle._ident_original
        assert g["tipo"] == "numero"
        assert g["obrigatorio"] is True
        assert "_id" not in g

    def test_02_update_v2_preserves_identifier(self):
        cid = TestCamposLifecycle._cid
        # Attempt to modify identificador (should be ignored / preserved)
        r = httpx.put(f"{API}/doc-config/campos/{cid}", headers=auth("master"), json={
            "nome": "TEST_LC_CAMPO_v2",
            "identificador_tecnico": "hacked_ident",
            "tipo": "decimal",
            "casas_decimais": 3,
            "aplicacao_modulos": ["os", "inspecao"],
            "motivo_alteracao": "v2",
        }, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["versao"] == 2

        g = httpx.get(f"{API}/doc-config/campos/{cid}", headers=auth("master"), timeout=30).json()
        assert g["nome"] == "TEST_LC_CAMPO_v2"
        # Immutable identifier preserved
        assert g["identificador_tecnico"] == TestCamposLifecycle._ident_original
        assert g["tipo"] == "decimal"
        assert g["casas_decimais"] == 3

    def test_03_list_versions(self):
        cid = TestCamposLifecycle._cid
        r = httpx.get(f"{API}/doc-config/campos/{cid}/versoes", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        vs = r.json()
        assert [v["versao"] for v in vs] == [2, 1]

    def test_04_restore_v1_creates_v3(self):
        cid = TestCamposLifecycle._cid
        r = httpx.post(f"{API}/doc-config/campos/{cid}/restaurar/1", headers=auth("master"), timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["nova_versao"] == 3
        g = httpx.get(f"{API}/doc-config/campos/{cid}", headers=auth("master"), timeout=30).json()
        assert g["versao"] == 3
        # Restored from v1 (numero, obrigatorio=True)
        assert g["tipo"] == "numero"
        assert g["obrigatorio"] is True

    def test_05_soft_delete(self):
        cid = TestCamposLifecycle._cid
        r = httpx.delete(f"{API}/doc-config/campos/{cid}", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        # 404 after delete
        assert httpx.get(f"{API}/doc-config/campos/{cid}", headers=auth("master"), timeout=30).status_code == 404
        # archive has "Exclusão" motivo
        v = httpx.get(f"{API}/doc-config/campos/{cid}/versoes", headers=auth("master"), timeout=30).json()
        assert any("Exclus" in (x.get("motivo") or "") for x in v)


class TestCamposPorModulo:
    _cid_os_corretiva = None
    _cid_os_all = None
    _cid_inspecao = None

    def test_01_seed_fields(self):
        # 1) Applies to OS + tipo corretiva
        p1 = {"nome": "TEST_PM_1", "identificador_tecnico": _ident(), "tipo": "texto_curto",
              "aplicacao_modulos": ["os"], "aplicacao_tipos": ["corretiva"]}
        r = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json=p1, timeout=30)
        assert r.status_code == 200
        TestCamposPorModulo._cid_os_corretiva = r.json()["id"]

        # 2) Applies to OS with no tipo filter (matches any)
        p2 = {"nome": "TEST_PM_2", "identificador_tecnico": _ident(), "tipo": "texto_curto",
              "aplicacao_modulos": ["os"], "aplicacao_tipos": []}
        r = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json=p2, timeout=30)
        assert r.status_code == 200
        TestCamposPorModulo._cid_os_all = r.json()["id"]

        # 3) Applies only to inspecao
        p3 = {"nome": "TEST_PM_3", "identificador_tecnico": _ident(), "tipo": "texto_curto",
              "aplicacao_modulos": ["inspecao"]}
        r = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json=p3, timeout=30)
        assert r.status_code == 200
        TestCamposPorModulo._cid_inspecao = r.json()["id"]

    def test_02_por_modulo_os_corretiva(self):
        r = httpx.get(f"{API}/doc-config/campos/por-modulo/os", headers=auth("master"),
                      params={"tipo": "corretiva"}, timeout=30)
        assert r.status_code == 200
        ids = {c["id"] for c in r.json()}
        # Must include both p1 (matches tipo) and p2 (empty tipos = matches any)
        assert TestCamposPorModulo._cid_os_corretiva in ids
        assert TestCamposPorModulo._cid_os_all in ids
        # Must NOT include p3 (inspecao only)
        assert TestCamposPorModulo._cid_inspecao not in ids

    def test_03_por_modulo_os_preventiva(self):
        r = httpx.get(f"{API}/doc-config/campos/por-modulo/os", headers=auth("master"),
                      params={"tipo": "preventiva"}, timeout=30)
        assert r.status_code == 200
        ids = {c["id"] for c in r.json()}
        # p1 restricted to corretiva → excluded
        assert TestCamposPorModulo._cid_os_corretiva not in ids
        # p2 empty tipos → included
        assert TestCamposPorModulo._cid_os_all in ids

    def test_04_por_modulo_inspecao(self):
        r = httpx.get(f"{API}/doc-config/campos/por-modulo/inspecao", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        ids = {c["id"] for c in r.json()}
        assert TestCamposPorModulo._cid_inspecao in ids
        assert TestCamposPorModulo._cid_os_corretiva not in ids


# ============== CABECALHOS/RODAPES ==============

class TestCabecalhosRodapes:
    _cab_id = None
    _rod_id = None

    def test_01_create_cabecalho(self):
        r = httpx.post(f"{API}/doc-config/cabecalhos-rodapes", headers=auth("master"), json={
            "nome": "TEST_CAB",
            "tipo": "cabecalho",
            "razao_social": "Empresa Teste",
            "cnpj": "00.000.000/0001-00",
        }, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["versao"] == 1
        TestCabecalhosRodapes._cab_id = data["id"]

    def test_02_create_rodape(self):
        r = httpx.post(f"{API}/doc-config/cabecalhos-rodapes", headers=auth("master"), json={
            "nome": "TEST_ROD", "tipo": "rodape", "mostrar_paginacao": True,
        }, timeout=30)
        assert r.status_code == 200, r.text
        TestCabecalhosRodapes._rod_id = r.json()["id"]

    def test_03_invalid_tipo_422(self):
        r = httpx.post(f"{API}/doc-config/cabecalhos-rodapes", headers=auth("master"), json={
            "nome": "TEST_BAD", "tipo": "meio",
        }, timeout=30)
        assert r.status_code == 422

    def test_04_update_v2(self):
        cid = TestCabecalhosRodapes._cab_id
        r = httpx.put(f"{API}/doc-config/cabecalhos-rodapes/{cid}", headers=auth("master"), json={
            "nome": "TEST_CAB_v2", "tipo": "cabecalho", "razao_social": "Nova Razão",
            "motivo_alteracao": "v2",
        }, timeout=30)
        assert r.status_code == 200
        assert r.json()["versao"] == 2

    def test_05_list_versions_and_restore(self):
        cid = TestCabecalhosRodapes._cab_id
        vs = httpx.get(f"{API}/doc-config/cabecalhos-rodapes/{cid}/versoes",
                       headers=auth("master"), timeout=30).json()
        assert [v["versao"] for v in vs] == [2, 1]
        r = httpx.post(f"{API}/doc-config/cabecalhos-rodapes/{cid}/restaurar/1",
                       headers=auth("master"), timeout=30)
        assert r.status_code == 200
        assert r.json()["nova_versao"] == 3

    def test_06_soft_delete(self):
        cid = TestCabecalhosRodapes._cab_id
        r = httpx.delete(f"{API}/doc-config/cabecalhos-rodapes/{cid}",
                         headers=auth("master"), timeout=30)
        assert r.status_code == 200


# ============== BLOCOS ASSINATURA ==============

class TestBlocosAssinatura:
    _ass_id = None

    def test_01_create_with_campos(self):
        r = httpx.post(f"{API}/doc-config/assinaturas", headers=auth("master"), json={
            "nome": "TEST_ASS_EXECUTOR",
            "papel": "executor",
            "campos": [
                {"campo": "nome", "obrigatorio": True, "ordem": 1},
                {"campo": "matricula", "obrigatorio": True, "ordem": 2},
                {"campo": "data", "obrigatorio": True, "ordem": 3},
                {"campo": "assinatura_imagem", "obrigatorio": False, "ordem": 4},
            ],
            "matricula_obrigatoria": True,
            "captura_digital": True,
        }, timeout=30)
        assert r.status_code == 200, r.text
        TestBlocosAssinatura._ass_id = r.json()["id"]

        g = httpx.get(f"{API}/doc-config/assinaturas/{TestBlocosAssinatura._ass_id}",
                      headers=auth("master"), timeout=30).json()
        assert g["papel"] == "executor"
        assert g["captura_digital"] is True
        assert len(g["campos"]) == 4
        assert g["campos"][0]["campo"] == "nome"

    def test_02_update_v2(self):
        aid = TestBlocosAssinatura._ass_id
        r = httpx.put(f"{API}/doc-config/assinaturas/{aid}", headers=auth("master"), json={
            "nome": "TEST_ASS_EXECUTOR_v2",
            "papel": "supervisor",
            "campos": [{"campo": "nome", "obrigatorio": True, "ordem": 1}],
            "motivo_alteracao": "v2",
        }, timeout=30)
        assert r.status_code == 200
        assert r.json()["versao"] == 2

    def test_03_delete(self):
        aid = TestBlocosAssinatura._ass_id
        r = httpx.delete(f"{API}/doc-config/assinaturas/{aid}", headers=auth("master"), timeout=30)
        assert r.status_code == 200


# ============== LAYOUTS + SNAPSHOT ISOLATION ==============

class TestLayouts:
    _cab_id = None
    _rod_id = None
    _layout_id = None

    def test_01_seed_cabecalho_and_rodape(self):
        c = httpx.post(f"{API}/doc-config/cabecalhos-rodapes", headers=auth("master"), json={
            "nome": "TEST_LAY_CAB",
            "tipo": "cabecalho",
            "razao_social": "ORIGINAL v1 razao",
        }, timeout=30)
        assert c.status_code == 200
        TestLayouts._cab_id = c.json()["id"]

        r = httpx.post(f"{API}/doc-config/cabecalhos-rodapes", headers=auth("master"), json={
            "nome": "TEST_LAY_ROD",
            "tipo": "rodape",
            "texto_personalizado": "ORIGINAL v1 rodape",
        }, timeout=30)
        assert r.status_code == 200
        TestLayouts._rod_id = r.json()["id"]

    def test_02_create_layout_auto_snapshot(self):
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth("master"), json={
            "nome": "TEST_LAY",
            "orientacao": "retrato",
            "tamanho_pagina": "A4",
            "cabecalho_id": TestLayouts._cab_id,
            "rodape_id": TestLayouts._rod_id,
        }, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["versao"] == 1
        TestLayouts._layout_id = data["id"]

        g = httpx.get(f"{API}/doc-config/layouts/{data['id']}", headers=auth("master"), timeout=30).json()
        assert g["cabecalho_id"] == TestLayouts._cab_id
        assert g["rodape_id"] == TestLayouts._rod_id
        # Auto-snapshot happened
        assert g.get("cabecalho_snapshot") is not None, "cabecalho snapshot not resolved"
        assert g["cabecalho_snapshot"].get("razao_social") == "ORIGINAL v1 razao"
        assert g.get("rodape_snapshot") is not None, "rodape snapshot not resolved"
        assert g["rodape_snapshot"].get("texto_personalizado") == "ORIGINAL v1 rodape"

    def test_03_snapshot_isolation_after_cabecalho_update(self):
        """CRITICAL: after source cabecalho is updated to v2, layout snapshot must remain original."""
        cab_id = TestLayouts._cab_id
        layout_id = TestLayouts._layout_id

        upd = httpx.put(f"{API}/doc-config/cabecalhos-rodapes/{cab_id}", headers=auth("master"), json={
            "nome": "TEST_LAY_CAB_UPD",
            "tipo": "cabecalho",
            "razao_social": "MUTATED v2 razao",
            "motivo_alteracao": "mutate",
        }, timeout=30)
        assert upd.status_code == 200
        assert upd.json()["versao"] == 2

        # layout should still hold ORIGINAL snapshot
        g = httpx.get(f"{API}/doc-config/layouts/{layout_id}", headers=auth("master"), timeout=30).json()
        assert g["cabecalho_snapshot"]["razao_social"] == "ORIGINAL v1 razao", \
            f"SNAPSHOT LEAKED! Got: {g['cabecalho_snapshot'].get('razao_social')}"

    def test_04_invalid_orientacao_422(self):
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth("master"), json={
            "nome": "TEST_BAD_LAY", "orientacao": "diagonal",
        }, timeout=30)
        assert r.status_code == 422

    def test_05_update_layout_v2_and_versions(self):
        lid = TestLayouts._layout_id
        r = httpx.put(f"{API}/doc-config/layouts/{lid}", headers=auth("master"), json={
            "nome": "TEST_LAY_v2",
            "orientacao": "paisagem",
            "cabecalho_id": TestLayouts._cab_id,
            "rodape_id": TestLayouts._rod_id,
            "motivo_alteracao": "v2 lay",
        }, timeout=30)
        assert r.status_code == 200
        assert r.json()["versao"] == 2

        vs = httpx.get(f"{API}/doc-config/layouts/{lid}/versoes",
                       headers=auth("master"), timeout=30).json()
        assert [v["versao"] for v in vs] == [2, 1]

    def test_06_restore_v1(self):
        lid = TestLayouts._layout_id
        r = httpx.post(f"{API}/doc-config/layouts/{lid}/restaurar/1",
                       headers=auth("master"), timeout=30)
        assert r.status_code == 200
        assert r.json()["nova_versao"] == 3
        g = httpx.get(f"{API}/doc-config/layouts/{lid}", headers=auth("master"), timeout=30).json()
        assert g["orientacao"] == "retrato"

    def test_07_soft_delete(self):
        lid = TestLayouts._layout_id
        r = httpx.delete(f"{API}/doc-config/layouts/{lid}", headers=auth("master"), timeout=30)
        assert r.status_code == 200
        assert httpx.get(f"{API}/doc-config/layouts/{lid}",
                         headers=auth("master"), timeout=30).status_code == 404


# ============== RBAC ==============

class TestRBAC:
    def test_tecnico_blocked_campos_post(self):
        r = httpx.post(f"{API}/doc-config/campos", headers=auth("tecnico"), json={
            "nome": "T", "identificador_tecnico": _ident(), "tipo": "texto_curto",
        }, timeout=30)
        assert r.status_code == 403

    def test_tecnico_blocked_cabecalhos_post(self):
        r = httpx.post(f"{API}/doc-config/cabecalhos-rodapes", headers=auth("tecnico"), json={
            "nome": "T", "tipo": "cabecalho",
        }, timeout=30)
        assert r.status_code == 403

    def test_tecnico_blocked_assinaturas_post(self):
        r = httpx.post(f"{API}/doc-config/assinaturas", headers=auth("tecnico"), json={
            "nome": "T", "papel": "executor",
        }, timeout=30)
        assert r.status_code == 403

    def test_tecnico_blocked_layouts_post(self):
        r = httpx.post(f"{API}/doc-config/layouts", headers=auth("tecnico"), json={
            "nome": "T",
        }, timeout=30)
        assert r.status_code == 403

    def test_tecnico_blocked_put_delete(self):
        # master creates
        c = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json={
            "nome": "TEST_RBAC_C", "identificador_tecnico": _ident(), "tipo": "texto_curto",
        }, timeout=30)
        cid = c.json()["id"]
        assert httpx.put(f"{API}/doc-config/campos/{cid}", headers=auth("tecnico"), json={
            "nome": "hack", "identificador_tecnico": _ident(), "tipo": "texto_curto",
        }, timeout=30).status_code == 403
        assert httpx.delete(f"{API}/doc-config/campos/{cid}", headers=auth("tecnico"),
                            timeout=30).status_code == 403

    def test_pcm_can_create_all_4_types(self):
        # campo
        r1 = httpx.post(f"{API}/doc-config/campos", headers=auth("pcm"), json={
            "nome": "TEST_PCM_C", "identificador_tecnico": _ident(), "tipo": "texto_curto",
        }, timeout=30)
        assert r1.status_code == 200

        # cabecalho
        r2 = httpx.post(f"{API}/doc-config/cabecalhos-rodapes", headers=auth("pcm"), json={
            "nome": "TEST_PCM_CB", "tipo": "cabecalho",
        }, timeout=30)
        assert r2.status_code == 200

        # assinatura
        r3 = httpx.post(f"{API}/doc-config/assinaturas", headers=auth("pcm"), json={
            "nome": "TEST_PCM_ASS", "papel": "executor",
        }, timeout=30)
        assert r3.status_code == 200

        # layout
        r4 = httpx.post(f"{API}/doc-config/layouts", headers=auth("pcm"), json={
            "nome": "TEST_PCM_LAY",
        }, timeout=30)
        assert r4.status_code == 200

    def test_pcm_can_update_campo(self):
        c = httpx.post(f"{API}/doc-config/campos", headers=auth("pcm"), json={
            "nome": "TEST_PCM_UPD", "identificador_tecnico": _ident(), "tipo": "texto_curto",
        }, timeout=30)
        cid = c.json()["id"]
        r = httpx.put(f"{API}/doc-config/campos/{cid}", headers=auth("pcm"), json={
            "nome": "TEST_PCM_UPD_v2", "identificador_tecnico": "ignored", "tipo": "texto_longo",
            "motivo_alteracao": "pcm",
        }, timeout=30)
        assert r.status_code == 200
        assert r.json()["versao"] == 2


# ============== EDGE CASES ==============

class TestEdgeCases:
    def test_get_nonexistent_campo_404(self):
        r = httpx.get(f"{API}/doc-config/campos/nonexistent-xyz",
                      headers=auth("master"), timeout=30)
        assert r.status_code == 404

    def test_restore_nonexistent_version_404(self):
        c = httpx.post(f"{API}/doc-config/campos", headers=auth("master"), json={
            "nome": "TEST_EDGE", "identificador_tecnico": _ident(), "tipo": "texto_curto",
        }, timeout=30)
        cid = c.json()["id"]
        r = httpx.post(f"{API}/doc-config/campos/{cid}/restaurar/999",
                       headers=auth("master"), timeout=30)
        assert r.status_code == 404
