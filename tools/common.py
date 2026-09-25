import os, json, urllib.request
ENV = {}
with open(os.path.join(os.path.dirname(__file__), "..", ".env")) as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); ENV[k] = v
URL = ENV["SUPABASE_URL"]; KEY = ENV["SUPABASE_SERVICE_ROLE_KEY"]
APP_URL = ENV.get("APP_URL", "https://rabap.kr")

def rest(path, method="GET", body=None, prefer=None):
    req = urllib.request.Request(f"{URL}/rest/v1/{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", **({"Prefer": prefer} if prefer else {})})
    with urllib.request.urlopen(req) as r:
        t = r.read().decode(); return json.loads(t) if t else None
