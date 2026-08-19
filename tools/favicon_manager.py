#!/usr/bin/env python3
"""Safe local favicon collector for Omni Icon Vault."""
from __future__ import annotations
import argparse, html, json, mimetypes, os, re, shutil, struct, sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from version import version

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/'favicons'/'registry.json'
OUT=ROOT/'browser'/'assets'/'favicons'
MAX_BYTES=4*1024*1024
UA=f'Omni-Icon-Vault/{version()} (+local favicon collector)'

class HeadLinks(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.title=''
    def handle_starttag(self,tag,attrs):
        a={str(k).lower():v for k,v in attrs if k}
        if tag.lower()=='link' and a.get('href'):
            rel=(a.get('rel') or '').lower()
            if 'icon' in rel or rel in ('apple-touch-icon','apple-touch-icon-precomposed','mask-icon'):
                self.links.append((a.get('href'),rel,a.get('type') or '',a.get('sizes') or ''))
    def handle_data(self,data):
        if not self.title and data.strip(): pass


def ensure():
    REG.parent.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    if not REG.exists(): REG.write_text('[]\n','utf-8')

def load():
    ensure()
    try:
        x=json.loads(REG.read_text('utf-8')); return x if isinstance(x,list) else []
    except Exception: return []

def save(x): REG.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf-8')

def canonical_site(raw):
    raw=raw.strip()
    if not re.match(r'^https?://',raw,re.I): raw='https://'+raw
    u=urlparse(raw)
    if u.scheme not in ('http','https') or not u.hostname: raise ValueError('Use an http:// or https:// website URL.')
    # URL fragments never matter to favicons.
    return u._replace(fragment='').geturl()

def key_for(url):
    u=urlparse(url); host=(u.hostname or 'site').lower().strip('.')
    if u.port: host+=f'-{u.port}'
    return re.sub(r'[^a-z0-9.-]+','-',host).strip('-') or 'site'

def request(url,accept='*/*',timeout=20):
    req=Request(url,headers={'User-Agent':UA,'Accept':accept})
    with urlopen(req,timeout=timeout) as r:
        ctype=(r.headers.get_content_type() or '').lower(); final=r.geturl()
        data=r.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES: raise ValueError('favicon exceeds 4 MiB safety limit')
        return final,ctype,data

def score_candidate(url,rel='',ctype='',sizes=''):
    l=url.lower(); score=0
    if '.svg' in l or 'svg' in ctype: score+=500
    elif '.png' in l or 'png' in ctype: score+=400
    elif '.webp' in l or 'webp' in ctype: score+=350
    elif '.ico' in l or 'icon' in ctype: score+=250
    if 'apple-touch' in rel: score+=60
    if 'mask-icon' in rel: score-=60
    nums=[int(x) for x in re.findall(r'\b(\d+)x\d+\b',sizes or '')]
    if nums: score+=min(max(nums),512)
    if 'favicon' in l: score+=30
    return score

def discover(site):
    final,ctype,data=request(site,'text/html,application/xhtml+xml;q=0.9,*/*;q=0.2')
    candidates=[]
    if 'html' in ctype or data.lstrip().startswith((b'<!DOCTYPE',b'<html',b'<HTML')):
        text=data.decode('utf-8','replace')
        p=HeadLinks(); p.feed(text)
        for href,rel,typ,sizes in p.links:
            u=urljoin(final,html.unescape(href))
            if urlparse(u).scheme in ('http','https'): candidates.append((score_candidate(u,rel,typ,sizes),u))
        # Web app manifest may contain higher-resolution icons.
        mm=re.search(r'<link\b[^>]*\brel=["\'][^"\']*manifest[^"\']*["\'][^>]*\bhref=["\']([^"\']+)',text,re.I)
        if mm:
            mu=urljoin(final,html.unescape(mm.group(1)))
            try:
                mf,mt,md=request(mu,'application/manifest+json,application/json;q=0.9,*/*;q=0.1')
                obj=json.loads(md.decode('utf-8','replace'))
                for it in obj.get('icons',[]) if isinstance(obj,dict) else []:
                    if not isinstance(it,dict) or not it.get('src'): continue
                    u=urljoin(mf,it['src']); candidates.append((score_candidate(u,'manifest',it.get('type',''),it.get('sizes',''))+20,u))
            except Exception: pass
    # Standard fallbacks, always tried.
    origin=f'{urlparse(final).scheme}://{urlparse(final).netloc}/'
    candidates += [(220,urljoin(origin,'favicon.svg')),(210,urljoin(origin,'favicon.png')),(200,urljoin(origin,'favicon.ico'))]
    out=[]; seen=set()
    for s,u in sorted(candidates,key=lambda x:-x[0]):
        if u not in seen: seen.add(u); out.append(u)
    return final,out

def local_tag(tag): return tag.split('}',1)[-1].lower()

def sanitize_svg(raw:bytes)->bytes:
    if len(raw)>MAX_BYTES: raise ValueError('SVG too large')
    text=raw.decode('utf-8','replace')
    # Hard reject XML constructs that can fetch/expand external entities.
    if re.search(r'<!DOCTYPE|<!ENTITY',text,re.I): raise ValueError('unsafe SVG doctype/entity')
    try: root=ET.fromstring(text)
    except Exception as e: raise ValueError(f'invalid SVG: {e}')
    if local_tag(root.tag)!='svg': raise ValueError('not an SVG document')
    forbidden={'script','foreignobject','iframe','object','embed','audio','video','canvas'}
    urlish=re.compile(r'(?i)(?:javascript\s*:|data\s*:\s*text/html|url\s*\(\s*["\']?\s*(?:https?:|//))')
    def clean(el):
        for child in list(el):
            if local_tag(child.tag) in forbidden: el.remove(child); continue
            clean(child)
        for k in list(el.attrib):
            lk=local_tag(k)
            v=el.attrib.get(k,'')
            if lk.startswith('on'): el.attrib.pop(k,None); continue
            if lk=='style':
                # Preserve ordinary local presentation styles, but remove CSS capable of
                # fetching/embedding remote or executable content.
                if urlish.search(v) or re.search(r'(?i)(?:expression\s*\(|javascript\s*:|@import|behavior\s*:)',v): el.attrib.pop(k,None)
                continue
            if lk in ('href','src') and re.match(r'(?i)\s*(?:https?:|//|javascript:)',v): el.attrib.pop(k,None); continue
            if urlish.search(v): el.attrib.pop(k,None)
    clean(root)
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    return ET.tostring(root,encoding='utf-8',xml_declaration=False)

def ico_png(raw:bytes):
    if len(raw)<6: return None
    reserved,typ,count=struct.unpack_from('<HHH',raw,0)
    if reserved!=0 or typ!=1 or count<1 or len(raw)<6+16*count: return None
    imgs=[]
    for n in range(count):
        off=6+16*n; w,h,colors,res,planes,bpp,size,pos=struct.unpack_from('<BBBBHHII',raw,off)
        if pos+size<=len(raw):
            chunk=raw[pos:pos+size]
            if chunk.startswith(b'\x89PNG\r\n\x1a\n'):
                area=(w or 256)*(h or 256); imgs.append((area,bpp,size,chunk))
    return max(imgs,key=lambda x:(x[0],x[1],x[2]))[3] if imgs else None

def classify(final,ctype,data):
    lead=data[:200].lstrip().lower()
    if 'svg' in ctype or lead.startswith(b'<svg') or b'<svg' in lead[:100]: return 'svg',sanitize_svg(data)
    if 'png' in ctype or data.startswith(b'\x89PNG\r\n\x1a\n'): return 'png',data
    if 'webp' in ctype or (len(data)>12 and data[:4]==b'RIFF' and data[8:12]==b'WEBP'): return 'webp',data
    if 'jpeg' in ctype or data.startswith(b'\xff\xd8\xff'): return 'jpg',data
    if 'icon' in ctype or data[:4] in (b'\x00\x00\x01\x00',b'\x00\x00\x02\x00') or final.lower().endswith('.ico'):
        png=ico_png(data)
        return ('png',png) if png else ('ico',data)
    ext=Path(urlparse(final).path).suffix.lower().lstrip('.')
    if ext in ('svg','png','webp','jpg','jpeg','ico'): return ('jpg' if ext=='jpeg' else ext),data
    raise ValueError('unsupported favicon image format')

def rebuild():
    import subprocess
    subprocess.run([sys.executable,str(ROOT/'tools'/'build-index.py')],check=True)

def add_site(raw,do_rebuild=True):
    site=canonical_site(raw); resolved,cands=discover(site); last=[]
    chosen=None
    for u in cands[:24]:
        try:
            final,ctype,data=request(u,'image/svg+xml,image/png,image/webp,image/x-icon,image/*;q=0.8,*/*;q=0.1')
            ext,data=classify(final,ctype,data)
            if len(data)<16: raise ValueError('empty image')
            chosen=(final,ext,data); break
        except Exception as e: last.append(f'{u}: {e}')
    if not chosen:
        raise RuntimeError('No usable favicon found. Tried:\n  '+'\n  '.join(last[-8:]))
    final,ext,data=chosen; key=key_for(resolved); filename=f'{key}.{ext}'
    # Remove stale file for this site before writing the replacement.
    regs=load(); old=next((x for x in regs if x.get('key')==key),None)
    if old and old.get('file'):
        try:(OUT/old['file']).unlink(missing_ok=True)
        except Exception:pass
    (OUT/filename).write_bytes(data)
    entry={'key':key,'domain':urlparse(resolved).hostname or key,'site':site,'resolvedSite':resolved,'faviconUrl':final,'file':filename,'format':ext,'fetchedAt':datetime.now(timezone.utc).isoformat()}
    regs=[x for x in regs if x.get('key')!=key]; regs.append(entry); regs.sort(key=lambda x:x.get('domain','').lower()); save(regs)
    if do_rebuild: rebuild()
    return entry

def remove_site(ref):
    regs=load(); ref=ref.lower().strip(); removed=[]; keep=[]
    for x in regs:
        if ref in (str(x.get('key','')).lower(),str(x.get('domain','')).lower(),str(x.get('site','')).lower()): removed.append(x)
        else: keep.append(x)
    if not removed: raise SystemExit(f'Favicon not found: {ref}')
    for x in removed:
        try:(OUT/x.get('file','')).unlink(missing_ok=True)
        except Exception:pass
    save(keep); rebuild(); return removed

def cmd_list(_):
    regs=load()
    if not regs: print('No custom favicons yet. Add one with: omni-icons favicon add example.com'); return
    for x in regs: print(f"{x.get('domain',''):<32} {x.get('format',''):<5} {x.get('faviconUrl','')}")
def cmd_add(a):
    x=add_site(a.url); print(f"Added favicon:{x['key']}  {x['domain']}  ({x['format']})")
def cmd_remove(a):
    xs=remove_site(a.ref)
    for x in xs: print('Removed favicon:'+x.get('key',''))
def cmd_refresh(a):
    regs=load(); selected=[x for x in regs if not a.ref or a.ref.lower() in (str(x.get('key','')).lower(),str(x.get('domain','')).lower())]
    if not selected: raise SystemExit('No matching favicon to refresh.')
    ok=0
    for x in selected:
        try: y=add_site(x.get('site') or x.get('resolvedSite'),do_rebuild=False); print('Refreshed favicon:'+y['key']); ok+=1
        except Exception as e: print(f"WARN: {x.get('domain')}: {e}",file=sys.stderr)
    rebuild(); print(f'Refreshed {ok}/{len(selected)} favicon(s).')

def build_parser():
    p=argparse.ArgumentParser(prog='omni-icons favicon',description='Add real website favicons to your local Omni library.')
    sp=p.add_subparsers(dest='cmd',required=True)
    a=sp.add_parser('add'); a.add_argument('url'); a.set_defaults(func=cmd_add)
    a=sp.add_parser('list'); a.set_defaults(func=cmd_list)
    a=sp.add_parser('remove'); a.add_argument('ref'); a.set_defaults(func=cmd_remove)
    a=sp.add_parser('refresh'); a.add_argument('ref',nargs='?'); a.set_defaults(func=cmd_refresh)
    return p

def main(argv=None):
    a=build_parser().parse_args(argv); a.func(a)
if __name__=='__main__': main()
