#!/usr/bin/env python3
"""초대 코드별 링크 열림(고유 방문자) vs 가입 수"""
from common import rest
ev=rest("events?event=eq.invite_open&select=code,visitor,created_at")
inv=rest("invites?select=code,issuer_id,used_count,users!invites_issuer_id_fkey(phone)")
opens={}
for e in ev: opens.setdefault(e["code"],set()).add(e["visitor"])
print(f"{'코드':10} {'발급자':14} {'링크 열림(고유)':>14} {'가입':>5}")
for i in sorted(inv, key=lambda x:-x["used_count"]):
    if i["used_count"]==0 and i["code"] not in opens: continue
    who=(i.get("users") or {}).get("phone","시드") if i.get("users") else "시드"
    print(f"{i['code']:10} {who:14} {len(opens.get(i['code'],())):>14} {i['used_count']:>5}")
