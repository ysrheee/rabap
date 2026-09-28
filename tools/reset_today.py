#!/usr/bin/env python3
"""오늘 사용 기록 롤백. 예: python3 reset_today.py 01065514388"""
import sys, datetime as dt
from common import rest
phone=sys.argv[1].replace("-","")
u=rest(f"users?phone=eq.{phone}&select=id")
if not u: print("해당 번호 없음"); sys.exit()
today=(dt.datetime.utcnow()+dt.timedelta(hours=9)).date().isoformat()
rest(f"redemptions?user_id=eq.{u[0]['id']}&redeemed_date=eq.{today}", "DELETE")
left=rest(f"redemptions?user_id=eq.{u[0]['id']}&select=id")
print(f"롤백 완료: {phone} 오늘 기록 삭제, 누적 남은 기록 {len(left)}건")
