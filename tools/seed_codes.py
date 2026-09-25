#!/usr/bin/env python3
"""시드 초대코드 발급(1회용). 예: python3 seed_codes.py 30"""
import sys; from common import rest
codes = rest("rpc/make_seed_codes", "POST", {"n": int(sys.argv[1]) if len(sys.argv) > 1 else 30})
print("\n".join(codes))
