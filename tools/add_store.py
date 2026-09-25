#!/usr/bin/env python3
"""매장 등록. 예:
python3 add_store.py "신림 제육집" "서울 관악구 신림로 123" --menu "제육볶음 9,000원" --hours 11:00-15:00 17:00-21:00 --phone 02-000-0000 --closed 0
--hours 는 여러 구간 가능(브레이크타임은 구간 2개로). --closed 는 휴무 요일(0=일 … 6=토), 여러 개 가능.
"""
import argparse, sys
from common import rest
p = argparse.ArgumentParser(); p.add_argument("name"); p.add_argument("address")
p.add_argument("--menu", default=""); p.add_argument("--phone", default=None); p.add_argument("--naver", default=None)
p.add_argument("--hours", nargs="+", required=True); p.add_argument("--closed", nargs="*", type=int, default=[])
p.add_argument("--discount", type=int, default=3000)
a = p.parse_args()
s = rest("stores", "POST", {"name": a.name, "address": a.address, "menu_note": a.menu, "phone": a.phone, "naver_url": a.naver, "discount_krw": a.discount}, prefer="return=representation")[0]
days = [d for d in range(7) if d not in a.closed]
for h in a.hours:
    o, c = h.split("-"); rest("rpc/set_hours", "POST", {"p_store": s["id"], "p_open": o, "p_close": c, "p_days": days})
print(f"등록 완료: {s['name']}  id={s['id']}  qr_secret={s['qr_secret']}")
