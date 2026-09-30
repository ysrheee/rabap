#!/usr/bin/env python3
"""두잇 ClickHouse(Redash DS 27) 쿼리. 사용: python3 doeat_query.py "SQL"  (REDASH_API_KEY는 ~/claude-note/.env)"""
import sys, json, urllib.request, time, os
key=None
for line in open(os.path.expanduser("~/claude-note/.env")):
    if line.startswith("REDASH_API_KEY="): key=line.strip().split("=",1)[1]
q=sys.argv[1]
def call(path, body=None):
    req=urllib.request.Request("http://54.180.0.38"+path, data=json.dumps(body).encode() if body else None, headers={"Authorization":"Key "+key,"Content-Type":"application/json"}, method="POST" if body else "GET")
    return json.load(urllib.request.urlopen(req))
r=call("/api/query_results", {"query": q, "data_source_id": 27, "max_age": 0}); job=r.get("job")
for _ in range(60):
    if not job: break
    j=call(f"/api/jobs/{job['id']}")["job"]
    if j["status"]==4: print("ERR", (j.get("error") or "")[:800]); sys.exit(1)
    if j["status"]==3: r=call(f"/api/query_results/{j['query_result_id']}"); break
    time.sleep(1)
print(json.dumps(r["query_result"]["data"]["rows"], ensure_ascii=False))
