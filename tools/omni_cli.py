#!/usr/bin/env python3
import argparse, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; INDEX=ROOT/'browser'/'icon-data.json'
sys.path.insert(0,str(ROOT/'tools'))
from platform_utils import DEFAULT_PORT, app_url, clipboard_write as platform_clipboard_write, health, open_browser, start_server, stop_server
from version import version

def load_items():
    if not INDEX.exists() or INDEX.stat().st_size < 5: raise SystemExit(f'Icon index not installed. Run: {sys.executable} {ROOT / "install.py"}')
    data=json.loads(INDEX.read_text('utf-8'))
    for i in data:
        i.setdefault('id',':'.join(x for x in (i.get('source',''),i.get('style',''),i.get('name','')) if x))
    return data

def score(i,q):
    q=q.strip().lower()
    if not q:return 1
    fields=[i.get('name',''),i.get('label',''),i.get('source',''),i.get('sourceLabel',''),i.get('style',''),i.get('kind',''),i.get('domain','')]
    terms=' '.join(map(str,i.get('terms',[]))); hay=' '.join(map(str,fields+[terms])).lower(); toks=q.split()
    if not all(t in hay for t in toks):return 0
    name=str(i.get('name','')).lower(); label=str(i.get('label','')).lower(); s=10
    if name==q:s+=1000
    elif label==q:s+=900
    elif name.startswith(q):s+=500
    elif label.startswith(q):s+=450
    elif q in name:s+=300
    elif q in label:s+=250
    for t in toks:
        if name.startswith(t):s+=40
        if t in terms.lower():s+=15
    return s

def search(items,q,source='all',limit=20):
    if source.startswith('kind:'):
        kind=source.split(':',1)[1]
        xs=[i for i in items if i.get('kind') in ('brand','favicon')] if kind=='brand' else [i for i in items if i.get('kind')==kind]
    else: xs=items if source in ('','all') else [i for i in items if i.get('source')==source]
    ranked=[(score(i,q),i) for i in xs]; ranked=[x for x in ranked if x[0]>0]
    ranked.sort(key=lambda x:(-x[0],x[1].get('label',''),x[1].get('style','')))
    return [i for _,i in ranked[:max(1,limit)]]

def find_id(items,ref):
    by={i['id']:i for i in items}
    if ref in by:return by[ref]
    matches=search(items,ref,limit=3)
    if len(matches)==1:return matches[0]
    choices='\n'.join('  '+i['id'] for i in matches)
    raise SystemExit(f'Icon not uniquely resolved: {ref}\n{choices}' if choices else f'Icon not found: {ref}')

def raster_path(i):
    r=i.get('raster','')
    return ROOT/r.lstrip('/') if r else None

def smart_format(i): return 'svg' if i.get('svg') else ('asset' if i.get('raster') else ('html' if i.get('source')=='material' else 'glyph'))

def value(i,fmt):
    if fmt=='smart':fmt=smart_format(i)
    if fmt=='id':return i.get('id','')
    if fmt=='svg':return i.get('svg','')
    if fmt=='html':return i.get('html','') or i.get('char','')
    if fmt=='css':return i.get('css','')
    if fmt=='glyph':return i.get('char','')
    if fmt=='asset':return str(raster_path(i) or '')
    if fmt=='json':return json.dumps(i,ensure_ascii=False,indent=2)
    raise SystemExit('Unknown format: '+fmt)

def clipboard_write(text):
    if not text: raise SystemExit('Selected icon has no content in that format.')
    if platform_clipboard_write(text): return True
    print(text)
    print('\nNo platform clipboard command was available; printed to stdout instead.', file=sys.stderr)
    return False

def safe_name(name):
    return ''.join(x[:1].upper()+x[1:] for x in re.split(r'[^A-Za-z0-9]+',str(name)) if x) or 'Icon'
def indent(s,n): return '\n'.join(' '*n+x for x in s.splitlines())
def jsx_svg(svg):
    for a,b in {'class=':'className=','stroke-width=':'strokeWidth=','stroke-linecap=':'strokeLinecap=','stroke-linejoin=':'strokeLinejoin=','fill-rule=':'fillRule=','clip-rule=':'clipRule=','fill-opacity=':'fillOpacity=','stroke-opacity=':'strokeOpacity=','xlink:href=':'xlinkHref='}.items():svg=svg.replace(a,b)
    m=re.search(r'<svg\b[^>]*>',svg,re.I|re.S)
    if m:
        op=re.sub(r'\s(?:width|height)=("[^"]*"|\'[^\']*\')','',m.group(0),flags=re.I); op=op[:-1]+' {...props}>'; svg=svg[:m.start()]+op+svg[m.end():]
    return svg

def copy_raster(i,out:Path,stem):
    src=raster_path(i)
    if not src or not src.is_file():raise SystemExit(f'{i["id"]} raster asset is missing.')
    ext=src.suffix.lower() or '.png'; dst=out/(stem+ext); shutil.copy2(src,dst); return dst

def export_one(i,out:Path,fmt,alias=None):
    out.mkdir(parents=True,exist_ok=True); alias=alias or safe_name(i.get('name','icon')); stem=re.sub(r'[^a-zA-Z0-9._-]+','-',alias).strip('-') or 'icon'
    if fmt=='asset':
        if i.get('svg'):
            p=out/(stem+'.svg'); p.write_text(i['svg'],'utf-8'); return p
        return copy_raster(i,out,stem)
    if fmt=='svg':
        if not i.get('svg'):raise SystemExit(f'{i["id"]} has no SVG; use --format asset for raster favicons.')
        p=out/(stem+'.svg');p.write_text(i['svg'],'utf-8');return p
    if fmt in ('html','css','json'):
        p=out/(stem+'.'+fmt);p.write_text(value(i,fmt)+'\n','utf-8');return p
    comp='Icon'+safe_name(alias)
    if fmt=='react':
        if i.get('svg'): text=f'import * as React from "react";\n\nexport function {comp}(props: React.SVGProps<SVGSVGElement>) {{\n  return (\n{indent(jsx_svg(i["svg"]),4)}\n  );\n}}\n'
        elif i.get('raster'):
            asset=copy_raster(i,out,stem); text=f'import * as React from "react";\nimport iconUrl from "./{asset.name}";\n\nexport function {comp}(props: React.ImgHTMLAttributes<HTMLImageElement>) {{\n  return <img src={{iconUrl}} alt="" {{...props}} />;\n}}\n'
        else:
            fam=i.get('fontFamily') or ('Material Symbols Outlined' if i.get('source')=='material' else 'Symbols Nerd Font Mono'); ch=i.get('char','')
            text=f'import * as React from "react";\n\nexport function {comp}(props: React.HTMLAttributes<HTMLSpanElement>) {{\n  return <span {{...props}} style={{{{fontFamily: {json.dumps(fam)}, lineHeight: 1, ...props.style}}}}>{ch}</span>;\n}}\n'
        p=out/(comp+'.tsx');p.write_text(text,'utf-8');return p
    if fmt=='vue':
        if i.get('svg'): text='<template>\n'+indent(i['svg'],2)+'\n</template>\n'
        elif i.get('raster'):
            asset=copy_raster(i,out,stem); text=f'<script setup>\nimport iconUrl from "./{asset.name}"\n</script>\n<template>\n  <img :src="iconUrl" alt="" />\n</template>\n'
        else:
            fam=i.get('fontFamily','Symbols Nerd Font Mono'); text=f'<template>\n  <span style="font-family: {fam}; line-height: 1">{i.get("char","")}</span>\n</template>\n'
        p=out/(alias+'.vue');p.write_text(text,'utf-8');return p
    if fmt=='svelte':
        if i.get('svg'):text=i['svg']+'\n'
        elif i.get('raster'):
            asset=copy_raster(i,out,stem);text=f'<script>import iconUrl from "./{asset.name}";</script>\n<img src={{iconUrl}} alt="" />\n'
        else:text=f'<span style="font-family: {i.get("fontFamily","Symbols Nerd Font Mono")}; line-height:1">{i.get("char","")}</span>\n'
        p=out/(alias+'.svelte');p.write_text(text,'utf-8');return p
    raise SystemExit('Unsupported export format: '+fmt)

def cmd_search(a):
    xs=search(load_items(),a.query,a.source,a.limit)
    if a.json:print(json.dumps([{k:i.get(k) for k in ('id','label','source','sourceLabel','kind','style','figmaType')} for i in xs],ensure_ascii=False,indent=2));return
    for i in xs:print(f'{i["id"]:<60} {i.get("label",i.get("name",""))}  [{i.get("sourceLabel",i.get("source",""))}]')
def cmd_show(a):print(json.dumps(find_id(load_items(),a.icon),ensure_ascii=False,indent=2))
def cmd_copy(a):
    i=find_id(load_items(),a.icon);fmt=smart_format(i) if a.format=='smart' else a.format
    if fmt=='asset':
        p=raster_path(i)
        if not p:raise SystemExit('No raster asset for this icon.')
        print(p);return
    if clipboard_write(value(i,fmt)):print(f'Copied {fmt}: {i["id"]}')
def cmd_export(a):
    items=load_items();out=Path(a.out).expanduser().resolve()
    for ref in a.icons:print(export_one(find_id(items,ref),out,a.format))
def cmd_init(a):
    dest=Path(a.path).expanduser().resolve();dest.mkdir(parents=True,exist_ok=True);p=dest/'omni-icons.json'
    if p.exists() and not a.force:raise SystemExit(f'{p} already exists (use --force).')
    sample={'format':'svg','out':'src/icons','icons':[{'id':'tabler:outline:camera','as':'Camera'},{'id':'simpleicons:brand:github','as':'Github'}]};p.write_text(json.dumps(sample,indent=2)+'\n','utf-8');print(p)
def sha256(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cmd_sync(a):
    manifest=Path(a.manifest).expanduser().resolve();cfg=json.loads(manifest.read_text());base=manifest.parent;fmt=a.format or cfg.get('format','svg');out=(base/(a.out or cfg.get('out','src/icons'))).resolve();items=load_items();written=[]
    for spec in cfg.get('icons',[]):
        ref=spec if isinstance(spec,str) else spec['id'];alias=None if isinstance(spec,str) else spec.get('as');written.append(export_one(find_id(items,ref),out,fmt,alias))
    lock={'generatedBy':f'Omni Icon Vault {version()}','format':fmt,'icons':[{'path':str(p.relative_to(base)),'sha256':sha256(p)} for p in written]};(base/'omni-icons.lock.json').write_text(json.dumps(lock,indent=2)+'\n');print(f'Synced {len(written)} files -> {out}')
def cmd_serve(a):
    from omni_server import main as server_main
    sys.argv=['omni_server.py','--root',str(ROOT),'--host',a.host,'--port',str(a.port)]+(['--quiet'] if a.quiet else []);raise SystemExit(server_main())
def cmd_favicon(a):
    from favicon_manager import main as fav_main
    return fav_main(a.args)
def cmd_rebuild(a):
    subprocess.run([sys.executable,str(ROOT/'tools'/'build-index.py')],check=True)
    print('Omni index rebuilt.')


def cmd_start(a):
    r=start_server(a.port)
    h=r['health']; print(f"Omni Icon Vault ready: {app_url(a.port)}/  ({h.get('icons',0):,} icons)")
def cmd_stop(a):
    stopped=stop_server(a.port); print('Omni Icon Vault stopped.' if stopped else 'No standalone Omni server PID was found.')
def cmd_status(a):
    h=health(a.port)
    if h: print(json.dumps({'running':True,'url':app_url(a.port),'health':h},ensure_ascii=False,indent=2)); return
    print(json.dumps({'running':False,'url':app_url(a.port)},indent=2)); raise SystemExit(1)
def cmd_open(a):
    print(open_browser(a.port))
def cmd_figma(a):
    r=start_server(a.port)
    manifest=ROOT/'figma-plugin'/'manifest.json'
    print(f'Omni server ready: {app_url(a.port)}/')
    print('Figma Desktop -> Plugins -> Development -> Import plugin from manifest...')
    print(manifest)

def cmd_update(a):
    cmd=[sys.executable,str(ROOT/'install.py'),'--refresh']
    if a.core_only: cmd.append('--core-only')
    if a.no_autostart: cmd.append('--no-autostart')
    raise SystemExit(subprocess.run(cmd,cwd=ROOT).returncode)

def cmd_doctor(a):
    problems=[]
    print(f'Omni Icon Vault {version()}')
    print(f'Root:   {ROOT}')
    print(f'Python: {sys.version.split()[0]} ({sys.executable})')
    try:
        items=load_items(); print(f'Index:  OK ({len(items):,} icons)')
        sources=sorted({i.get('source') for i in items if i.get('source')}); print('Packs:  '+', '.join(sources))
    except BaseException as e:
        print(f'Index:  FAIL ({e})'); problems.append('index')
    try:
        json.loads((ROOT/'figma-plugin'/'manifest.json').read_text('utf-8')); print('Figma:  manifest OK')
    except Exception as e:
        print(f'Figma:  FAIL ({e})'); problems.append('figma')
    h=health(a.port); print(f'Server: '+(f"OK ({app_url(a.port)})" if h else 'not running (run: omni-icons start)'))
    if problems: raise SystemExit(2)

def build_parser():
    p=argparse.ArgumentParser(prog='omni-icons',description=f'Omni Icon Vault {version()} — search, Figma, favicons and design-to-code')
    p.add_argument('--version',action='version',version=f'Omni Icon Vault {version()}')
    sp=p.add_subparsers(dest='cmd',required=True)
    s=sp.add_parser('search');s.add_argument('query');s.add_argument('--source',default='all',help='pack name or kind:ui / kind:brand / kind:developer / kind:favicon');s.add_argument('-n','--limit',type=int,default=20);s.add_argument('--json',action='store_true');s.set_defaults(func=cmd_search)
    s=sp.add_parser('show');s.add_argument('icon');s.set_defaults(func=cmd_show)
    s=sp.add_parser('copy');s.add_argument('icon');s.add_argument('--format',choices=['smart','svg','html','css','glyph','asset','id','json'],default='smart');s.set_defaults(func=cmd_copy)
    s=sp.add_parser('export');s.add_argument('icons',nargs='+');s.add_argument('--out',default='./omni-icons');s.add_argument('--format',choices=['asset','svg','html','css','json','react','vue','svelte'],default='svg');s.set_defaults(func=cmd_export)
    s=sp.add_parser('init');s.add_argument('path',nargs='?',default='.');s.add_argument('--force',action='store_true');s.set_defaults(func=cmd_init)
    s=sp.add_parser('sync');s.add_argument('manifest',nargs='?',default='omni-icons.json');s.add_argument('--out');s.add_argument('--format',choices=['asset','svg','html','css','json','react','vue','svelte']);s.set_defaults(func=cmd_sync)
    s=sp.add_parser('serve');s.add_argument('--host',default='127.0.0.1');s.add_argument('--port',type=int,default=17836);s.add_argument('--quiet',action='store_true');s.set_defaults(func=cmd_serve)
    s=sp.add_parser('favicon',help='add/list/remove/refresh real website favicons');s.add_argument('args',nargs=argparse.REMAINDER);s.set_defaults(func=cmd_favicon)
    s=sp.add_parser('rebuild',help='re-index installed packs, favicons and custom SVGs');s.set_defaults(func=cmd_rebuild)
    s=sp.add_parser('start',help='start the local browser/Figma API');s.add_argument('--port',type=int,default=DEFAULT_PORT);s.set_defaults(func=cmd_start)
    s=sp.add_parser('stop',help='stop the standalone local server');s.add_argument('--port',type=int,default=DEFAULT_PORT);s.set_defaults(func=cmd_stop)
    s=sp.add_parser('status',help='show local server status');s.add_argument('--port',type=int,default=DEFAULT_PORT);s.set_defaults(func=cmd_status)
    s=sp.add_parser('open',aliases=['launch'],help='start Omni and open the icon browser');s.add_argument('--port',type=int,default=DEFAULT_PORT);s.set_defaults(func=cmd_open)
    s=sp.add_parser('doctor',help='check the installation');s.add_argument('--port',type=int,default=DEFAULT_PORT);s.set_defaults(func=cmd_doctor)
    s=sp.add_parser('figma',help='start the local API and show Figma plugin setup path');s.add_argument('--port',type=int,default=DEFAULT_PORT);s.set_defaults(func=cmd_figma)
    s=sp.add_parser('update',help='redownload pinned sources and rebuild Omni');s.add_argument('--core-only',action='store_true');s.add_argument('--no-autostart',action='store_true');s.set_defaults(func=cmd_update)
    return p

def main():
    a=build_parser().parse_args();return a.func(a) or 0
if __name__=='__main__':raise SystemExit(main())
