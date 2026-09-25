#!/usr/bin/env python3
"""어제 사용 집계. 슬랙 웹훅(SLACK_WEBHOOK_RABAP in .env)이 있으면 전송, 없으면 출력만."""
import json, urllib.request, datetime as dt
from common import rest, ENV
y = (dt.datetime.utcnow() + dt.timedelta(hours=9) - dt.timedelta(days=1)).date().isoformat()
rows = rest(f"redemptions?redeemed_date=eq.{y}&select=discount_krw,stores(name)")
users = rest("users?select=id", prefer="count=exact") or []
by = {}
for r in rows: by[r["stores"]["name"]] = by.get(r["stores"]["name"], 0) + 1
lines = [f"*라밥 일일 리포트 {y}*", f"- 할인 사용 {len(rows)}건 / 누적 가입 {len(users)}명"] + [f"- {k}: {v}건" for k, v in sorted(by.items(), key=lambda x: -x[1])]
msg = "\n".join(lines); print(msg)
if ENV.get("SLACK_WEBHOOK_RABAP"):
    urllib.request.urlopen(urllib.request.Request(ENV["SLACK_WEBHOOK_RABAP"], data=json.dumps({"text": msg}).encode(), headers={"Content-Type": "application/json"}))
