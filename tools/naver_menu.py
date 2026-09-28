import sys, re, json, urllib.request, urllib.parse
UA="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
def get(url):
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept-Language":"ko"}); return urllib.request.urlopen(req, timeout=20).read().decode("utf-8","ignore")
def find_id(q):
    h=get("https://m.map.naver.com/search2/search.naver?query="+urllib.parse.quote(q))
    ids=re.findall(r'place/(\d{6,12})', h); return ids[0] if ids else None
def apollo(h):
    m=re.search(r'window\.__APOLLO_STATE__\s*=\s*(\{.*?\});\s*</script>', h, re.S) or re.search(r'window\.__APOLLO_STATE__\s*=\s*(\{.*?\})\s*;?\s*window\.', h, re.S)
    if not m: return {}
    try: return json.loads(m.group(1))
    except Exception:
        # trailing content; cut at last brace
        s=m.group(1); 
        for i in range(len(s)-1, 0, -1):
            if s[i]=='}':
                try: return json.loads(s[:i+1])
                except Exception: continue
        return {}
for q in sys.argv[1:]:
    pid=find_id(q); print(f"=== {q} → place id {pid}")
    if not pid: continue
    h=get(f"https://m.place.naver.com/restaurant/{pid}/menu/list"); st=apollo(h)
    base=None
    for k,v in st.items():
        if k.startswith("PlaceDetailBase:") and isinstance(v,dict): base=v; break
    if base: print("이름:", base.get("name"), "| 주소:", base.get("roadAddress") or base.get("address"), "| 전화:", base.get("phone") or base.get("virtualPhone"))
    menus=[(v.get("name"), v.get("price"), v.get("recommend")) for k,v in st.items() if k.startswith("Menu:") and isinstance(v,dict)]
    if not menus:
        menus=re.findall(r'"name":"([^"]{1,40})","price":"?([0-9,]+)"?', h)[:40]
    for m in menus[:40]: print("  -", m)
    # 영업시간
    for k,v in st.items():
        if "BusinessHour" in k or "businessHours" in k: print("  hours:", json.dumps(v, ensure_ascii=False)[:300]); break
    bh=re.findall(r'"day":"([^"]+)","businessHours":\{[^}]*"start":"([^"]+)","end":"([^"]+)"', h)[:7]
    if bh: print("  hours:", bh)
