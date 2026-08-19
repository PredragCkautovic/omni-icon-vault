#!/usr/bin/env python3
from __future__ import annotations
import json, sys, urllib.parse, urllib.request

BASE='http://localhost:17836'

def get(path, **params):
    q=urllib.parse.urlencode(params)
    with urllib.request.urlopen(BASE+path+('?' + q if q else ''), timeout=5) as r:
        return json.loads(r.read().decode('utf-8'))

def main():
    health=get('/api/health')
    print(f"Server: Omni {health.get('version')} · API revision {health.get('apiRevision', 0)} · {health.get('icons', 0):,} icons")
    if int(health.get('apiRevision',0)) < 3:
        print('FAIL: stale API process. Run: omni-icons open', file=sys.stderr)
        return 2
    stats=get('/api/stats').get('capabilities',{})
    rows=[]
    for cap in ('svg','glyph','html','css'):
        d=get('/api/search', capability=cap, limit=1)
        applied=d.get('appliedFilters',{}).get('capability')
        ok=applied==cap and all(cap in x.get('capabilities',[]) for x in d.get('items',[]))
        count=d.get('total',0)
        rows.append((cap,count,ok))
        print(f"{cap:>5}: {count:>7,} indexed · API applied={applied!r} · {'PASS' if ok else 'FAIL'}")
    if not all(ok for _,_,ok in rows): return 3
    counts={cap:n for cap,n,_ in rows}
    if counts['svg']==counts['glyph']==health.get('icons',0):
        print('WARN: SVG and Glyph counts equal the full index; inspect icon-data capabilities.')
    else:
        print('PASS: capability filters are changing the result set.')
    return 0

if __name__=='__main__': raise SystemExit(main())
