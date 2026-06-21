"""Iteration 39 - Bloco 2: Field-level audit logging
Tests that PUT /api/* generates audit_logs with action='field_change' and a structured
'changes' array containing campo, valor_anterior, valor_novo."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
ADMIN = {"email": "admin@manutrix.com", "password": "admin123"}
PCM = {"email": "pcm@manutrix.com", "password": "pcm123"}


def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    return data.get('access_token') or data.get('token'), data.get('user') or {}


@pytest.fixture(scope="module")
def admin_session():
    token, user = _login(ADMIN)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    s.user = user
    return s


@pytest.fixture(scope="module")
def pcm_session():
    token, user = _login(PCM)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    s.user = user
    return s


def _fetch_recent_field_change_logs(session, entity_type=None, entity_id=None, limit=50):
    """Fetch recent field_change logs filtered optionally by entity."""
    r = session.get(f"{BASE_URL}/api/admin/audit-logs?action=field_change&limit={limit}", timeout=30)
    assert r.status_code == 200, f"audit-logs GET failed: {r.status_code} {r.text}"
    logs = r.json()
    if entity_type:
        logs = [l for l in logs if l.get('entity_type') == entity_type]
    if entity_id:
        logs = [l for l in logs if l.get('entity_id') == entity_id]
    return logs


def _find_log_with_field(logs, campo_label):
    for log in logs:
        for ch in (log.get('changes') or []):
            if ch.get('campo') == campo_label:
                return log, ch
    return None, None


# ------------------ OS prioridade ------------------
def test_os_prioridade_change_creates_field_change_log(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/ordens-servico?limit=20", timeout=30)
    assert r.status_code == 200, r.text
    oss = [o for o in r.json() if o.get('status') not in ('concluida', 'cancelada')]
    assert oss, "No editable OS available"
    os_doc = oss[0]
    os_id = os_doc['id']
    old_prio = os_doc.get('prioridade') or 'media'
    new_prio = 'alta' if old_prio != 'alta' else 'media'

    upd = admin_session.put(f"{BASE_URL}/api/ordens-servico/{os_id}", json={"prioridade": new_prio}, timeout=30)
    assert upd.status_code == 200, f"PUT OS failed: {upd.status_code} {upd.text}"
    time.sleep(1)

    logs = _fetch_recent_field_change_logs(admin_session, entity_id=os_id)
    assert logs, f"No field_change log for OS {os_id}"
    log, ch = _find_log_with_field(logs, 'Prioridade')
    assert ch is not None, f"No 'Prioridade' change in changes: {[l.get('changes') for l in logs]}"
    assert str(ch['valor_anterior']) == str(old_prio)
    assert str(ch['valor_novo']) == str(new_prio)
    assert log['action'] == 'field_change'
    assert log['entity_type'] == 'ordens_servico' or 'os' in log['entity_type'].lower() or log['entity_type'] == 'ordens_servico'
    assert log.get('user_nome')
    assert log.get('user_role') == 'admin'
    assert log.get('details') and 'Prioridade' in log['details']


# ------------------ Ativo fabricante ------------------
def test_ativo_fabricante_change_creates_field_change_log(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/ativos?limit=20", timeout=30)
    assert r.status_code == 200, r.text
    ativos = r.json()
    assert ativos, "No ativos"
    a = ativos[0]
    old_fab = a.get('fabricante') or ''
    new_fab = f"FAB-TEST-{int(time.time())}"

    upd = admin_session.put(f"{BASE_URL}/api/ativos/{a['id']}", json={"fabricante": new_fab}, timeout=30)
    assert upd.status_code == 200, f"PUT Ativo failed: {upd.status_code} {upd.text}"
    time.sleep(1)

    logs = _fetch_recent_field_change_logs(admin_session, entity_id=a['id'])
    log, ch = _find_log_with_field(logs, 'Fabricante')
    assert ch is not None, f"No 'Fabricante' field_change for ativo {a['id']}; logs={logs[:2]}"
    assert str(ch['valor_anterior']) == str(old_fab) or ch['valor_anterior'] in (old_fab, None, '')
    assert ch['valor_novo'] == new_fab
    assert log['action'] == 'field_change'
    assert log.get('user_role') == 'admin'


# ------------------ Estoque quantidade ------------------
def test_estoque_quantidade_change_creates_field_change_log(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/estoque?limit=20", timeout=30)
    assert r.status_code == 200, r.text
    items = r.json()
    assert items, "No estoque items"
    item = items[0]
    item_id = item['id']
    old_q = item.get('quantidade', 0)
    new_q = (old_q or 0) + 7

    upd = admin_session.put(f"{BASE_URL}/api/estoque/{item_id}", json={"quantidade": new_q}, timeout=30)
    assert upd.status_code == 200, f"PUT Estoque failed: {upd.status_code} {upd.text}"
    time.sleep(1)

    logs = _fetch_recent_field_change_logs(admin_session, entity_id=item_id)
    log, ch = _find_log_with_field(logs, 'Quantidade')
    assert ch is not None, f"No 'Quantidade' change for estoque {item_id}; logs={logs[:2]}"
    assert str(ch['valor_anterior']) == str(old_q)
    assert str(ch['valor_novo']) == str(new_q)
    assert log['action'] == 'field_change'


# ------------------ Sobressalente descricao ------------------
def test_sobressalente_descricao_change_creates_field_change_log(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/sobressalentes?limit=20", timeout=30)
    assert r.status_code == 200, r.text
    sps = r.json()
    if not sps:
        pytest.skip("No sobressalentes available")
    sp = sps[0]
    old_desc = sp.get('descricao') or ''
    new_desc = f"DESC-TEST-{int(time.time())}"

    upd = admin_session.put(f"{BASE_URL}/api/sobressalentes/{sp['id']}", json={"descricao": new_desc}, timeout=30)
    assert upd.status_code == 200, f"PUT Sobressalente failed: {upd.status_code} {upd.text}"
    time.sleep(1)

    logs = _fetch_recent_field_change_logs(admin_session, entity_id=sp['id'])
    log, ch = _find_log_with_field(logs, 'Descrição')
    assert ch is not None, f"No 'Descrição' change for sobressalente {sp['id']}; logs={logs[:2]}"
    assert ch['valor_novo'] == new_desc
    assert log['action'] == 'field_change'


# ------------------ GET audit-logs returns changes array ------------------
def test_get_audit_logs_filter_action_field_change_returns_changes(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/admin/audit-logs?action=field_change&limit=20", timeout=30)
    assert r.status_code == 200
    logs = r.json()
    assert isinstance(logs, list)
    assert logs, "Expected at least one field_change log from prior tests"
    sample = logs[0]
    for k in ('id', 'action', 'entity_type', 'entity_id', 'user_nome', 'user_role', 'details', 'changes', 'created_at'):
        assert k in sample, f"Missing key '{k}' in audit log response: {sample.keys()}"
    assert sample['action'] == 'field_change'
    assert isinstance(sample['changes'], list)
    assert sample['changes'], "changes array must not be empty for field_change action"
    ch = sample['changes'][0]
    assert 'campo' in ch and 'valor_anterior' in ch and 'valor_novo' in ch
    assert 'campo_raw' in ch


# ------------------ No-op change does NOT create a log ------------------
def test_noop_change_does_not_create_field_change_log(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/ativos?limit=5", timeout=30)
    ativos = r.json()
    assert ativos
    a = ativos[0]
    current_fab = a.get('fabricante') or ''

    # Count logs for this entity before
    before = len(_fetch_recent_field_change_logs(admin_session, entity_id=a['id'], limit=200))

    # PUT same value
    upd = admin_session.put(f"{BASE_URL}/api/ativos/{a['id']}", json={"fabricante": current_fab}, timeout=30)
    assert upd.status_code == 200, upd.text
    time.sleep(1)

    after = len(_fetch_recent_field_change_logs(admin_session, entity_id=a['id'], limit=200))
    assert after == before, f"No-op PUT created a new field_change log (before={before}, after={after})"


# ------------------ updated_at / alterado_por NOT reported ------------------
def test_updated_at_and_alterado_por_not_in_changes(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/admin/audit-logs?action=field_change&limit=50", timeout=30)
    logs = r.json()
    assert logs
    forbidden = {'updated_at', 'alterado_por', 'deleted_at', '_id', 'organization_id'}
    for log in logs:
        for ch in (log.get('changes') or []):
            assert ch.get('campo_raw') not in forbidden, f"Forbidden field '{ch.get('campo_raw')}' in changes of log {log.get('id')}"
            assert ch.get('campo') not in {'updated_at', 'alterado_por'}, f"Raw timestamp label leaked: {ch}"


# ------------------ Multiple field changes in single PUT -> one log, multiple changes ------------------
def test_multiple_field_changes_single_put(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/ativos?limit=5", timeout=30)
    ativos = r.json()
    assert ativos
    a = ativos[0]
    new_fab = f"MFAB-{int(time.time())}"
    new_modelo = f"MMOD-{int(time.time())}"

    upd = admin_session.put(
        f"{BASE_URL}/api/ativos/{a['id']}",
        json={"fabricante": new_fab, "modelo": new_modelo},
        timeout=30,
    )
    assert upd.status_code == 200, upd.text
    time.sleep(1)

    logs = _fetch_recent_field_change_logs(admin_session, entity_id=a['id'], limit=20)
    # Find the most recent log that has BOTH fabricante and modelo
    found = None
    for log in logs:
        labels = {c.get('campo') for c in (log.get('changes') or [])}
        if {'Fabricante', 'Modelo'}.issubset(labels):
            found = log
            break
    assert found is not None, f"Expected single audit log with both Fabricante and Modelo; logs={[l.get('changes') for l in logs[:3]]}"
    assert len(found['changes']) >= 2


# ------------------ Log schema completeness ------------------
def test_field_change_log_has_required_attributes(admin_session):
    logs = _fetch_recent_field_change_logs(admin_session, limit=30)
    assert logs
    log = logs[0]
    assert log.get('user_nome'), "user_nome empty"
    assert log.get('user_role') in ('admin', 'pcm', 'supervisor', 'tecnico', 'gerente')
    assert log.get('entity_type')
    assert log.get('entity_id')
    assert log.get('details') and isinstance(log['details'], str) and len(log['details']) > 0
    assert isinstance(log.get('changes'), list) and len(log['changes']) >= 1


# ------------------ PCM attribution ------------------
def test_pcm_field_change_attributed_to_pcm(pcm_session, admin_session):
    # Use estoque which PCM can edit
    r = pcm_session.get(f"{BASE_URL}/api/estoque?limit=5", timeout=30)
    assert r.status_code == 200, r.text
    items = r.json()
    if not items:
        pytest.skip("No estoque for PCM")
    item = items[0]
    old_q = item.get('quantidade', 0)
    new_q = (old_q or 0) + 3

    upd = pcm_session.put(f"{BASE_URL}/api/estoque/{item['id']}", json={"quantidade": new_q}, timeout=30)
    assert upd.status_code == 200, f"PCM PUT estoque failed: {upd.status_code} {upd.text}"
    time.sleep(1)

    # Admin reads audit logs (PCM may also read)
    logs = _fetch_recent_field_change_logs(admin_session, entity_id=item['id'], limit=30)
    # Find log made by pcm
    pcm_logs = [l for l in logs if l.get('user_role') == 'pcm']
    assert pcm_logs, f"No PCM-authored field_change log; logs roles={[l.get('user_role') for l in logs[:5]]}"
    log = pcm_logs[0]
    # user_nome should contain pcm identity
    assert log.get('user_nome'), "user_nome empty for PCM log"
    assert 'pcm' in (log['user_nome'].lower() + (pcm_session.user.get('email') or '').lower()) or log['user_nome'] == pcm_session.user.get('nome')
    labels = {c.get('campo') for c in (log.get('changes') or [])}
    assert 'Quantidade' in labels
