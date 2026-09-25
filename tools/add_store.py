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
p.add_argument("--latlng", default=None, help="위도,경도 (예: 37.4845,126.9296). 없으면 주소로 자동 지오코딩 시도")
a = p.parse_args()
lat = lng = None
if a.latlng:
    lat, lng = map(float, a.latlng.split(","))
else:
    import urllib.parse, urllib.request, json
    try:
        q = urllib.parse.urlencode({"q": a.address, "format": "json", "limit": 1, "countrycodes": "kr"})
        req = urllib.request.Request(f"https://nominatim.openstreetmap.org/search?{q}", headers={"User-Agent": "rabap-admin/1.0"})
        r = json.load(urllib.request.urlopen(req, timeout=10))
        if r: lat, lng = float(r[0]["lat"]), float(r[0]["lon"]); print(f"지오코딩: {lat},{lng} ({r[0]['display_name'][:60]})")
        else: print("⚠ 지오코딩 실패 — --latlng 로 직접 넣으세요 (네이버지도에서 우클릭→좌표)")
    except Exception as e: print("⚠ 지오코딩 오류:", e)
s = rest("stores", "POST", {"name": a.name, "address": a.address, "menu_note": a.menu, "phone": a.phone, "naver_url": a.naver, "discount_krw": a.discount, "lat": lat, "lng": lng}, prefer="return=representation")[0]
days = [d for d in range(7) if d not in a.closed]
for h in a.hours:
    o, c = h.split("-"); rest("rpc/set_hours", "POST", {"p_store": s["id"], "p_open": o, "p_close": c, "p_days": days})
print(f"등록 완료: {s['name']}  id={s['id']}  qr_secret={s['qr_secret']}")
