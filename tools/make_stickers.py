#!/usr/bin/env python3
"""활성 매장 전부의 QR 스티커를 A4 인쇄용 HTML로 생성 → stickers.html (브라우저에서 열어 인쇄, 1장당 매장 1곳)"""
import base64, io, qrcode, html
from common import rest, APP_URL
stores = rest("stores?is_active=eq.true&select=name,address,qr_secret&order=name")
cards = []
for s in stores:
    url = f"{APP_URL}/#/s/{s['qr_secret']}"
    img = qrcode.make(url, box_size=10, border=2); buf = io.BytesIO(); img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    cards.append(f"""<section class="page">
  <div class="brand">라밥</div>
  <div class="head">라이더 3,000원 할인 매장</div>
  <img src="data:image/png;base64,{b64}">
  <div class="store">{html.escape(s['name'])}</div>
  <div class="how">① 라밥 앱 열기 → ② 이 QR 찍기 → ③ 할인 화면을 사장님께 보여주기</div>
  <div class="time">할인 시간 14:00~17:00 · 20:00~24:00 · 하루 1회</div>
</section>""")
open("stickers.html", "w").write(f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>라밥 QR 스티커</title><style>
@page{{size:A4;margin:0}} body{{margin:0;font-family:-apple-system,"Apple SD Gothic Neo",sans-serif}}
.page{{width:210mm;height:297mm;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;page-break-after:always;padding:20mm;box-sizing:border-box}}
.brand{{font-size:28pt;font-weight:900;color:#FF6B35}} .head{{font-size:22pt;font-weight:800;margin:6mm 0 10mm}}
img{{width:110mm;height:110mm}} .store{{font-size:20pt;font-weight:700;margin:10mm 0 6mm}}
.how{{font-size:13pt;color:#333;margin-bottom:4mm}} .time{{font-size:12pt;color:#666}}
</style></head><body>{''.join(cards)}</body></html>""")
print(f"stickers.html 생성: {len(stores)}곳 (APP_URL={APP_URL})")
