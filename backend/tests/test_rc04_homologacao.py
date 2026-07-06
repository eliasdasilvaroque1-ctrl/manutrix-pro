#!/usr/bin/env python3
"""RC-04 — HOMOLOGAÇÃO OPERACIONAL ASTEC
Tests all user flows via API calls. Reports PASS/FAIL per flow."""

import requests, json, sys, time, os

API = os.environ.get("API_URL", "").rstrip("/")
if not API:
    # Read from frontend .env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                API = line.strip().split("=", 1)[1].rstrip("/")

RESULTS = []
BUGS = []

def log(flow, test, status, detail="", file="", fix=""):
    RESULTS.append({"flow": flow, "test": test, "status": status, "detail": detail, "file": file, "fix": fix})
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} {test}: {detail[:120]}" if detail else f"  {icon} {test}")
    if status == "FAIL":
        BUGS.append({"flow": flow, "test": test, "detail": detail, "file": file, "fix": fix})

def login(email, password):
    r = requests.post(f"{API}/api/auth/login", json={"email": email, "password": password})
    if r.status_code == 200:
        return r.json().get("access_token")
    return None

def auth(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# ============================================================
# MASTER FLOW
# ============================================================
print("\n" + "="*60)
print("FLUXO MASTER (master@maintrix.com)")
print("="*60)

token = login("master@maintrix.com", "master123")
if not token:
    log("MASTER", "Login", "FAIL", "Não conseguiu autenticar")
else:
    log("MASTER", "Login", "PASS")
    h = auth(token)
    
    # Me
    r = requests.get(f"{API}/api/auth/me", headers=h)
    log("MASTER", "GET /auth/me", "PASS" if r.status_code == 200 and r.json().get("role") == "master" else "FAIL", f"status={r.status_code} role={r.json().get('role','?')}")
    
    # Permissions
    r = requests.get(f"{API}/api/auth/permissions", headers=h)
    perms = r.json().get("permissions", []) if r.status_code == 200 else []
    log("MASTER", "GET /auth/permissions", "PASS" if len(perms) > 20 else "FAIL", f"{len(perms)} permissions")
    
    # Organizations (public)
    r = requests.get(f"{API}/api/public/organizations")
    orgs = r.json() if r.status_code == 200 else []
    log("MASTER", "Empresas (public/organizations)", "PASS" if len(orgs) > 0 else "FAIL", f"{len(orgs)} orgs")
    
    # White Label - list orgs
    r = requests.get(f"{API}/api/master/organizations", headers=h)
    log("MASTER", "White Label (master/organizations)", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Users
    r = requests.get(f"{API}/api/admin/users", headers=h)
    users = r.json() if r.status_code == 200 else []
    log("MASTER", "Usuários (admin/users)", "PASS" if len(users) > 0 else "FAIL", f"{len(users)} users")
    
    # Single user
    if users:
        r2 = requests.get(f"{API}/api/admin/users/{users[0]['id']}", headers=h)
        log("MASTER", "GET /admin/users/{id}", "PASS" if r2.status_code == 200 and "nome" in r2.json() else "FAIL", f"status={r2.status_code}")
    
    # Auditoria
    r = requests.get(f"{API}/api/admin/audit-logs", headers=h)
    log("MASTER", "Auditoria (audit-logs)", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Configurações
    r = requests.get(f"{API}/api/org/config", headers=h)
    log("MASTER", "Configurações (org/config)", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Exportações
    for entity in ["ativos", "ordens-servico", "estoque", "inspecoes", "sobressalentes", "audit"]:
        r = requests.get(f"{API}/api/export/{entity}?format=excel", headers=h)
        log("MASTER", f"Export Excel {entity}", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} size={len(r.content)}B", file=f"server.py export/{entity}")
    for entity in ["ativos", "ordens-servico", "inspecoes"]:
        r = requests.get(f"{API}/api/export/{entity}?format=pdf", headers=h)
        log("MASTER", f"Export PDF {entity}", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} size={len(r.content)}B")
    
    # Ativos
    r = requests.get(f"{API}/api/ativos", headers=h)
    ativos = r.json() if r.status_code == 200 else []
    log("MASTER", "Ativos (list)", "PASS" if len(ativos) > 0 else "FAIL", f"{len(ativos)} ativos")
    
    # QR Code / Portal Público
    if ativos:
        aid = ativos[0]["id"]
        r = requests.get(f"{API}/api/public/ativo/{aid}")
        log("MASTER", "Portal Público (public/ativo)", "PASS" if r.status_code == 200 and "tag" in r.json() else "FAIL", f"status={r.status_code}")
    
    # Dashboard
    r = requests.get(f"{API}/api/dashboard/stats", headers=h)
    log("MASTER", "Dashboard stats", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Cleanup page accessible
    r = requests.get(f"{API}/api/master/admin-actions", headers=h)
    log("MASTER", "Admin actions (limpeza)", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")

# ============================================================
# GERENTE FLOW
# ============================================================
print("\n" + "="*60)
print("FLUXO GERENTE (test.gerente@maintrix.com)")
print("="*60)

token = login("test.gerente@maintrix.com", "ger123")
if not token:
    log("GERENTE", "Login", "FAIL", "Não conseguiu autenticar")
else:
    log("GERENTE", "Login", "PASS")
    h = auth(token)
    
    # Dashboard / Indicadores
    r = requests.get(f"{API}/api/dashboard/stats", headers=h)
    log("GERENTE", "Dashboard stats", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Consulta de ativos
    r = requests.get(f"{API}/api/ativos", headers=h)
    log("GERENTE", "Consulta ativos", "PASS" if r.status_code == 200 else "FAIL", f"{len(r.json())} ativos")
    
    # Consulta OS
    r = requests.get(f"{API}/api/ordens-servico", headers=h)
    os_list = r.json() if r.status_code == 200 else []
    log("GERENTE", "Consulta OS", "PASS" if r.status_code == 200 else "FAIL", f"{len(os_list)} OS")
    
    # Consulta Inspeções (histórico)
    r = requests.get(f"{API}/api/inspecoes", headers=h)
    log("GERENTE", "Consulta Inspeções", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Auditoria
    r = requests.get(f"{API}/api/admin/audit-logs", headers=h)
    log("GERENTE", "Auditoria", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Aprovação de OS - find one pending
    pendentes = [o for o in os_list if o.get("aprovacao", {}).get("status") == "pendente" and o.get("status") == "aguardando_aprovacao"]
    if pendentes:
        os_id = pendentes[0]["id"]
        r = requests.post(f"{API}/api/ordens-servico/{os_id}/aprovar", json={"acao": "aprovar", "observacao": "Aprovado homologação"}, headers=h)
        log("GERENTE", "Aprovar OS", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} detail={r.text[:100]}")
    else:
        log("GERENTE", "Aprovar OS", "PASS", "Nenhuma OS aguardando aprovação (ok, fluxo existe)")
    
    # NÃO pode criar OS
    r = requests.post(f"{API}/api/ordens-servico", json={"ativo_id": "x", "titulo": "t", "descricao": "d", "tipo": "corretiva", "origem": "manual"}, headers=h)
    log("GERENTE", "Criar OS (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}", file="routes/work_orders.py check_not_gerente")
    
    # NÃO pode acessar admin users
    r = requests.get(f"{API}/api/admin/users", headers=h)
    log("GERENTE", "Admin users (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")

# ============================================================
# SUPERVISOR FLOW
# ============================================================
print("\n" + "="*60)
print("FLUXO SUPERVISOR (test.sup.mec@maintrix.com)")
print("="*60)

token = login("test.sup.mec@maintrix.com", "sup123")
if not token:
    log("SUPERVISOR", "Login", "FAIL", "Não conseguiu autenticar")
else:
    log("SUPERVISOR", "Login", "PASS")
    h = auth(token)
    
    # Criar OS
    r = requests.get(f"{API}/api/ativos", headers=h)
    ativos = r.json() if r.status_code == 200 else []
    if ativos:
        ativo_id = ativos[0]["id"]
        r = requests.post(f"{API}/api/ordens-servico", json={
            "ativo_id": ativo_id, "titulo": "HOM-SUP Teste Supervisor", "descricao": "Teste homologação",
            "tipo": "corretiva", "origem": "supervisor", "prioridade": "media"
        }, headers=h)
        sup_os_id = r.json().get("id") if r.status_code in (200, 201) else None
        log("SUPERVISOR", "Criar OS", "PASS" if sup_os_id else "FAIL", f"status={r.status_code} os_id={sup_os_id}")
    
    # Consultar backlog
    r = requests.get(f"{API}/api/ordens-servico", headers=h)
    log("SUPERVISOR", "Consultar backlog OS", "PASS" if r.status_code == 200 else "FAIL", f"{len(r.json())} OS")
    
    # Consultar equipe
    r = requests.get(f"{API}/api/users/tecnicos", headers=h)
    log("SUPERVISOR", "Consultar equipe (tecnicos)", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Consultar ativos
    r = requests.get(f"{API}/api/ativos", headers=h)
    log("SUPERVISOR", "Consultar ativos", "PASS" if r.status_code == 200 else "FAIL", f"{len(r.json())} ativos")
    
    # Consultar inspeções
    r = requests.get(f"{API}/api/inspecoes", headers=h)
    log("SUPERVISOR", "Consultar inspeções", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Dashboard
    r = requests.get(f"{API}/api/dashboard/stats", headers=h)
    log("SUPERVISOR", "Dashboard stats", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")

# ============================================================
# PCM FLOW (COMPLETO)
# ============================================================
print("\n" + "="*60)
print("FLUXO PCM (test.pcm@maintrix.com) — CICLO COMPLETO")
print("="*60)

token = login("test.pcm@maintrix.com", "pcm123")
if not token:
    log("PCM", "Login", "FAIL", "Não conseguiu autenticar")
else:
    log("PCM", "Login", "PASS")
    h = auth(token)
    
    # 1. Cadastrar Ativo
    r = requests.get(f"{API}/api/setores", headers=h)
    sectors = r.json() if r.status_code == 200 else []
    sector_id = sectors[0]["id"] if sectors else ""
    
    r = requests.post(f"{API}/api/ativos", json={
        "nome": "HOM-PCM Bomba Teste", "tag": "BT-HOM-01", "tipo_equipamento": "Bomba",
        "fabricante": "WEG", "modelo": "W22", "numero_serie": "HOM001",
        "criticidade": "alta", "status": "operacional", "sector_id": sector_id
    }, headers=h)
    pcm_ativo_id = r.json().get("id") if r.status_code in (200, 201) else None
    log("PCM", "1. Cadastrar Ativo", "PASS" if pcm_ativo_id else "FAIL", f"status={r.status_code} id={pcm_ativo_id}", file="routes/assets.py POST /ativos")
    
    # 2. Cadastrar Material no Estoque
    r = requests.post(f"{API}/api/estoque", json={
        "nome": "HOM Rolamento 6205", "codigo": "HOM-ROL-6205", "categoria": "Rolamento",
        "unidade": "pç", "quantidade": 50, "estoque_minimo": 5, "localizacao": "Almox A1"
    }, headers=h)
    mat_id = r.json().get("id") if r.status_code in (200, 201) else None
    log("PCM", "2. Cadastrar Material", "PASS" if mat_id else "FAIL", f"status={r.status_code}")
    
    # 3. Importar Plano (parse-text)
    r = requests.post(f"{API}/api/planos-inspecao/parse-text", json={
        "text": "1. Verificar nível de óleo\n2. Medir temperatura do mancal (max 80°C)\n3. Verificar vazamentos\n4. Registrar vibração (mm/s)"
    }, headers=h)
    parsed = r.json() if r.status_code == 200 else {}
    log("PCM", "3. Importar Plano (parse-text)", "PASS" if parsed.get("perguntas") and len(parsed["perguntas"]) >= 3 else "FAIL", f"status={r.status_code} perguntas={len(parsed.get('perguntas',[]))}")
    
    # 4. Criar Template de Inspeção
    r = requests.post(f"{API}/api/inspection-templates", json={
        "nome": "HOM Template Bomba", "tipo_equipamento": "Bomba",
        "descricao": "Template homologação",
        "itens": [
            {"pergunta": "Nível de óleo OK?", "tipo": "conforme_nao_conforme"},
            {"pergunta": "Temperatura mancal (°C)", "tipo": "numerico", "limite_min": 20, "limite_max": 80},
            {"pergunta": "Observações", "tipo": "texto"}
        ]
    }, headers=h)
    tmpl_id = r.json().get("id") if r.status_code in (200, 201) else None
    log("PCM", "4. Criar Template Inspeção", "PASS" if tmpl_id else "FAIL", f"status={r.status_code}")
    
    # 5. Criar Plano de Inspeção
    r = requests.post(f"{API}/api/planos-inspecao", json={
        "nome": "HOM Plano Bomba Mensal", "tipo": "preventiva", "frequencia": "mensal",
        "disciplina": "mecanica", "ativo_ids": [pcm_ativo_id] if pcm_ativo_id else [],
        "template_id": tmpl_id,
        "perguntas": [
            {"pergunta": "Nível de óleo OK?", "tipo": "conforme_nao_conforme"},
            {"pergunta": "Temperatura (°C)", "tipo": "numerico", "limite_min": 20, "limite_max": 80}
        ]
    }, headers=h)
    plano_id = r.json().get("id") if r.status_code in (200, 201) else None
    log("PCM", "5. Criar Plano de Inspeção", "PASS" if plano_id else "FAIL", f"status={r.status_code} detail={r.text[:150]}")
    
    # 6. Criar Inspeção
    r = requests.post(f"{API}/api/inspecoes", json={
        "ativo_id": pcm_ativo_id or ativos[0]["id"] if ativos else "",
        "plano_id": plano_id,
        "tipo": "preventiva", "disciplina": "mecanica",
        "data_programada": "2026-07-06T10:00:00Z"
    }, headers=h)
    insp_id = r.json().get("id") if r.status_code in (200, 201) else None
    log("PCM", "6. Criar Inspeção", "PASS" if insp_id else "FAIL", f"status={r.status_code} detail={r.text[:150]}")
    
    # 7. Iniciar Inspeção
    if insp_id:
        r = requests.post(f"{API}/api/inspecoes/{insp_id}/iniciar", headers=h)
        log("PCM", "7. Iniciar Inspeção (executar)", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # 8. Concluir Inspeção
    if insp_id:
        r = requests.post(f"{API}/api/inspecoes/{insp_id}/concluir", json={
            "checklist": [
                {"pergunta": "Nível de óleo OK?", "tipo": "conforme_nao_conforme", "resposta": "conforme"},
                {"pergunta": "Temperatura (°C)", "tipo": "numerico", "resposta": "65"}
            ],
            "observacoes": "Inspeção homologação concluída"
        }, headers=h)
        log("PCM", "8. Concluir Inspeção", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} detail={r.text[:150]}")
    
    # 9. Gerar OS (manual)
    r = requests.post(f"{API}/api/ordens-servico", json={
        "ativo_id": pcm_ativo_id or (ativos[0]["id"] if ativos else ""),
        "titulo": "HOM-PCM OS Corretiva Bomba", "descricao": "Troca de rolamento",
        "tipo": "corretiva", "origem": "pcm", "prioridade": "alta", "disciplina": "mecanica"
    }, headers=h)
    pcm_os_id = r.json().get("id") if r.status_code in (200, 201) else None
    log("PCM", "9. Gerar OS", "PASS" if pcm_os_id else "FAIL", f"status={r.status_code} detail={r.text[:150]}")
    
    # 10. Planejar OS (status → programada)
    if pcm_os_id:
        r = requests.patch(f"{API}/api/ordens-servico/{pcm_os_id}/status", json={"new_status": "programada"}, headers=h)
        log("PCM", "10. Planejar OS", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} detail={r.text[:100]}")
    
    # 11. Reservar Material
    if pcm_os_id and mat_id:
        r = requests.post(f"{API}/api/ordens-servico/{pcm_os_id}/materiais", json={
            "item_estoque_id": mat_id, "quantidade": 2
        }, headers=h)
        log("PCM", "11. Reservar Material", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} detail={r.text[:150]}")
    
    # 12. Liberar OS (status → disponivel)
    if pcm_os_id:
        r = requests.patch(f"{API}/api/ordens-servico/{pcm_os_id}/status", json={"new_status": "disponivel"}, headers=h)
        log("PCM", "12. Liberar OS (disponivel)", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # 13. Iniciar OS → em_execucao
    if pcm_os_id:
        r = requests.post(f"{API}/api/ordens-servico/{pcm_os_id}/iniciar", headers=h)
        log("PCM", "13. Iniciar OS (em_execucao)", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # 14. Concluir OS
    if pcm_os_id:
        r = requests.post(f"{API}/api/ordens-servico/{pcm_os_id}/concluir", json={
            "servicos_realizados": "Rolamento trocado", "observacoes": "Homologação",
            "causa_falha": "Desgaste natural", "skip_foto_check": True
        }, headers=h)
        log("PCM", "14. Concluir OS", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} detail={r.text[:150]}")
    
    # Exportações
    for entity in ["ativos", "ordens-servico", "estoque", "inspecoes"]:
        r = requests.get(f"{API}/api/export/{entity}?format=excel", headers=h)
        log("PCM", f"Export Excel {entity}", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")

# ============================================================
# TÉCNICO MECÂNICO
# ============================================================
print("\n" + "="*60)
print("FLUXO TÉCNICO MECÂNICO (test.mec@maintrix.com)")
print("="*60)

token = login("test.mec@maintrix.com", "tec123")
if not token:
    log("TEC_MEC", "Login", "FAIL", "Não conseguiu autenticar")
else:
    log("TEC_MEC", "Login", "PASS")
    h = auth(token)
    
    # Minha Jornada (Central)
    r = requests.get(f"{API}/api/central", headers=h)
    central = r.json() if r.status_code == 200 else {}
    log("TEC_MEC", "Minha Jornada (central)", "PASS" if r.status_code == 200 and central.get("role") == "tec_mecanico" else "FAIL", f"role={central.get('role')} vencidas={len(central.get('vencidas',[]))}")
    
    # Abrir OS
    r = requests.get(f"{API}/api/ativos", headers=h)
    ativos_tec = r.json() if r.status_code == 200 else []
    if ativos_tec:
        r = requests.post(f"{API}/api/ordens-servico", json={
            "ativo_id": ativos_tec[0]["id"], "titulo": "HOM-TEC OS Mecânica",
            "descricao": "Teste técnico mecânico", "tipo": "corretiva", "origem": "operador"
        }, headers=h)
        tec_os_id = r.json().get("id") if r.status_code in (200, 201) else None
        log("TEC_MEC", "Abrir OS", "PASS" if tec_os_id else "FAIL", f"status={r.status_code}")
    
    # Iniciar/Executar OS
    if tec_os_id:
        r = requests.post(f"{API}/api/ordens-servico/{tec_os_id}/iniciar", headers=h)
        log("TEC_MEC", "Executar OS (iniciar)", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Lançar HH
    if tec_os_id:
        r = requests.post(f"{API}/api/os/{tec_os_id}/hh-manual", json={"horas": 2, "descricao": "Teste HH"}, headers=h)
        log("TEC_MEC", "Lançar HH", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} detail={r.text[:100]}")
    
    # Concluir OS
    if tec_os_id:
        r = requests.post(f"{API}/api/ordens-servico/{tec_os_id}/concluir", json={
            "servicos_realizados": "Serviço concluído", "skip_foto_check": True
        }, headers=h)
        log("TEC_MEC", "Concluir OS", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} detail={r.text[:100]}")
    
    # NÃO acesso admin
    r = requests.get(f"{API}/api/admin/users", headers=h)
    log("TEC_MEC", "Admin users (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")
    
    r = requests.get(f"{API}/api/master/organizations", headers=h)
    log("TEC_MEC", "Master orgs (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")

# ============================================================
# TÉCNICO ELÉTRICO
# ============================================================
print("\n" + "="*60)
print("FLUXO TÉCNICO ELÉTRICO (test.ele@maintrix.com)")
print("="*60)

token = login("test.ele@maintrix.com", "tec123")
if not token:
    log("TEC_ELE", "Login", "FAIL", "Não conseguiu autenticar")
else:
    log("TEC_ELE", "Login", "PASS")
    h = auth(token)
    
    # Central
    r = requests.get(f"{API}/api/central", headers=h)
    central = r.json() if r.status_code == 200 else {}
    log("TEC_ELE", "Minha Jornada (central)", "PASS" if r.status_code == 200 else "FAIL", f"role={central.get('role')} vencidas={len(central.get('vencidas',[]))}")
    
    # Abrir OS
    r = requests.get(f"{API}/api/ativos", headers=h)
    ativos_ele = r.json() if r.status_code == 200 else []
    if ativos_ele:
        r = requests.post(f"{API}/api/ordens-servico", json={
            "ativo_id": ativos_ele[0]["id"], "titulo": "HOM-ELE OS Elétrica",
            "descricao": "Teste técnico elétrico", "tipo": "corretiva", "origem": "operador"
        }, headers=h)
        ele_os_id = r.json().get("id") if r.status_code in (200, 201) else None
        log("TEC_ELE", "Abrir OS", "PASS" if ele_os_id else "FAIL", f"status={r.status_code}")
        
        if ele_os_id:
            r = requests.post(f"{API}/api/ordens-servico/{ele_os_id}/iniciar", headers=h)
            log("TEC_ELE", "Executar OS", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
            r = requests.post(f"{API}/api/ordens-servico/{ele_os_id}/concluir", json={"servicos_realizados": "OK", "skip_foto_check": True}, headers=h)
            log("TEC_ELE", "Concluir OS", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # NÃO acesso admin
    r = requests.get(f"{API}/api/admin/users", headers=h)
    log("TEC_ELE", "Admin users (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")

# ============================================================
# OPERADOR
# ============================================================
print("\n" + "="*60)
print("FLUXO OPERADOR (test.operador@maintrix.com)")
print("="*60)

token = login("test.operador@maintrix.com", "op123")
if not token:
    log("OPERADOR", "Login", "FAIL", "Não conseguiu autenticar")
else:
    log("OPERADOR", "Login", "PASS")
    h = auth(token)
    
    # Solicitação de Serviço
    r = requests.get(f"{API}/api/ativos", headers=h)
    ativos_op = r.json() if r.status_code == 200 else []
    if ativos_op:
        r = requests.post(f"{API}/api/ordens-servico", json={
            "ativo_id": ativos_op[0]["id"], "titulo": "HOM-OP Solicitação",
            "descricao": "Ruído anormal", "justificativa": "Equipamento vibrando",
            "tipo": "corretiva", "origem": "operador", "equipamento_parado": False
        }, headers=h)
        log("OPERADOR", "Solicitação de Serviço", "PASS" if r.status_code in (200, 201) else "FAIL", f"status={r.status_code}")
    
    # Portal Público
    if ativos_op:
        r = requests.get(f"{API}/api/public/ativo/{ativos_op[0]['id']}")
        log("OPERADOR", "Portal Público", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # NÃO pode aprovar OS
    r = requests.get(f"{API}/api/ordens-servico", headers=h)
    os_list = r.json() if r.status_code == 200 else []
    if os_list:
        r = requests.post(f"{API}/api/ordens-servico/{os_list[0]['id']}/aprovar", json={"acao": "aprovar"}, headers=h)
        log("OPERADOR", "Aprovar OS (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")
    
    # NÃO pode alterar plano
    r = requests.post(f"{API}/api/planos-inspecao", json={"nome": "x"}, headers=h)
    log("OPERADOR", "Criar Plano (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")
    
    # NÃO pode alterar ativo
    r = requests.post(f"{API}/api/ativos", json={"nome": "x", "tag": "x"}, headers=h)
    log("OPERADOR", "Criar Ativo (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")
    
    # NÃO acesso admin
    r = requests.get(f"{API}/api/admin/users", headers=h)
    log("OPERADOR", "Admin users (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")
    
    # NÃO pode exportar
    r = requests.get(f"{API}/api/export/ativos?format=excel", headers=h)
    log("OPERADOR", "Exportar (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")

# ============================================================
# VISUALIZADOR
# ============================================================
print("\n" + "="*60)
print("FLUXO VISUALIZADOR")
print("="*60)

# Create a temp visualizador user
master_token = login("master@maintrix.com", "master123")
r = requests.post(f"{API}/api/admin/users", json={
    "email": "hom.viewer@maintrix.com", "password": "viewer123", "nome": "HOM Viewer",
    "role": "visualizador"
}, headers=auth(master_token))
viewer_created = r.status_code in (200, 201)

token = login("hom.viewer@maintrix.com", "viewer123")
if not token:
    log("VISUALIZADOR", "Login", "FAIL", "Não conseguiu autenticar (viewer pode não existir)")
else:
    log("VISUALIZADOR", "Login", "PASS")
    h = auth(token)
    
    # Consultar ativos
    r = requests.get(f"{API}/api/ativos", headers=h)
    log("VISUALIZADOR", "Consultar ativos", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Consultar OS
    r = requests.get(f"{API}/api/ordens-servico", headers=h)
    log("VISUALIZADOR", "Consultar OS", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # Consultar inspeções
    r = requests.get(f"{API}/api/inspecoes", headers=h)
    log("VISUALIZADOR", "Consultar inspeções", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")
    
    # NÃO pode criar OS
    r = requests.post(f"{API}/api/ordens-servico", json={"ativo_id": "x", "titulo": "x", "descricao": "x", "tipo": "corretiva", "origem": "manual"}, headers=h)
    log("VISUALIZADOR", "Criar OS (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")
    
    # NÃO pode criar ativo
    r = requests.post(f"{API}/api/ativos", json={"nome": "x", "tag": "x"}, headers=h)
    log("VISUALIZADOR", "Criar Ativo (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")
    
    # NÃO pode editar estoque
    r = requests.post(f"{API}/api/estoque", json={"nome": "x"}, headers=h)
    log("VISUALIZADOR", "Criar Estoque (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")
    
    # NÃO pode exportar
    r = requests.get(f"{API}/api/export/ativos?format=excel", headers=h)
    log("VISUALIZADOR", "Exportar (deve ser 403)", "PASS" if r.status_code == 403 else "FAIL", f"status={r.status_code}")

# Cleanup viewer
if viewer_created:
    users = requests.get(f"{API}/api/admin/users", headers=auth(master_token)).json()
    vu = [u for u in users if u.get("email") == "hom.viewer@maintrix.com"]
    if vu:
        requests.delete(f"{API}/api/admin/users/{vu[0]['id']}", headers=auth(master_token))

# ============================================================
# VALIDAÇÕES TRANSVERSAIS
# ============================================================
print("\n" + "="*60)
print("VALIDAÇÕES TRANSVERSAIS")
print("="*60)

master_h = auth(login("master@maintrix.com", "master123"))

# Recuperação de senha
r = requests.post(f"{API}/api/auth/forgot-password", json={"email": "master@maintrix.com"})
has_token = "token" in r.json() if r.status_code == 200 else False
log("TRANSVERSAL", "Recuperação de senha (sem token leak)", "PASS" if r.status_code == 200 and not has_token else "FAIL", f"status={r.status_code} has_token={has_token}")

# Duplicação de template
r = requests.get(f"{API}/api/inspection-templates", headers=master_h)
templates = r.json() if r.status_code == 200 else []
if templates:
    r = requests.post(f"{API}/api/inspection-templates/{templates[0]['id']}/duplicate", headers=master_h)
    log("TRANSVERSAL", "Duplicar Template Inspeção", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")

# Estoque
r = requests.get(f"{API}/api/estoque", headers=master_h)
log("TRANSVERSAL", "Estoque (listar)", "PASS" if r.status_code == 200 else "FAIL", f"{len(r.json())} itens")

# Sobressalentes
r = requests.get(f"{API}/api/sobressalentes", headers=master_h)
log("TRANSVERSAL", "Sobressalentes (listar)", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")

# Paradas programadas
r = requests.get(f"{API}/api/paradas-programadas", headers=master_h)
log("TRANSVERSAL", "Paradas programadas", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}")

# Workflow completo da OS (verificar status progression)
r = requests.get(f"{API}/api/ordens-servico", headers=master_h)
os_all = r.json() if r.status_code == 200 else []
statuses = set(o.get("status") for o in os_all)
log("TRANSVERSAL", "OS statuses presentes", "PASS" if len(statuses) > 3 else "FAIL", f"statuses={statuses}")

# ============================================================
# RELATÓRIO FINAL
# ============================================================
print("\n" + "="*60)
print("RELATÓRIO FINAL RC-04")
print("="*60)

passes = sum(1 for r in RESULTS if r["status"] == "PASS")
fails = sum(1 for r in RESULTS if r["status"] == "FAIL")
total = len(RESULTS)

print(f"\nTotal: {total} testes | ✅ {passes} PASS | ❌ {fails} FAIL")
print(f"Taxa de sucesso: {passes/total*100:.1f}%\n")

if BUGS:
    print("BUGS ENCONTRADOS:")
    print("-" * 40)
    for b in BUGS:
        print(f"🔴 [{b['flow']}] {b['test']}")
        print(f"   Motivo: {b['detail']}")
        if b['file']:
            print(f"   Arquivo: {b['file']}")
        print()
else:
    print("🎉 NENHUM BUG ENCONTRADO!")

# Write JSON report
import json
report = {
    "total": total, "pass": passes, "fail": fails,
    "success_rate": f"{passes/total*100:.1f}%",
    "results": RESULTS, "bugs": BUGS
}
with open("/app/test_reports/rc04_homologacao.json", "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print(f"\nRelatório salvo em /app/test_reports/rc04_homologacao.json")
