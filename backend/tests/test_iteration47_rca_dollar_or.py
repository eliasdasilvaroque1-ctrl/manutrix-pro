"""
RCA test: server.py lines 1180-1182 have two `$or` keys in the same dict literal —
the second `$or` (status) overwrites the first (`categoria`/`tipo` matcher).

Impact: if an ativo has multiple plans (e.g. inspecao + lubrificacao),
POST /inspecoes for tipo=inspecao may match the lubrificacao plan, because the
tipo/categoria $or is dropped from the Mongo query and only status is filtered.

Reproduction:
1. Create plan tipo=lubrificacao for ativo A (created FIRST, has lower versao)
2. Create plan tipo=inspecao for ativo A (created SECOND)
3. POST /inspecoes ativo_id=A tipo=lubrificacao
4. Because sort=[("versao",-1),("created_at",-1)] picks the most-recent one,
   the resulting checklist may match the INSPECAO plan instead of LUBRIFICACAO.
"""
import os, uuid, requests, pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

@pytest.fixture(scope="module")
def auth():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{API}/auth/login", json={"email": "admin@manutrix.com", "password": "admin123"})
    tok = r.json().get("token") or r.json().get("access_token")
    s.headers.update({"Authorization": f"Bearer {tok}"})
    return s

@pytest.fixture(scope="module")
def ativo_id(auth):
    r = auth.get(f"{API}/ativos")
    return r.json()[0]["id"]

def test_two_plans_tipo_filter_works(auth, ativo_id):
    """Both plans exist for ativo: inspecao with 7 questions, lubrificacao with 2 questions.
    Creating inspecao tipo should return a checklist with the INSPECAO plan's questions, not lubrificacao."""
    # plan A: lubrificacao (2 perguntas)
    p_lub = auth.post(f"{API}/planos-inspecao", json={
        "nome": f"TEST_RCA_LUB_{uuid.uuid4().hex[:6]}",
        "tipo": "lubrificacao",
        "ativo_id": ativo_id,
        "status": "ativo",
        "versao": 1,
        "perguntas": [
            {"texto": "LUB-Q1", "tipo_campo": "texto", "ordem": 1},
            {"texto": "LUB-Q2", "tipo_campo": "numero", "ordem": 2},
        ],
    }).json()
    # plan B: inspecao (7 perguntas, higher versao so it wins any sort)
    p_insp = auth.post(f"{API}/planos-inspecao", json={
        "nome": f"TEST_RCA_INSP_{uuid.uuid4().hex[:6]}",
        "tipo": "inspecao",
        "ativo_id": ativo_id,
        "status": "ativo",
        "versao": 99,
        "perguntas": [
            {"texto": f"INSP-Q{i}", "tipo_campo": "boolean", "ordem": i} for i in range(1, 8)
        ],
    }).json()
    try:
        # Create inspection tipo=lubrificacao — should resolve to LUB plan (2 questions)
        r = auth.post(f"{API}/inspecoes", json={"ativo_id": ativo_id, "tipo": "lubrificacao"})
        assert r.status_code == 200, r.text
        insp = r.json()
        # if $or bug exists, this will pick the INSPECAO plan (7 questions) due to higher versao
        assert insp["plano_id"] == p_lub["id"], (
            f"BUG: expected lubrificacao plan ({p_lub['id']} / 2 questions), "
            f"got {insp.get('plano_nome')} ({insp.get('plano_id')}) "
            f"with {len(insp['checklist'])} checklist items. "
            f"Likely caused by duplicate $or keys at server.py:1180-1182."
        )
        assert len(insp["checklist"]) == 2, f"expected 2 items, got {len(insp['checklist'])}"
    finally:
        auth.delete(f"{API}/planos-inspecao/{p_lub['id']}")
        auth.delete(f"{API}/planos-inspecao/{p_insp['id']}")
