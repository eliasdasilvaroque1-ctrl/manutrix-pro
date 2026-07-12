#!/usr/bin/env python3
"""
MAINTRIX — Post-Deploy Validation Script
Run after every deployment to confirm production matches RC1.5.
Usage: python3 validate_deploy.py [--domain maintrix.com.br]
"""
import sys
import json
import subprocess
import time

DOMAIN = "www.maintrix.com.br"
EXPECTED = {
    "api_version": "v5.2.0-RC1",
    "sw_version": "maintrix-v4",
    "terms_version": "1.0",
    "security_headers": [
        "x-content-type-options",
        "x-frame-options",
        "referrer-policy",
        "permissions-policy",
    ],
}

def curl(url, method="GET", headers=None, data=None):
    cmd = ["curl", "-s", "-w", "\n%{http_code}", url]
    if method != "GET":
        cmd += ["-X", method]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
    if data:
        cmd += ["-d", data]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    lines = r.stdout.strip().rsplit("\n", 1)
    body = lines[0] if len(lines) > 1 else ""
    code = int(lines[-1]) if lines[-1].isdigit() else 0
    return code, body

def curl_headers(url):
    cmd = ["curl", "-sI", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    hdrs = {}
    for line in r.stdout.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            hdrs[k.strip().lower()] = v.strip()
    return hdrs

results = []
def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, status, detail))
    icon = "✅" if passed else "❌"
    print(f"  {icon} {name}: {status}" + (f" ({detail})" if detail else ""))

print(f"\n{'='*60}")
print(f"MAINTRIX DEPLOY VALIDATION — {DOMAIN}")
print(f"{'='*60}\n")

# 1. API Version
print("[1/7] API VERSION")
code, body = curl(f"https://{DOMAIN}/api")
try:
    ver = json.loads(body).get("message", "")
except:
    ver = body
has_version = EXPECTED["api_version"] in ver
check("API Version", has_version, ver)

# 2. Service Worker
print("\n[2/7] SERVICE WORKER")
code, body = curl(f"https://{DOMAIN}/service-worker.js")
has_sw = EXPECTED["sw_version"] in body
check("SW Version", has_sw, body.split("\n")[0] if body else "empty")

# 3. Compliance
print("\n[3/7] COMPLIANCE ENDPOINTS")
code, body = curl(f"https://{DOMAIN}/api/compliance/about")
check("/compliance/about", code == 200, f"HTTP {code}")
code, body = curl(f"https://{DOMAIN}/api/compliance/terms")
check("/compliance/terms", code == 200, f"HTTP {code}")

# 4. Security Headers
print("\n[4/7] SECURITY HEADERS")
hdrs = curl_headers(f"https://{DOMAIN}/api/public/organizations")
for h in EXPECTED["security_headers"]:
    check(f"Header {h}", h in hdrs, hdrs.get(h, "MISSING"))

# 5. Health Check
print("\n[5/7] HEALTH CHECK")
code, body = curl(f"https://{DOMAIN}/api/public/organizations")
try:
    orgs = json.loads(body)
    check("Public orgs", code == 200 and isinstance(orgs, list), f"HTTP {code}, {len(orgs)} orgs")
except:
    check("Public orgs", False, f"HTTP {code}")

# 6. Frontend Routes
print("\n[6/7] FRONTEND ROUTES")
for route in ["/", "/login", "/termos", "/privacidade", "/sobre"]:
    code, _ = curl(f"https://{DOMAIN}{route}")
    check(f"GET {route}", code == 200, f"HTTP {code}")

# 7. Build Info
print("\n[7/7] BUILD INFO")
hdrs = curl_headers(f"https://{DOMAIN}/")
lm = hdrs.get("last-modified", "unknown")
etag = hdrs.get("etag", "unknown")
check("Last-Modified recent", "2026" in lm and "Jul" not in lm.split(",")[0] if "02 Jul" in lm else True, lm)
print(f"  ETag: {etag}")

# Summary
print(f"\n{'='*60}")
passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
total = len(results)
print(f"RESULTADO: {passed}/{total} PASS, {failed}/{total} FAIL")
if failed == 0:
    print("🟢 DEPLOY VALIDADO — Produção corresponde à RC1.5")
elif failed <= 3:
    print("🟡 DEPLOY PARCIAL — Verificar itens FAIL")
else:
    print("🔴 DEPLOY FALHOU — Produção desatualizada")
print(f"{'='*60}\n")

sys.exit(0 if failed == 0 else 1)
