#!/usr/bin/env python3
"""매장별 할인 시간 설정. 예: python3 set_window.py "부흥집" 13:30 17:00   (해제: python3 set_window.py "부흥집" -)"""
import sys; from common import rest
name=sys.argv[1]; st=rest(f"stores?name=eq.{name}&select=id")
if not st: print("매장 없음"); sys.exit(1)
body={"window_start":None,"window_end":None} if sys.argv[2]=="-" else {"window_start":sys.argv[2],"window_end":sys.argv[3]}
rest(f"stores?id=eq.{st[0]['id']}", "PATCH", body); print("설정:", name, body)
