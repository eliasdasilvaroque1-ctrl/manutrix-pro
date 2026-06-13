# MANUTRIX OMNI — Production Backup & Rollback Instructions

## Backup Info
- **Date**: 2026-06-13
- **Location**: `/app/backups/production_20260613/`
- **Total Documents**: 341
- **Collections**: 20

## Backup Contents

| Collection | Count | File |
|------------|-------|------|
| users | 9 | users.json |
| sectors | 9 | sectors.json |
| ativos | 36 | ativos.json |
| itens_estoque | 29 | itens_estoque.json |
| ordens_servico | 49 | ordens_servico.json |
| inspecoes | 49 | inspecoes.json |
| anomalias | 6 | anomalias.json |
| spare_assets | 9 | spare_assets.json |
| spare_movements | 1 | spare_movements.json |
| attachments | 7 | attachments.json |
| audit_logs | 40 | audit_logs.json |
| notificacoes | 60 | notificacoes.json |
| rotas_inspecao | 4 | rotas_inspecao.json |
| movimentacoes_estoque | 21 | movimentacoes_estoque.json |
| knowledge_base | 3 | knowledge_base.json |
| areas | 4 | areas.json (legacy) |
| plantas | 1 | plantas.json (legacy) |
| plants | 4 | plants.json (legacy) |

## Rollback Instructions

### Option 1: Use Emergent Platform Rollback (Recommended)
1. Go to the Emergent chat interface
2. Click "Rollback" button
3. Select the checkpoint BEFORE the deployment
4. Free of charge, instant restore

### Option 2: Manual Database Restore
If only the database needs to be restored (code is fine):

```bash
cd /app/backend
python3 << 'RESTORE'
import os, json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('.env')
client = MongoClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]

backup_dir = "/app/backups/production_20260613"
collections = [
    'users', 'sectors', 'ativos', 'itens_estoque', 'ordens_servico',
    'inspecoes', 'anomalias', 'spare_assets', 'spare_movements',
    'attachments', 'audit_logs', 'notificacoes', 'rotas_inspecao',
    'movimentacoes_estoque', 'knowledge_base'
]

for coll_name in collections:
    filepath = f"{backup_dir}/{coll_name}.json"
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r') as f:
        docs = json.load(f)
    if not docs:
        continue
    # Drop and restore
    db[coll_name].drop()
    db[coll_name].insert_many(docs)
    print(f"Restored {coll_name}: {len(docs)} docs")

print("Rollback complete")
RESTORE
```

### Option 3: Restore Single Collection
```bash
cd /app/backend && python3 -c "
import os, json
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv('.env')
client = MongoClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
COLLECTION = 'ordens_servico'  # Change this
with open(f'/app/backups/production_20260613/{COLLECTION}.json') as f:
    docs = json.load(f)
db[COLLECTION].drop()
db[COLLECTION].insert_many(docs)
print(f'Restored {COLLECTION}: {len(docs)} docs')
"
```

## Post-Rollback Checklist
1. Restart backend: `sudo supervisorctl restart backend`
2. Verify API: `curl {URL}/api/`
3. Login test: admin@manutrix.com / admin123
4. Check dashboard loads
5. Verify sectors, ativos, OS counts match backup

## Emergency Contact
- Use Emergent Platform "Rollback" feature for instant code + DB restore
- All backups are JSON format, human-readable, and can be imported into any MongoDB instance
