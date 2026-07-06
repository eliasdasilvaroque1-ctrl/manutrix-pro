"""Helper script to create the RC07 viewer test user for GUI testing.

Run: python create_viewer.py
Prints the viewer ID at the end (save it to delete later).
"""
import os
import sys
import requests

BASE_URL = "https://procure-manutrix.preview.emergentagent.com"
API = f"{BASE_URL}/api"

s = requests.Session()
orgs = s.get(f"{API}/public/organizations").json()
astec = next(o for o in orgs if "ASTEC" in (o.get("nome") or "").upper())
org_id = astec["id"]

r = s.post(f"{API}/auth/login", json={
    "email": "master@maintrix.com",
    "password": "master123",
    "organization_id": org_id,
})
r.raise_for_status()
master_token = r.json()["access_token"]
h = {"Authorization": f"Bearer {master_token}"}

# Clean any leftover
r = s.get(f"{API}/admin/users", headers=h)
for u in r.json():
    if u.get("email") == "rc07test@maintrix.com":
        s.delete(f"{API}/admin/users/{u['id']}", headers=h)

# Create viewer
r = s.post(f"{API}/admin/users", headers=h, json={
    "email": "rc07test@maintrix.com",
    "password": "v123",
    "nome": "RC07 Test Viewer",
    "role": "visualizador",
})
r.raise_for_status()
uid = r.json()["id"]

# Flip force_password_change
r = s.put(f"{API}/admin/users/{uid}", headers=h, json={"force_password_change": False})
r.raise_for_status()

print(f"VIEWER_ID={uid}")
print(f"ORG_ID={org_id}")
print("Done. Login: rc07test@maintrix.com / v123 (org=ASTEC)")
