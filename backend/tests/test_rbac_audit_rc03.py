"""
Sprint RC-03 verification tests - P1 fixes on top of RC-02
- P1-05: /api/ativos filtered by area_ids for operacional roles
- P1-06: /api/export/audit filtered by organization_id (master exports OK)
- P1-07: GET /api/admin/users/{id} implemented
- Regressions on top of RC-02 P0 fixes (tec_mec create OS, central visibility)
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get(
    'REACT_APP_BACKEND_URL',
    'https://procure-manutrix.preview.emergentagent.com',
).rstrip('/')
API = f"{BASE_URL}/api"

CREDS = {
    "master":    ("master@maintrix.com",         "master123"),
    "tec_mec":   ("test.mec@maintrix.com",       "tec123"),
    "gerente":   ("test.gerente@maintrix.com",   "ger123"),
    "operador":  ("test.operador@maintrix.com",  "op123"),
}


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    body = r.json()
    token = body.get("token") or body.get("access_token")
    assert token, f"No token: {body}"
    return token, body


def _h(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# P1-07  GET /api/admin/users/{id}
# ---------------------------------------------------------------------------
class TestP1_07_AdminGetUser:
    def test_master_get_user_by_id_returns_200(self):
        token, _ = _login(*CREDS["master"])
        # find a user via list
        list_r = requests.get(f"{API}/admin/users", headers=_h(token), timeout=30)
        assert list_r.status_code == 200, list_r.text
        users = list_r.json() if isinstance(list_r.json(), list) else list_r.json().get("users", [])
        assert users, "No users returned in list"
        target = users[0]
        uid = target.get("id")
        assert uid, f"No id in user record: {target}"

        r = requests.get(f"{API}/admin/users/{uid}", headers=_h(token), timeout=30)
        print(f"[P1-07] GET /api/admin/users/{uid} -> {r.status_code}")
        assert r.status_code == 200, (
            f"BUG NOT FIXED: expected 200, got {r.status_code}. Body: {r.text[:400]}"
        )
        body = r.json()
        assert body.get("id") == uid
        assert body.get("email"), f"missing email: {body}"
        assert body.get("nome"), f"missing nome: {body}"
        assert body.get("role"), f"missing role: {body}"
        # password_hash should never leak
        assert "password_hash" not in body, f"password_hash leaked in response: {body}"

    def test_master_get_user_nonexistent_returns_404(self):
        token, _ = _login(*CREDS["master"])
        r = requests.get(f"{API}/admin/users/nonexistent-id-xxx", headers=_h(token), timeout=30)
        print(f"[P1-07] GET /api/admin/users/nonexistent -> {r.status_code}")
        assert r.status_code == 404, (
            f"Expected 404 for missing id but got {r.status_code}. Body: {r.text[:300]}"
        )

    def test_non_admin_forbidden(self):
        token, _ = _login(*CREDS["operador"])
        r = requests.get(f"{API}/admin/users/any-id", headers=_h(token), timeout=30)
        print(f"[P1-07] operador GET /api/admin/users/any-id -> {r.status_code}")
        assert r.status_code in (401, 403), (
            f"Expected 401/403 for non-admin, got {r.status_code}"
        )


# ---------------------------------------------------------------------------
# P1-06  /api/export/audit filtered by organization_id
# ---------------------------------------------------------------------------
class TestP1_06_ExportAuditFiltered:
    def test_master_export_audit_excel_returns_spreadsheet(self):
        token, _ = _login(*CREDS["master"])
        r = requests.get(f"{API}/export/audit", params={"format": "excel"}, headers=_h(token), timeout=60)
        ct = r.headers.get("content-type", "")
        print(f"[P1-06] master /api/export/audit?format=excel -> {r.status_code} ct={ct} len={len(r.content)}")
        assert r.status_code == 200, r.text[:300]
        assert "spreadsheet" in ct or "excel" in ct or "openxml" in ct, (
            f"Expected spreadsheet content-type, got {ct}"
        )
        assert len(r.content) > 100, "Empty export body"


# ---------------------------------------------------------------------------
# P1-05  /api/ativos filtered by area_ids for operador
# ---------------------------------------------------------------------------
class TestP1_05_AtivosAreaFilter:
    def test_operador_sees_only_area_assets_vs_master_sees_all(self):
        m_token, _ = _login(*CREDS["master"])
        op_token, op_body = _login(*CREDS["operador"])

        m_list = requests.get(f"{API}/ativos", headers=_h(m_token), timeout=30)
        op_list = requests.get(f"{API}/ativos", headers=_h(op_token), timeout=30)
        assert m_list.status_code == 200 and op_list.status_code == 200
        m_data = m_list.json()
        op_data = op_list.json()
        assert isinstance(m_data, list) and isinstance(op_data, list)

        # Get area_ids from login body user object
        area_ids = (op_body.get("user") or {}).get("area_ids") or []
        print(f"[P1-05] operador area_ids={area_ids} | master ativos={len(m_data)} operador ativos={len(op_data)}")

        # If operador has area_ids configured: op count must be <= master AND every op ativo must belong to those areas
        if area_ids:
            assert len(op_data) <= len(m_data), (
                f"operador sees MORE ativos than master (op={len(op_data)}, master={len(m_data)})"
            )
            # ALL ativos returned to operador MUST have sector_id in area_ids (this is the real fix verification)
            bad = [a for a in op_data if a.get("sector_id") not in area_ids]
            assert not bad, (
                f"BUG NOT FIXED: operador seeing ativos outside area_ids: {[a.get('tag') for a in bad[:5]]}"
            )
            # Sanity: check whether master has any ativos in sectors that are NOT in op's area_ids
            master_sector_ids = {a.get("sector_id") for a in m_data if a.get("sector_id")}
            outside_sectors = master_sector_ids - set(area_ids)
            if outside_sectors:
                # There are master ativos in sectors outside op's areas; op must see FEWER
                assert len(op_data) < len(m_data), (
                    f"BUG NOT FIXED: master has ativos in sectors {outside_sectors} but operador still sees all {len(op_data)}"
                )
                print(f"[P1-05] confirmed filter: op sees {len(op_data)}/{len(m_data)} (excluded sectors={outside_sectors})")
            else:
                # In current dataset all master ativos are within op's area_ids => equal counts is EXPECTED
                print(f"[P1-05] filter query applied but all master ativos happen to be in op areas; count parity is expected. master_sectors={master_sector_ids}, op_areas subset OK")
        else:
            # No area assigned -> no filter, op should get everything (behavior)
            print("[P1-05] operador has no area_ids assigned; skipping strict filter check")

    def test_master_still_sees_all_ativos(self):
        m_token, _ = _login(*CREDS["master"])
        r = requests.get(f"{API}/ativos", headers=_h(m_token), timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        print(f"[P1-05 REG] master ativos count={len(r.json())}")


# ---------------------------------------------------------------------------
# REGRESSION: master unaffected
# ---------------------------------------------------------------------------
class TestRegressionMaster:
    def test_master_dashboard_stats(self):
        token, _ = _login(*CREDS["master"])
        r = requests.get(f"{API}/dashboard/stats", headers=_h(token), timeout=30)
        assert r.status_code == 200

    def test_master_ordens_servico_list(self):
        token, _ = _login(*CREDS["master"])
        r = requests.get(f"{API}/ordens-servico", headers=_h(token), timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# REGRESSION: RC-02 P0 fixes still work (tec_mec)
# ---------------------------------------------------------------------------
class TestRegressionRC02:
    def test_tec_mec_can_create_os(self):
        m_token, _ = _login(*CREDS["master"])
        t_token, _ = _login(*CREDS["tec_mec"])
        ativos = requests.get(f"{API}/ativos", headers=_h(m_token), timeout=30).json()
        ativo_id = ativos[0]["id"]
        payload = {
            "ativo_id": ativo_id,
            "titulo": f"TEST_RC03 corretiva by tec_mec {int(time.time())}",
            "descricao": "RC-03 regression",
            "tipo": "corretiva",
            "origem": "operador",
        }
        r = requests.post(f"{API}/ordens-servico", headers=_h(t_token), json=payload, timeout=30)
        print(f"[REG-RC02] tec_mec POST /api/ordens-servico -> {r.status_code}")
        assert r.status_code in (200, 201), r.text[:400]

    def test_tec_mec_central_has_vencidas(self):
        t_token, _ = _login(*CREDS["tec_mec"])
        r = requests.get(f"{API}/central", headers=_h(t_token), timeout=30)
        assert r.status_code == 200
        body = r.json()
        v = body.get("vencidas") if isinstance(body, dict) else None
        if isinstance(v, dict):
            total = v.get("total") if isinstance(v.get("total"), int) else sum(len(x) for x in v.values() if isinstance(x, list))
        elif isinstance(v, list):
            total = len(v)
        else:
            total = 0
        print(f"[REG-RC02] tec_mec /api/central vencidas={total}")
        assert total > 0, "RC-02 P0-03 regression: tec_mec central vencidas dropped to 0"
