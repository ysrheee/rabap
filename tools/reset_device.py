#!/usr/bin/env python3
"""기기 바인딩 초기화 (폰 분실/교체 시). 예: python3 reset_device.py 01012345678"""
import sys; from common import rest
phone = sys.argv[1].replace("-", "")
rest(f"users?phone=eq.{phone}", "PATCH", {"device_id": None})
u = rest(f"users?phone=eq.{phone}&select=phone,invite_code_used")
print(f"초기화 완료: {u[0]['phone']} / 가입 코드 {u[0]['invite_code_used']} (이 코드+번호로 새 기기에서 로그인)" if u else "해당 번호 없음")
