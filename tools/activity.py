#!/usr/bin/env python3
"""라이더별 활동: 가입일 · 마지막 접속 · 접속 횟수(오늘/누적) · 할인 사용 횟수. KST 표시"""
import datetime as dt, re
from common import rest
KST=dt.timezone(dt.timedelta(hours=9))
def fix_iso(ts):
    ts=ts.replace("Z","+00:00")
    m=re.match(r"(.*\.\d+)([+-]\d\d:\d\d)$", ts)
    if m:  # 마이크로초 6자리로 맞춤
        head,tz=m.groups(); base,frac=head.split("."); ts=f"{base}.{frac[:6].ljust(6,'0')}{tz}"
    return ts
def k(ts): return dt.datetime.fromisoformat(fix_iso(ts)).astimezone(KST)
users=rest("users?select=id,phone,created_at&order=created_at")
ev=rest("events?event=eq.app_open&select=user_id,created_at&order=created_at")
rd=rest("redemptions?select=user_id,redeemed_at,stores(name)&order=redeemed_at")
today=dt.datetime.now(KST).date()
opens={}; 
for e in ev: opens.setdefault(e["user_id"],[]).append(k(e["created_at"]))
uses={}
for r in rd: uses.setdefault(r["user_id"],[]).append((k(r["redeemed_at"]), (r.get("stores") or {}).get("name")))
print(f"{'번호':13} {'가입':11} {'마지막 접속':14} {'오늘':>4} {'누적':>4} {'사용':>4}  최근 사용")
for u in users:
    o=opens.get(u["id"],[]); us=uses.get(u["id"],[])
    last=o[-1].strftime("%m/%d %H:%M") if o else "-"
    print(f"{u['phone'][:3]}-{u['phone'][3:7]}-{u['phone'][7:]}  {k(u['created_at']).strftime('%m/%d %H:%M')}  {last:14} {sum(1 for x in o if x.date()==today):>4} {len(o):>4} {len(us):>4}  {us[-1][0].strftime('%m/%d %H:%M')+' '+str(us[-1][1]) if us else ''}")
