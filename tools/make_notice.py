#!/usr/bin/env python3
"""매장 비치용 A4 안내문 생성 → notice.html (매장별 1장, 브라우저에서 인쇄)"""
import html, base64, io, re, qrcode
from common import rest, APP_URL
stores = rest("stores?is_active=eq.true&select=id,name,min_order_krw&order=name")
# 매장별 초대 코드 발급(없으면 생성): S + 매장 id 앞 6자리 대문자, 500명 한도
codes = {}
for s in stores:
    code = "S" + s["id"].replace("-", "")[:6].upper()
    if not rest(f"invites?code=eq.{code}&select=code"):
        rest("invites", "POST", {"code": code, "issuer_id": None, "max_uses": 500})
    codes[s["id"]] = code
def qr_b64(url):
    img = qrcode.make(url, box_size=8, border=2); buf = io.BytesIO(); img.save(buf, format="PNG"); return base64.b64encode(buf.getvalue()).decode()
card = '''<div class="card"><div class="b">라밥 멤버십</div><div class="w">010-****-1234</div><div class="c">14:32:07</div><div class="d">2026.09.28 (월)</div><div class="p">● 지금 3,000원 할인 가능</div></div>'''
pages = []
for s in stores:
    pages.append(f'''<section class="page">
  <div class="brand">라밥</div>
  <h1>라이더 3,000원 할인 매장</h1>
  <p class="sub">{html.escape(s["name"])}</p>
  <div class="row">
    <div class="col">{card}<div class="cap">라이더 폰에 이 카드가 떠 있으면 할인해 주세요</div></div>
    <div class="col how">
      <div class="h">확인 방법</div>
      <ol>
        <li><b>시계가 움직이는지</b> 봐주세요. 캡처 화면은 시계가 멈춰 있어요.</li>
        <li>배지가 <b>"지금 3,000원 할인 가능"</b>(주황색)인지 봐주세요. 회색이면 할인 시간이 아니에요.</li>
        <li>주문 금액이 <b>{s["min_order_krw"]:,}원 이상</b>이면 <b>3,000원을 빼주세요.</b> 1인 1일 1회예요.</li>
      </ol>
    </div>
  </div>
  <div class="time">할인 시간 &nbsp;14:00 ~ 17:00 &nbsp;·&nbsp; {s["min_order_krw"]:,}원 이상 주문 시</div>
  <div class="join"><img src="data:image/png;base64,{qr_b64(APP_URL + "/#/join?code=" + codes[s["id"]])}"><div><div class="jh">라이더님, 아직 라밥 회원이 아니세요?</div><div class="jt">이 QR을 찍으면 바로 가입돼요 · 첫 주 무료 · 초대 코드 <b>{codes[s["id"]]}</b></div></div></div>
  <div class="foot">라밥은 관악구 라이더 전용 식사 멤버십이에요 · 문의 open.kakao.com/o/ssiAtQPi</div>
</section>''')
open("notice.html", "w").write(f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>라밥 매장 안내문</title><style>
@page{{size:A4;margin:0}} body{{margin:0;font-family:-apple-system,"Apple SD Gothic Neo",sans-serif;color:#191F28}}
.page{{width:210mm;height:297mm;padding:22mm 18mm;box-sizing:border-box;page-break-after:always;display:flex;flex-direction:column}}
.brand{{font-size:20pt;font-weight:900;color:#FF6B35}} h1{{font-size:30pt;margin:4mm 0 2mm;letter-spacing:-.02em}} .sub{{font-size:16pt;color:#6B7684;margin:0 0 12mm}}
.row{{display:flex;gap:12mm;align-items:flex-start}} .col{{flex:1}}
.card{{border-radius:8mm;padding:9mm 8mm;color:#fff;background:linear-gradient(120deg,#FF6B35,#FF8F5E 45%,#FFB08A)}}
.card .b{{font-weight:800;font-size:11pt}} .card .w{{font-size:17pt;font-weight:800;margin-top:6mm}} .card .c{{font-size:26pt;font-weight:800;margin-top:2mm}} .card .d{{font-size:10pt;opacity:.9}} .card .p{{display:inline-block;margin-top:5mm;background:rgba(255,255,255,.25);border-radius:99px;padding:2mm 4mm;font-size:10pt;font-weight:700}}
.cap{{font-size:11pt;color:#6B7684;margin-top:4mm;text-align:center}}
.how .h{{font-size:14pt;font-weight:800;margin-bottom:3mm}} .how ol{{padding-left:6mm;margin:0;font-size:13pt;line-height:1.7}} .how li{{margin-bottom:3mm}}
.time{{margin-top:auto;background:#F2F4F6;border-radius:5mm;padding:6mm;text-align:center;font-size:16pt;font-weight:800}}
.foot{{font-size:10pt;color:#8B95A1;text-align:center;margin-top:6mm}}
.join{{display:flex;align-items:center;gap:6mm;border:1px solid #E5E8EB;border-radius:5mm;padding:5mm 6mm;margin-top:6mm}} .join img{{width:28mm;height:28mm}} .jh{{font-size:13pt;font-weight:800}} .jt{{font-size:11pt;color:#4E5968;margin-top:2mm}}
</style></head><body>{"".join(pages)}</body></html>''')
print(f"notice.html 생성: {len(stores)}곳")
