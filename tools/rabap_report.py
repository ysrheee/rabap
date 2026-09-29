#!/usr/bin/env python3
"""라밥 정기 리포트 → 슬랙. env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SLACK_BOT_TOKEN, SLACK_CHANNEL"""
import os, json, re, urllib.request, datetime as dt
URL=os.environ["SUPABASE_URL"]; KEY=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
KST=dt.timezone(dt.timedelta(hours=9)); now=dt.datetime.now(KST); today=now.date()
def rest(path):
    req=urllib.request.Request(f"{URL}/rest/v1/{path}", headers={"apikey":KEY,"Authorization":f"Bearer {KEY}"})
    return json.loads(urllib.request.urlopen(req).read().decode())
def k(ts): return dt.datetime.fromisoformat(re.sub(r"(\.\d{6})\d*", r"\1", ts).replace("Z","+00:00")).astimezone(KST)
OWNER="01065514388"
users=[u for u in rest("users?select=id,phone,created_at,invite_code_used&order=created_at") if u["phone"]!=OWNER]
uid={u["id"]:u for u in users}
opens=rest("events?event=eq.app_open&select=user_id,created_at"); link=rest("events?event=eq.invite_open&select=visitor,created_at")
reds=rest("redemptions?select=user_id,redeemed_at,stores(name)")
new_today=[u for u in users if k(u["created_at"]).date()==today]
dau=len({e["user_id"] for e in opens if e["user_id"] in uid and k(e["created_at"]).date()==today})
uses_today=[r for r in reds if r["user_id"] in uid and k(r["redeemed_at"]).date()==today]
link_today=len({e["visitor"] for e in link if k(e["created_at"]).date()==today})
A={"01047577104","01096010409","01027615668","01056145118","01056676999","01068718007","01075183202","01090643613","01071805281","01097956693","01073754125","01022341211","01028886099","01039543883","01055970688"}
B={"01054874888","01038666620","01040231976","01021776661","01024379328","01056158852","01098788699","01029699133","01077785992","01068166955","01058004569","01042458111","01026191156","01091338881","01049633036"}
a=[u for u in users if u["phone"] in A]; b=[u for u in users if u["phone"] in B]
by_store={}
for r in uses_today: n=r["stores"]["name"]; by_store[n]=by_store.get(n,0)+1
lines=[f"*라밥 {now.strftime('%m/%d %H:%M')}*",
 f"- 회원 {len(users)}명 (오늘 +{len(new_today)}) · 오늘 앱 연 사람 {dau}명 · 초대링크 열람 {link_today}명",
 f"- 오늘 사용 {len(uses_today)}건" + (" · " + ", ".join(f"{n} {c}" for n,c in by_store.items()) if by_store else ""),
 f"- 9/29 문자 A(링크) {len(a)}/15 가입 · B(회신) {len(b)}/15 가입"]
if uses_today:
    lines.append("- 사용자: " + ", ".join(f"{uid[r['user_id']]['phone'][-4:]}({r['stores']['name']} {k(r['redeemed_at']).strftime('%H:%M')})" for r in uses_today))
text="\n".join(lines); print(text)
tok=os.environ.get("SLACK_BOT_TOKEN"); ch=os.environ.get("SLACK_CHANNEL")
if tok and ch:
    req=urllib.request.Request("https://slack.com/api/chat.postMessage", data=json.dumps({"channel":ch,"text":text}).encode(), headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json"})
    r=json.loads(urllib.request.urlopen(req).read().decode()); print("slack:", r.get("ok"), r.get("error",""))
