#!/usr/bin/env python3
"""9/29 첫 문자 배포 A/B 집계: 그룹별 가입·접속·사용"""
import datetime as dt, re
from common import rest
A=[("최양수","01047577104"),("장성철","01096010409"),("박승학","01027615668"),("이창범","01056145118"),("박의","01056676999"),("유춘식","01068718007"),("현호","01075183202"),("박진용","01090643613"),("김동환","01071805281"),("최성철","01097956693"),("문찬규","01073754125"),("정서영","01022341211"),("유성주","01028886099"),("김남","01039543883"),("류의홍","01055970688")]
B=[("이철봉","01054874888"),("신상호","01038666620"),("최광호","01040231976"),("박청룡","01021776661"),("이광욱","01024379328"),("허해옥","01056158852"),("김송호","01098788699"),("송재성","01029699133"),("김응빈","01077785992"),("박운","01068166955"),("김계선","01058004569"),("이영권","01042458111"),("박정태","01026191156"),("원명동","01091338881"),("김미선","01049633036")]
users={u["phone"]:u for u in rest("users?select=id,phone,created_at,invite_code_used")}
ev=rest("events?event=eq.app_open&select=user_id"); opens={}
for e in ev: opens[e["user_id"]]=opens.get(e["user_id"],0)+1
rd=rest("redemptions?select=user_id"); uses={}
for r in rd: uses[r["user_id"]]=uses.get(r["user_id"],0)+1
KST=dt.timezone(dt.timedelta(hours=9))
def show(name, grp):
    joined=[(n,p,users[p]) for n,p in grp if p in users]
    print(f"\n[{name}] 발송 {len(grp)}명 → 가입 {len(joined)}명 ({len(joined)/len(grp)*100:.0f}%)")
    for n,p,u in joined:
        t=dt.datetime.fromisoformat(re.sub(r"(\.\d{6})\d*", r"\1", u["created_at"]).replace("Z","+00:00")).astimezone(KST)
        print(f"  - {n} {p[:3]}-{p[3:7]}-{p[7:]} 가입 {t.strftime('%m/%d %H:%M')} · 접속 {opens.get(u['id'],0)} · 사용 {uses.get(u['id'],0)}")
show("A 링크+코드 (1~15)", A); show("B 확인 회신 (16~30)", B)
others=[u for p,u in users.items() if p not in dict(A+B).values()]
print(f"\n[그 외] 회원 {len(others)}명 (기존 7명 포함)")
