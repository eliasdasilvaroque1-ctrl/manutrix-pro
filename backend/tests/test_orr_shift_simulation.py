"""
ORR — Operational Readiness Review (GATE FINAL)
Simulates a full ASTEC Cedro shift. OBSERVATION MODE: no fixes, only record.
Timeline:
  07:00 Login (Operador)
  07:05 Detect + create OS
  07:10 Verify solicitada excluded from KPIs
  07:15 Supervisor moves to em_analise
  07:20 PCM programada
  07:25 PCM materiais
  07:30 Técnico em_execucao
  07:45 Técnico conclui
  07:50 Dashboard/KPIs
  07:55 Auditoria
  08:00 Historico
  08:05 Preventiva full lifecycle
  08:15 Lubrificação full lifecycle
  08:25 Cross-check
  08:30 Export
  08:35 RBAC final
  Cleanup
"""
import os
import time
import json
import pytest
import requests

BASE_URL = (os.environ.get('REACT_APP_BACKEND_URL')
            or 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"
ORG_ASTEC = "9a232bf2-fc01-4253-813f-8df356be31c1"

# Test users (from /app/memory/test_credentials.md)
USERS = {
    "admin": ("test.admin@maintrix.com", "admin123"),
    "pcm": ("test.pcm@maintrix.com", "pcm123"),
    "sup_mec": ("test.sup.mec@maintrix.com", "sup123"),
    "tec_mec": ("test.mec@maintrix.com", "tec123"),
    "operador": ("test.operador@maintrix.com", "op123"),
    "gerente": ("test.gerente@maintrix.com", "ger123"),
    "viewer": ("rc07v@maintrix.com", "viewer123"),
}

# Shared shift log (JSON-serializable evidence)
SHIFT_LOG = {"events": [], "kpis": {}, "os_ids": {}, "audit_trail": {}, "veredito": {}}


def _log(step, actor, action, result, evidence=None, elapsed_ms=None):
    entry = {
        "step": step,
        "actor": actor,
        "action": action,
        "result": result,
        "evidence": evidence or {},
    }
    if elapsed_ms is not None:
        entry["elapsed_ms"] = round(elapsed_ms, 1)
    SHIFT_LOG["events"].append(entry)
    print(f"[{step}] {actor} → {action}: {result} ({elapsed_ms}ms)")


def _login(role_key):
    email, password = USERS[role_key]
    t0 = time.time()
    r = requests.post(f"{API}/auth/login", json={
        "email": email, "password": password, "organization_id": ORG_ASTEC
    }, timeout=30)
    elapsed = (time.time() - t0) * 1000
    if r.status_code != 200:
        _log("LOGIN", role_key, f"POST /auth/login", f"FAIL {r.status_code}", {"body": r.text[:200]}, elapsed)
        return None
    tok = r.json().get("access_token")
    _log("LOGIN", role_key, "POST /auth/login", "OK", {"has_token": bool(tok)}, elapsed)
    return tok


def H(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# ----------- Fixtures ---------------

@pytest.fixture(scope="module")
def tokens():
    return {role: _login(role) for role in USERS}


@pytest.fixture(scope="module")
def ativos(tokens):
    r = requests.get(f"{API}/ativos", headers=H(tokens["admin"]), timeout=30)
    assert r.status_code == 200, f"ativos list failed: {r.status_code}"
    ativos_list = r.json()
    # find ativos with tag patterns
    return ativos_list


@pytest.fixture(scope="module")
def estoque_item(tokens):
    r = requests.get(f"{API}/estoque", headers=H(tokens["admin"]), timeout=30)
    assert r.status_code == 200
    items = r.json()
    if not items:
        pytest.skip("No estoque items available")
    # pick one with quantity >= 5 to survive consumption
    for it in items:
        if it.get("quantidade", 0) >= 5:
            return it
    return items[0]


# ----------- TIMELINE STEPS ---------------

class TestORRShift:
    """ORR shift simulation — observation only."""

    def test_0700_login_operador(self, tokens):
        """07:00 — Operador logs in, verify Central loads."""
        tok = tokens["operador"]
        assert tok, "Operador login FAIL"
        t0 = time.time()
        r = requests.get(f"{API}/central", headers=H(tok), timeout=30)
        elapsed = (time.time() - t0) * 1000
        _log("07:00", "operador", "GET /central",
             f"{r.status_code}",
             {"body_keys": list(r.json().keys()) if r.status_code == 200 else r.text[:200]},
             elapsed)
        assert r.status_code == 200, f"Central load failed: {r.status_code}"

    def test_0705_operador_creates_corretiva(self, tokens, ativos):
        """07:05 — Operador creates corretiva OS."""
        assert ativos, "no ativos"
        first_ativo = ativos[0]
        payload = {
            "titulo": "ORR - Vibração excessiva no Alimentador AV-01",
            "tipo": "corretiva",
            "disciplina": "mecanica",
            "prioridade": "alta",
            "ativo_id": first_ativo["id"],
        }
        t0 = time.time()
        r = requests.post(f"{API}/ordens-servico", headers=H(tokens["operador"]),
                          json=payload, timeout=30)
        elapsed = (time.time() - t0) * 1000
        _log("07:05", "operador", "POST /ordens-servico (corretiva)",
             f"{r.status_code}",
             {"status": r.status_code, "body": r.json() if r.status_code < 400 else r.text[:300]},
             elapsed)
        assert r.status_code in (200, 201), f"Create OS failed: {r.status_code} {r.text[:300]}"
        os_doc = r.json()
        SHIFT_LOG["os_ids"]["corretiva"] = os_doc.get("id")
        SHIFT_LOG["os_ids"]["corretiva_numero"] = os_doc.get("numero")
        SHIFT_LOG["os_ids"]["corretiva_ativo"] = first_ativo["id"]
        assert os_doc.get("status") == "solicitada", f"status must be solicitada, got {os_doc.get('status')}"

    def test_0710_verify_solicitada_not_in_kpis(self, tokens):
        """07:10 — Solicitada OS must NOT be in KPI backlog but MUST be in OS list."""
        r_kpi = requests.get(f"{API}/kpis", headers=H(tokens["admin"]), timeout=30)
        kpis_before = r_kpi.json() if r_kpi.status_code == 200 else {}
        SHIFT_LOG["kpis"]["before_conclusion"] = kpis_before

        r_list = requests.get(f"{API}/ordens-servico?status=solicitada",
                              headers=H(tokens["admin"]), timeout=30)
        os_list = r_list.json() if r_list.status_code == 200 else []
        found = any(o.get("id") == SHIFT_LOG["os_ids"].get("corretiva") for o in os_list)

        _log("07:10", "admin", "verify solicitada excluded from KPIs / present in list",
             f"kpi={r_kpi.status_code} list={r_list.status_code}",
             {"kpis": kpis_before, "in_list": found,
              "backlog_count": kpis_before.get("backlog_count") if isinstance(kpis_before, dict) else None})
        assert r_kpi.status_code == 200
        assert r_list.status_code == 200
        assert found, "OS solicitada not found in list"

    def test_0715_supervisor_em_analise(self, tokens):
        """07:15 — Supervisor moves to em_analise."""
        os_id = SHIFT_LOG["os_ids"].get("corretiva")
        r = requests.patch(f"{API}/ordens-servico/{os_id}/status",
                           headers=H(tokens["sup_mec"]),
                           json={"new_status": "em_analise"}, timeout=30)
        _log("07:15", "sup_mec", "PATCH status → em_analise", f"{r.status_code}",
             {"body": r.json() if r.status_code < 400 else r.text[:300]})
        # Not asserting hard-pass; record only
        SHIFT_LOG["kpis"]["07_15_status"] = r.status_code

    def test_0720_pcm_programada(self, tokens):
        """07:20 — PCM moves to programada."""
        os_id = SHIFT_LOG["os_ids"].get("corretiva")
        r = requests.patch(f"{API}/ordens-servico/{os_id}/status",
                           headers=H(tokens["pcm"]),
                           json={"new_status": "programada"}, timeout=30)
        _log("07:20", "pcm", "PATCH status → programada", f"{r.status_code}",
             {"body": r.json() if r.status_code < 400 else r.text[:300]})
        # verify data_planejamento set
        rget = requests.get(f"{API}/ordens-servico/{os_id}", headers=H(tokens["pcm"]), timeout=30)
        if rget.status_code == 200:
            data_plan = rget.json().get("data_planejamento")
            _log("07:20", "pcm", "verify data_planejamento set", "OK" if data_plan else "MISSING",
                 {"data_planejamento": data_plan, "status": rget.json().get("status")})

    def test_0725_pcm_add_material(self, tokens, estoque_item):
        """07:25 — PCM adds material, verify estoque decreased."""
        os_id = SHIFT_LOG["os_ids"].get("corretiva")
        est_id = estoque_item["id"]
        est_before = estoque_item.get("quantidade", 0)

        # get before
        rb = requests.get(f"{API}/estoque/{est_id}", headers=H(tokens["pcm"]), timeout=30)
        if rb.status_code == 200:
            est_before = rb.json().get("quantidade", est_before)

        r = requests.post(f"{API}/ordens-servico/{os_id}/materiais",
                          headers=H(tokens["pcm"]),
                          json={"item_estoque_id": est_id, "quantidade": 2}, timeout=30)
        after = None
        ra = requests.get(f"{API}/estoque/{est_id}", headers=H(tokens["pcm"]), timeout=30)
        if ra.status_code == 200:
            after = ra.json().get("quantidade")

        _log("07:25", "pcm", f"POST /ordens-servico/{os_id[:8]}/materiais (qtd=2)",
             f"{r.status_code}",
             {"estoque_before": est_before, "estoque_after": after,
              "expected_after": est_before - 2 if isinstance(est_before, (int, float)) else None,
              "body": r.json() if r.status_code < 400 else r.text[:300]})
        SHIFT_LOG["kpis"]["material"] = {"before": est_before, "after": after,
                                          "status": r.status_code, "item_id": est_id}

    def test_0730_tecnico_em_execucao(self, tokens):
        """07:30 — Técnico moves to em_execucao, verify data_inicio auto-set."""
        os_id = SHIFT_LOG["os_ids"].get("corretiva")
        r = requests.patch(f"{API}/ordens-servico/{os_id}/status",
                           headers=H(tokens["tec_mec"]),
                           json={"new_status": "em_execucao"}, timeout=30)
        rget = requests.get(f"{API}/ordens-servico/{os_id}", headers=H(tokens["tec_mec"]), timeout=30)
        data_inicio = rget.json().get("data_inicio") if rget.status_code == 200 else None
        _log("07:30", "tec_mec", "PATCH → em_execucao", f"{r.status_code}",
             {"data_inicio": data_inicio, "status_after": rget.json().get("status") if rget.status_code == 200 else None})

    def test_0745_tecnico_concluir(self, tokens):
        """07:45 — Técnico conclui OS (90min)."""
        os_id = SHIFT_LOG["os_ids"].get("corretiva")
        payload = {
            "tempo_execucao_minutos": 90,
            "servicos_realizados": "Troca de rolamento do alimentador AV-01. Alinhamento verificado.",
            "skip_foto_check": True,
        }
        r = requests.post(f"{API}/ordens-servico/{os_id}/concluir",
                          headers=H(tokens["tec_mec"]), json=payload, timeout=30)
        rget = requests.get(f"{API}/ordens-servico/{os_id}", headers=H(tokens["tec_mec"]), timeout=30)
        final = rget.json() if rget.status_code == 200 else {}
        _log("07:45", "tec_mec", "POST /concluir", f"{r.status_code}",
             {"final_status": final.get("status"),
              "data_conclusao": final.get("data_conclusao"),
              "tempo": final.get("tempo_execucao_minutos"),
              "servicos": (final.get("servicos_realizados") or "")[:80],
              "body": r.json() if r.status_code < 400 else r.text[:300]})

    def test_0750_kpis_after_conclusion(self, tokens):
        """07:50 — KPIs reflect conclusion."""
        rk = requests.get(f"{API}/kpis", headers=H(tokens["admin"]), timeout=30)
        rs = requests.get(f"{API}/dashboard/stats", headers=H(tokens["admin"]), timeout=30)
        SHIFT_LOG["kpis"]["after_corretiva"] = rk.json() if rk.status_code == 200 else {}
        SHIFT_LOG["kpis"]["dashboard_after_corretiva"] = rs.json() if rs.status_code == 200 else {}
        _log("07:50", "admin", "GET /kpis & /dashboard/stats",
             f"kpi={rk.status_code} stats={rs.status_code}",
             {"kpis": SHIFT_LOG["kpis"]["after_corretiva"],
              "stats": SHIFT_LOG["kpis"]["dashboard_after_corretiva"]})

    def test_0755_audit_trail(self, tokens):
        """07:55 — Audit log complete trail."""
        os_id = SHIFT_LOG["os_ids"].get("corretiva")
        r = requests.get(f"{API}/admin/audit-logs?entity_id={os_id}&limit=100",
                         headers=H(tokens["admin"]), timeout=30)
        logs = r.json() if r.status_code == 200 else []
        if isinstance(logs, dict):
            logs = logs.get("logs", logs.get("items", []))
        actions = [l.get("action") for l in logs] if isinstance(logs, list) else []
        SHIFT_LOG["audit_trail"]["corretiva"] = {"count": len(actions), "actions": actions}
        _log("07:55", "admin", "GET /admin/audit-logs?entity_id=...", f"{r.status_code}",
             {"entries": len(actions), "actions_sequence": actions[:20]})

    def test_0800_historico_ativo(self, tokens):
        """08:00 — OS appears in ativo history."""
        ativo_id = SHIFT_LOG["os_ids"].get("corretiva_ativo")
        os_id = SHIFT_LOG["os_ids"].get("corretiva")
        r = requests.get(f"{API}/ativos/{ativo_id}", headers=H(tokens["admin"]), timeout=30)
        found = False
        os_list = []
        if r.status_code == 200:
            data = r.json()
            os_list = data.get("ordens_servico", [])
            found = any(o.get("id") == os_id for o in os_list)
        _log("08:00", "admin", f"GET /ativos/{ativo_id[:8]}", f"{r.status_code}",
             {"os_in_history": found, "history_count": len(os_list),
              "kpis": r.json().get("kpis") if r.status_code == 200 else None})

    def _full_lifecycle(self, tokens, ativos, tipo, disciplina, prioridade, titulo, tempo, servicos, key):
        """Helper: creates and moves an OS through full lifecycle."""
        payload = {"titulo": titulo, "tipo": tipo, "disciplina": disciplina,
                   "prioridade": prioridade}
        # For lubrificacao it can work without ativo, else pick 2nd ativo
        if tipo != "lubrificacao" and len(ativos) >= 2:
            payload["ativo_id"] = ativos[1]["id"]
        elif ativos:
            payload["ativo_id"] = ativos[0]["id"]

        rc = requests.post(f"{API}/ordens-servico", headers=H(tokens["admin"]),
                           json=payload, timeout=30)
        if rc.status_code not in (200, 201):
            _log(key, "admin", f"POST /ordens-servico ({tipo})", f"FAIL {rc.status_code}",
                 {"body": rc.text[:300]})
            return None
        os_id = rc.json().get("id")
        SHIFT_LOG["os_ids"][tipo] = os_id

        # programada
        r1 = requests.patch(f"{API}/ordens-servico/{os_id}/status",
                            headers=H(tokens["admin"]),
                            json={"new_status": "programada"}, timeout=30)
        # em_execucao
        r2 = requests.patch(f"{API}/ordens-servico/{os_id}/status",
                            headers=H(tokens["admin"]),
                            json={"new_status": "em_execucao"}, timeout=30)
        # concluir
        r3 = requests.post(f"{API}/ordens-servico/{os_id}/concluir",
                           headers=H(tokens["admin"]),
                           json={"tempo_execucao_minutos": tempo,
                                 "servicos_realizados": servicos,
                                 "skip_foto_check": True}, timeout=30)
        rget = requests.get(f"{API}/ordens-servico/{os_id}", headers=H(tokens["admin"]), timeout=30)
        final = rget.json() if rget.status_code == 200 else {}
        _log(key, "admin", f"lifecycle ({tipo})",
             f"create={rc.status_code} prog={r1.status_code} exec={r2.status_code} concl={r3.status_code}",
             {"os_id": os_id, "final_status": final.get("status"),
              "tempo": final.get("tempo_execucao_minutos"),
              "data_inicio": final.get("data_inicio"),
              "data_conclusao": final.get("data_conclusao")})
        return os_id

    def test_0805_preventiva(self, tokens, ativos):
        """08:05 — Preventiva full lifecycle."""
        self._full_lifecycle(
            tokens, ativos, "preventiva", "mecanica", "media",
            "ORR - Preventiva mensal Britador BR-01",
            120,
            "Inspeção visual, lubrificação geral, verificação de folgas",
            "08:05"
        )

    def test_0815_lubrificacao(self, tokens, ativos):
        """08:15 — Lubrificação full lifecycle."""
        self._full_lifecycle(
            tokens, ativos, "lubrificacao", "lubrificacao", "baixa",
            "ORR - Lubrificação Correia TC-01",
            30,
            "Lubrificação de rolamentos com graxa NLGI-2",
            "08:15"
        )

    def test_0825_cross_check(self, tokens):
        """08:25 — All 3 OS concluded → verify KPIs, stats, trend, central."""
        rk = requests.get(f"{API}/kpis", headers=H(tokens["admin"]), timeout=30)
        rs = requests.get(f"{API}/dashboard/stats", headers=H(tokens["admin"]), timeout=30)
        rt = requests.get(f"{API}/dashboard/trend", headers=H(tokens["admin"]), timeout=30)
        rc = requests.get(f"{API}/central", headers=H(tokens["admin"]), timeout=30)

        SHIFT_LOG["kpis"]["final"] = {
            "kpis": rk.json() if rk.status_code == 200 else rk.text[:200],
            "stats": rs.json() if rs.status_code == 200 else rs.text[:200],
            "trend": (rt.json() if rt.status_code == 200 else rt.text[:200]),
            "central_keys": list(rc.json().keys()) if rc.status_code == 200 else rc.text[:200],
        }
        _log("08:25", "admin", "cross-check KPIs/stats/trend/central",
             f"kpi={rk.status_code} stats={rs.status_code} trend={rt.status_code} central={rc.status_code}",
             SHIFT_LOG["kpis"]["final"])

    def test_0830_exports(self, tokens):
        """08:30 — Export OS and Estoque (use real endpoints /api/export/*)."""
        r_os = requests.get(f"{API}/export/ordens-servico", headers=H(tokens["admin"]), timeout=60)
        r_est = requests.get(f"{API}/export/estoque", headers=H(tokens["admin"]), timeout=60)
        _log("08:30", "admin", "GET /export/ordens-servico & /export/estoque",
             f"os={r_os.status_code} est={r_est.status_code}",
             {"os_size": len(r_os.content) if r_os.status_code == 200 else 0,
              "est_size": len(r_est.content) if r_est.status_code == 200 else 0,
              "os_ct": r_os.headers.get("content-type", ""),
              "est_ct": r_est.headers.get("content-type", "")})

        # Also test the endpoints in the problem statement (which don't exist)
        r_os_alt = requests.get(f"{API}/ordens-servico/export/excel", headers=H(tokens["admin"]), timeout=30)
        r_est_alt = requests.get(f"{API}/estoque/export/excel", headers=H(tokens["admin"]), timeout=30)
        _log("08:30", "admin", "GET spec endpoints (/export/excel variants)",
             f"os_alt={r_os_alt.status_code} est_alt={r_est_alt.status_code}",
             {"note": "spec used non-existent /export/excel; real endpoints are /api/export/*"})

    def test_0835_rbac_final(self, tokens):
        """08:35 — RBAC: Operador can see but not change status; Viewer cannot see; Gerente sees dashboard."""
        os_id = SHIFT_LOG["os_ids"].get("corretiva")
        # 1) Operador can see OS
        r_op_get = requests.get(f"{API}/ordens-servico/{os_id}",
                                headers=H(tokens["operador"]), timeout=30)
        # Operador tries to change status (create dummy OS first to avoid altering concluida)
        # Better: try to PATCH the corretiva OS status → expect 403
        r_op_patch = requests.patch(f"{API}/ordens-servico/{os_id}/status",
                                    headers=H(tokens["operador"]),
                                    json={"new_status": "em_analise"}, timeout=30)

        # 2) Viewer cannot see OS list
        r_v = requests.get(f"{API}/ordens-servico", headers=H(tokens["viewer"]), timeout=30)
        viewer_can_see_orr = False
        if r_v.status_code == 200:
            lst = r_v.json()
            if isinstance(lst, list):
                viewer_can_see_orr = any(
                    "ORR -" in (o.get("titulo") or "") for o in lst
                )

        # 3) Gerente sees dashboard
        r_g_kpi = requests.get(f"{API}/kpis", headers=H(tokens["gerente"]), timeout=30)
        r_g_stats = requests.get(f"{API}/dashboard/stats", headers=H(tokens["gerente"]), timeout=30)

        _log("08:35", "operador", f"GET OS then PATCH status",
             f"get={r_op_get.status_code} patch={r_op_patch.status_code}",
             {"expected_patch": "403", "actual_patch": r_op_patch.status_code})
        _log("08:35", "viewer", "GET /ordens-servico",
             f"{r_v.status_code}",
             {"viewer_can_see_orr_os": viewer_can_see_orr,
              "count": len(r_v.json()) if r_v.status_code == 200 and isinstance(r_v.json(), list) else "n/a"})
        _log("08:35", "gerente", "GET /kpis & /dashboard/stats",
             f"kpi={r_g_kpi.status_code} stats={r_g_stats.status_code}",
             {"can_see_dashboard": r_g_kpi.status_code == 200 and r_g_stats.status_code == 200})

    def test_zzz_cleanup(self, tokens):
        """CLEANUP: soft-delete ORR OS + restore estoque if possible."""
        cleanup_results = {}
        for tipo, os_id in list(SHIFT_LOG["os_ids"].items()):
            if not isinstance(os_id, str) or not os_id or tipo.endswith("_numero") or tipo.endswith("_ativo"):
                continue
            r = requests.delete(f"{API}/ordens-servico/{os_id}",
                                headers=H(tokens["admin"]), timeout=30)
            cleanup_results[tipo] = r.status_code

        # Restore estoque
        mat = SHIFT_LOG["kpis"].get("material", {})
        if mat.get("before") is not None and mat.get("after") is not None and mat.get("item_id"):
            item_id = mat["item_id"]
            try:
                # try to restore via PUT
                r = requests.put(f"{API}/estoque/{item_id}",
                                 headers=H(tokens["admin"]),
                                 json={"quantidade": mat["before"]}, timeout=30)
                cleanup_results["estoque_restore"] = r.status_code
            except Exception as e:
                cleanup_results["estoque_restore_err"] = str(e)[:100]

        _log("CLEANUP", "admin", "DELETE ORR OS & restore estoque", "done", cleanup_results)

    def test_zzzz_final_dump(self, tokens):
        """Write full shift log to disk."""
        out = "/app/test_reports/orr_shift_log.json"
        with open(out, "w") as f:
            json.dump(SHIFT_LOG, f, indent=2, default=str)
        print(f"\n=== ORR SHIFT LOG WRITTEN: {out} ===")
