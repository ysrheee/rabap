#!/usr/bin/env python3
"""누가 누구를 초대했는지 트리로 출력 (users.invited_by 기준)"""
from common import rest
users=rest("users?select=id,phone,invited_by,invite_code_used,created_at&order=created_at")
by={u["id"]:u for u in users}; kids={}
for u in users: kids.setdefault(u["invited_by"], []).append(u)
def fmt(u): return f"{u['phone'][:3]}-{u['phone'][3:7]}-{u['phone'][7:]} (가입 {u['created_at'][5:16].replace('T',' ')}, 코드 {u['invite_code_used']})"
def walk(pid, depth):
    for u in kids.get(pid, []):
        print("  "*depth + ("└ " if depth else "• ") + fmt(u)); walk(u["id"], depth+1)
print("[시드 코드로 직접 가입]"); walk(None, 0)
