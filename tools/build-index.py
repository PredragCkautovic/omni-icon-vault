#!/usr/bin/env python3
import html
import json
import re
import shutil
import sys
from pathlib import Path

from favicon_manager import sanitize_svg

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'vendor'
BROWSER = ROOT / 'browser'
ASSETS = BROWSER / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)
items=[]
seen_ids=set()

SOURCE_INFO = {
    'fontawesome': ('Font Awesome Free', 'ui'),
    'nerdfonts': ('Nerd Fonts', 'developer'),
    'bootstrap': ('Bootstrap Icons', 'ui'),
    'material': ('Material Symbols', 'ui'),
    'tabler': ('Tabler Icons', 'ui'),
    'simpleicons': ('Simple Icons', 'brand'),
    'lucide': ('Lucide', 'ui'),
    'heroicons': ('Heroicons', 'ui'),
    'phosphor': ('Phosphor', 'ui'),
    'iconoir': ('Iconoir', 'ui'),
    'ionicons': ('Ionicons', 'ui'),
    'octicons': ('Octicons', 'ui'),
    'devicon': ('Devicon', 'developer'),
    'fluent': ('Fluent UI Icons', 'ui'),
    'favicons': ('My Favicons', 'favicon'),
    'custom': ('My Custom SVGs', 'ui'),
}


def uniq_terms(xs):
    out=[]; seen=set()
    for x in xs or []:
        if not isinstance(x,str): continue
        x=x.strip()
        if x and x.lower() not in seen:
            seen.add(x.lower()); out.append(x)
    return out[:40]


def slugify(s):
    s=html.unescape(str(s or '')).strip().lower()
    s=re.sub(r'[^a-z0-9]+','-',s).strip('-')
    return s or 'icon'


def labelize(s):
    return re.sub(r'[-_]+',' ',str(s)).strip().title()


def add(**kw):
    if not kw.get('name'): return
    source=kw.get('source','')
    style=kw.get('style','')
    name=kw.get('name','')
    label,kind=SOURCE_INFO.get(source,(source.title(),kw.get('kind','ui')))
    kw.setdefault('sourceLabel',label)
    if not kw.get('kind'): kw['kind']=kind
    kw['terms']=uniq_terms(kw.get('terms',[]))
    kw['id']=kw.get('id') or ':'.join(x for x in (source,style,name) if x)
    if kw['id'] in seen_ids:
        return
    seen_ids.add(kw['id'])
    if kw.get('svg'):
        kw['figmaType']='svg'
    elif kw.get('raster'):
        kw['figmaType']='raster'
    elif source == 'nerdfonts':
        kw['figmaType']='font'; kw['fontFamily']='Symbols Nerd Font Mono'; kw['fontStyle']='Regular'
    elif source == 'material':
        kw['figmaType']='font'; kw['fontFamily']='Material Symbols Outlined'; kw['fontStyle']='Regular'
    else:
        kw.setdefault('figmaType','glyph')
    items.append(kw)


def read_svg(path, sanitize=False):
    try:
        raw=path.read_bytes()
        if sanitize:
            raw=sanitize_svg(raw)
        s=raw.decode('utf-8','replace')
    except Exception:
        return ''
    return s if re.search(r'<(?:[A-Za-z_][\w.-]*:)?svg\b', s, re.I) else ''


def best_dir(base, name, recursive=True):
    if not base.exists(): return None
    cands=[]
    direct=base/name
    if direct.is_dir(): cands.append(direct)
    if recursive:
        cands += [p for p in base.rglob(name) if p.is_dir() and p != direct]
    def score(p):
        try: return sum(1 for _ in p.rglob('*.svg'))
        except Exception: return 0
    cands=[p for p in cands if score(p)>0]
    return max(cands,key=score) if cands else None


def vector_item(source,name,svg,style='',label=None,terms=None,kind=None,render='auto'):
    label=label or labelize(name)
    css=f'/* {SOURCE_INFO.get(source,(source,))[0]} {style}: {name} */\n/* Paste the copied SVG inline; size/color it with normal SVG/CSS rules. */'
    add(source=source,name=name,label=label,style=style,code='',char='',terms=terms or [],svg=svg,html=svg,css=css,kind=kind,render=render)


def fa_class(style):
    return {'brands':'fa-brands','regular':'fa-regular','solid':'fa-solid'}.get(style,'fa-solid')


def parse_fa():
    base=VENDOR/'fontawesome'
    meta_json=next(base.rglob('icons.json'),None) if base.exists() else None
    meta_yml=next(base.rglob('icons.yml'),None) if base.exists() else None
    data=None
    if meta_json:
        try: data=json.loads(meta_json.read_text('utf-8'))
        except Exception: data=None
    if isinstance(data,dict):
        for name,v in data.items():
            code=str(v.get('unicode','')).lower(); free=(v.get('free') if 'free' in v else (v.get('styles') or []))
            label=v.get('label') or name
            search=v.get('search') or {}; terms=(search.get('terms') or []) + (v.get('aliases',{}).get('names',[]) if isinstance(v.get('aliases'),dict) else [])
            for style in free:
                if style not in ('solid','regular','brands'): continue
                svg_path=base/'svgs'/style/f'{name}.svg'
                if not svg_path.exists(): continue
                svg=read_svg(svg_path)
                if not svg: continue
                char=chr(int(code,16)) if code and re.fullmatch(r'[0-9a-f]+',code) else ''
                cls=fa_class(style); weight='400' if style in ('regular','brands') else '900'; family='Font Awesome 7 Brands' if style=='brands' else 'Font Awesome 7 Free'
                add(source='fontawesome',name=name,label=label,style=style,code=code,char=char,faClass=cls,terms=terms,svg=svg,
                    kind='brand' if style=='brands' else 'ui', render='fill', html=f'<i class="{cls} fa-{name}"></i>',
                    css=f'.icon-{name}::before {{ font-family: "{family}"; font-weight: {weight}; content: "\\{code}"; }}')
        return
    if meta_yml:
        txt=meta_yml.read_text('utf-8',errors='ignore')
        blocks=re.split(r'(?m)^(?=[a-z0-9][a-z0-9-]*:\s*$)',txt)
        for block in blocks:
            m=re.match(r'(?m)^([a-z0-9][a-z0-9-]*):\s*$',block)
            if not m: continue
            name=m.group(1)
            cm=re.search(r'(?m)^\s+unicode:\s*["\']?([0-9a-fA-F]+)',block); code=cm.group(1).lower() if cm else ''
            lm=re.search(r'(?m)^\s+label:\s*["\']?(.+?)["\']?\s*$',block); label=(lm.group(1).strip('"\'') if lm else name)
            fm=re.search(r'(?ms)^\s+free:\s*\n((?:\s+-\s+[^\n]+\n?)+)',block)
            if fm: styles=re.findall(r'(?m)^\s+-\s+([a-z]+)',fm.group(1))
            else:
                sm=re.search(r'(?ms)^\s+styles:\s*\n((?:\s+-\s+[^\n]+\n?)+)',block); styles=re.findall(r'(?m)^\s+-\s+([a-z]+)',sm.group(1)) if sm else []
            for style in styles:
                if style not in ('solid','regular','brands'): continue
                svg_path=base/'svgs'/style/f'{name}.svg'; svg=read_svg(svg_path) if svg_path.exists() else ''
                if not svg: continue
                char=chr(int(code,16)) if code else ''; cls=fa_class(style); weight='400' if style in ('regular','brands') else '900'; family='Font Awesome 7 Brands' if style=='brands' else 'Font Awesome 7 Free'
                add(source='fontawesome',name=name,label=label,style=style,code=code,char=char,faClass=cls,terms=[],svg=svg,kind='brand' if style=='brands' else 'ui',render='fill',
                    html=f'<i class="{cls} fa-{name}"></i>',css=f'.icon-{name}::before {{ font-family: "{family}"; font-weight: {weight}; content: "\\{code}"; }}')
        return
    print('WARN: Font Awesome metadata not found',file=sys.stderr)


def parse_bootstrap():
    base=VENDOR/'bootstrap'; mapping={}
    jsonf=next(base.rglob('bootstrap-icons.json'),None) if base.exists() else None
    if jsonf:
        try: mapping=json.loads(jsonf.read_text('utf-8'))
        except Exception: pass
    if not mapping:
        cssf=next(base.rglob('bootstrap-icons.css'),None) if base.exists() else None
        if cssf:
            txt=cssf.read_text('utf-8',errors='ignore')
            for name,code in re.findall(r'\.bi-([a-z0-9-]+)::before\s*\{[^}]*content:\s*["\']\\([0-9a-fA-F]+)["\']',txt,re.I|re.S): mapping[name]=code
    for name,val in mapping.items():
        if isinstance(val,int): code=f'{val:x}'
        else:
            raw=str(val).strip(); code=f'{int(raw):x}' if raw.isdigit() else raw.replace('\\','').replace('U+','').replace('u','').lower()
        if not re.fullmatch(r'[0-9a-f]+',code): continue
        svg_path=base/'icons'/f'{name}.svg'; svg=read_svg(svg_path) if svg_path.exists() else ''
        if not svg: continue
        char=chr(int(code,16))
        add(source='bootstrap',name=name,label=labelize(name),style='',code=code,char=char,terms=[],svg=svg,render='fill',
            html=f'<i class="bi bi-{name}"></i>',css=f'.icon-{name}::before {{ font-family: "bootstrap-icons"; content: "\\{code}"; }}')


def parse_nerd():
    base=VENDOR/'nerdfonts'; glyph=base/'glyphnames.json'
    if not glyph.exists(): print('WARN: Nerd Fonts glyphnames.json not found',file=sys.stderr); return
    try: data=json.loads(glyph.read_text('utf-8'))
    except Exception as e: print('WARN: Nerd Fonts JSON failed',e,file=sys.stderr); return
    for name,v in data.items():
        if not isinstance(v,dict): continue
        code=str(v.get('code','')).lower().replace('0x','')
        char=v.get('char') or (chr(int(code,16)) if re.fullmatch(r'[0-9a-f]+',code) else '')
        if not char: continue
        add(source='nerdfonts',name=name,label=name.replace('_',' ').replace('-',' '),style='',code=code,char=char,terms=['developer','terminal'],svg='',kind='developer',
            html=f'<span class="nerd-icon">&#x{code};</span>',css=f'.icon-{re.sub("[^a-zA-Z0-9_-]","-",name)}::before {{ font-family: "Symbols Nerd Font Mono"; content: "\\{code}"; }}')


def parse_material():
    base=VENDOR/'material'; cp=base/'MaterialSymbolsOutlined.codepoints'
    if not cp.exists(): print('WARN: Material codepoints not found',file=sys.stderr); return
    for line in cp.read_text('utf-8',errors='ignore').splitlines():
        bits=line.strip().split()
        if len(bits)!=2 or not re.fullmatch(r'[0-9a-fA-F]+',bits[1]): continue
        name,code=bits[0],bits[1].lower(); char=chr(int(code,16))
        add(source='material',name=name,label=name.replace('_',' ').title(),style='outlined',code=code,char=char,terms=[],svg='',
            html=f'<span class="material-symbols-outlined">{name}</span>',css=f'.material-{name} {{ font-family: "Material Symbols Outlined"; font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24; }}')


def parse_tabler():
    base=VENDOR/'tabler'; root=best_dir(base,'icons')
    if not root: print('WARN: Tabler icons directory not found',file=sys.stderr); return
    local_seen=set()
    for p in root.rglob('*.svg'):
        rel=p.relative_to(root); parts=[x.lower() for x in rel.parts[:-1]]; name=p.stem
        style='outline'
        if any(x in ('filled','fill','solid') for x in parts): style='filled'
        key=(style,name)
        if key in local_seen: continue
        svg=read_svg(p)
        if not svg: continue
        local_seen.add(key); vector_item('tabler',name,svg,style,render='stroke' if style=='outline' else 'fill')


def parse_simpleicons():
    base=VENDOR/'simpleicons'; root=best_dir(base,'icons')
    if not root: print('WARN: Simple Icons not found',file=sys.stderr); return
    for p in sorted(root.glob('*.svg')):
        svg=read_svg(p)
        if not svg: continue
        tm=re.search(r'<title>(.*?)</title>',svg,re.I|re.S)
        label=html.unescape(re.sub(r'<[^>]+>','',tm.group(1))).strip() if tm else labelize(p.stem)
        vector_item('simpleicons',p.stem,svg,'brand',label=label,terms=['brand','logo','favicon','website','company'],kind='brand',render='fill')


def parse_lucide():
    base=VENDOR/'lucide'; root=best_dir(base,'icons')
    if not root: print('WARN: Lucide icons not found',file=sys.stderr); return
    # prefer the canonical direct icons directory; avoid package/demo copies
    paths=list(root.glob('*.svg')) or list(root.rglob('*.svg'))
    for p in sorted(paths):
        svg=read_svg(p)
        if svg: vector_item('lucide',p.stem,svg,'outline',terms=['outline','stroke'],render='stroke')


def parse_heroicons():
    base=VENDOR/'heroicons'; opt=best_dir(base,'optimized')
    if not opt: print('WARN: Heroicons optimized assets not found',file=sys.stderr); return
    for p in sorted(opt.rglob('*.svg')):
        svg=read_svg(p)
        if not svg: continue
        rel=[x.lower() for x in p.relative_to(opt).parts[:-1]]
        size=next((x for x in rel if x.isdigit()),'')
        variant=next((x for x in rel if x in ('outline','solid','mini','micro')), rel[-1] if rel else '')
        style='-'.join(x for x in (size,variant) if x) or 'default'
        vector_item('heroicons',p.stem,svg,style,terms=[size,variant],render='stroke' if variant=='outline' else 'fill')


def parse_phosphor():
    base=VENDOR/'phosphor'; assets=best_dir(base,'assets')
    if not assets: print('WARN: Phosphor assets not found',file=sys.stderr); return
    weights={'thin','light','regular','bold','fill','duotone'}
    for p in sorted(assets.rglob('*.svg')):
        svg=read_svg(p)
        if not svg: continue
        style=next((part.lower() for part in p.relative_to(assets).parts[:-1] if part.lower() in weights),'regular')
        name=p.stem
        if name.endswith('-'+style): name=name[:-(len(style)+1)]
        vector_item('phosphor',name,svg,style,terms=[style],render='fill' if style=='fill' else 'auto')


def parse_iconoir():
    base=VENDOR/'iconoir'; root=best_dir(base,'icons')
    if not root: print('WARN: Iconoir icons not found',file=sys.stderr); return
    for p in sorted(root.rglob('*.svg')):
        svg=read_svg(p)
        if not svg: continue
        rel=[x.lower() for x in p.relative_to(root).parts[:-1]]
        style='solid' if 'solid' in rel or p.stem.endswith('-solid') else 'regular'
        name=p.stem[:-6] if p.stem.endswith('-solid') else p.stem
        vector_item('iconoir',name,svg,style,terms=[style],render='fill' if style=='solid' else 'stroke')


def parse_ionicons():
    base=VENDOR/'ionicons'
    roots=[]
    for rel in ('src/svg','icons'):
        p=base/rel
        if p.is_dir() and any(p.glob('*.svg')): roots=[p]; break
    if not roots:
        r=best_dir(base,'svg'); roots=[r] if r else []
    if not roots: print('WARN: Ionicons SVGs not found',file=sys.stderr); return
    root=roots[0]
    for p in sorted(root.glob('*.svg')):
        svg=read_svg(p)
        if not svg: continue
        name=p.stem; style='filled'
        for suffix in ('-outline','-sharp'):
            if name.endswith(suffix): style=suffix[1:]; name=name[:-len(suffix)]; break
        kind='brand' if name.startswith('logo-') else 'ui'
        vector_item('ionicons',name,svg,style,terms=['ionic',style,'brand' if kind=='brand' else ''],kind=kind,render='auto')


def parse_octicons():
    base=VENDOR/'octicons'; root=best_dir(base,'icons')
    if not root: print('WARN: Octicons not found',file=sys.stderr); return
    paths=list(root.glob('*.svg')) or list(root.rglob('*.svg'))
    for p in sorted(paths):
        svg=read_svg(p)
        if not svg: continue
        m=re.match(r'(.+)-(12|16|20|24|32|48)$',p.stem)
        name=m.group(1) if m else p.stem; style=m.group(2) if m else 'default'
        kind='brand' if 'github' in name else 'ui'
        vector_item('octicons',name,svg,style,terms=['github','primer',style],kind=kind,render='fill')


def parse_devicon():
    base=VENDOR/'devicon'; root=best_dir(base,'icons')
    if not root: print('WARN: Devicon icons not found',file=sys.stderr); return
    for tech in sorted([p for p in root.iterdir() if p.is_dir()]):
        for p in sorted(tech.glob('*.svg')):
            svg=read_svg(p)
            if not svg: continue
            stem=p.stem; prefix=tech.name+'-'; style=stem[len(prefix):] if stem.startswith(prefix) else stem
            vector_item('devicon',tech.name,svg,style,label=f'{labelize(tech.name)} · {labelize(style)}',terms=[tech.name,style,'developer','programming','tool','logo'],kind='developer',render='native')


def parse_fluent():
    base=VENDOR/'fluent'; assets=best_dir(base,'assets')
    if not assets: print('WARN: Fluent UI assets not found',file=sys.stderr); return
    local=set()
    for p in sorted(assets.rglob('*.svg')):
        low=str(p).lower()
        if any(x in low for x in ('/test/','/tests/','/examples/','/docs/')): continue
        svg=read_svg(p)
        if not svg: continue
        stem=re.sub(r'\s+','_',p.stem.strip())
        m=re.match(r'(.+?)[_-](\d+)[_-](regular|filled|light|color)(.*)$',stem,re.I)
        if m:
            name=slugify(m.group(1)); extra=slugify(m.group(4)) if m.group(4).strip('_- ') else ''
            style=f'{m.group(2)}-{m.group(3).lower()}' + (f'-{extra}' if extra else '')
        else:
            name=slugify(stem); style='default'
        key=(name,style)
        if key in local: continue
        local.add(key); vector_item('fluent',name,svg,style,terms=['microsoft','fluent',style],render='fill' if 'filled' in style else 'auto')


def parse_favicons():
    reg=ROOT/'favicons'/'registry.json'
    if not reg.exists(): return
    try: data=json.loads(reg.read_text('utf-8'))
    except Exception as e: print('WARN: favicon registry invalid',e,file=sys.stderr); return
    entries=data.get('favicons',[]) if isinstance(data,dict) else data
    for e in entries:
        if not isinstance(e,dict): continue
        domain=e.get('domain') or e.get('name'); fn=e.get('file'); key=e.get('key') or slugify(domain)
        if not domain or not fn: continue
        p=ASSETS/'favicons'/fn
        if not p.exists(): continue
        label=e.get('title') or domain
        site=e.get('site') or e.get('resolvedSite') or e.get('url','')
        remote=e.get('faviconUrl') or e.get('url','')
        terms=[domain,site,remote,e.get('title',''),'favicon','website','site','brand','logo']
        if p.suffix.lower()=='.svg':
            svg=read_svg(p)
            if not svg: continue
            add(id=f'favicon:{key}',source='favicons',name=domain,label=label,style='',code='',char='',terms=terms,svg=svg,html=svg,css=f'/* favicon for {domain} */',kind='favicon',render='native',url=site)
        else:
            asset_url=f'/browser/assets/favicons/{p.name}'
            add(id=f'favicon:{key}',source='favicons',name=domain,label=label,style='',code='',char='',terms=terms,svg='',raster=asset_url,html=f'<img src="{asset_url}" alt="{html.escape(label)}">',css=f'/* favicon for {domain}: {asset_url} */',kind='favicon',render='raster',url=site)



def parse_custom():
    root=ROOT/'custom-icons'
    if not root.exists(): return
    for p in sorted(root.rglob('*.svg')):
        svg=read_svg(p, sanitize=True)
        if not svg: continue
        rel=p.relative_to(root)
        style=slugify(str(rel.parent)) if str(rel.parent) != '.' else 'custom'
        name=slugify(p.stem)
        vector_item('custom',name,svg,style,label=labelize(p.stem),terms=['custom','local',str(rel.parent)],kind='ui',render='native')

def install_browser_fonts():
    nfroot=VENDOR/'nerdfonts'
    nf=next((p for p in nfroot.rglob('*Mono-Regular.ttf') if 'Symbols' in p.name),None) if nfroot.exists() else None
    if not nf and nfroot.exists(): nf=next((p for p in nfroot.rglob('*.ttf') if 'Symbols' in p.name),None)
    if nf: shutil.copy2(nf,ASSETS/'nerd-symbols.ttf')
    mf=VENDOR/'material'/'MaterialSymbolsOutlined.ttf'
    if mf.exists(): shutil.copy2(mf,ASSETS/'material-symbols-outlined.ttf')


parsers=[parse_fa,parse_bootstrap,parse_nerd,parse_material,parse_tabler,parse_simpleicons,parse_lucide,parse_heroicons,parse_phosphor,parse_iconoir,parse_ionicons,parse_octicons,parse_devicon,parse_fluent,parse_favicons,parse_custom]
for fn in parsers:
    try: fn()
    except Exception as e: print(f'WARN: {fn.__name__} failed: {e}',file=sys.stderr)
install_browser_fonts()
items.sort(key=lambda i:(i.get('source',''),i.get('style',''),i.get('name','')))
json_text=json.dumps(items,ensure_ascii=False,separators=(',',':'))
(BROWSER/'icon-data.js').write_text('window.ICON_DATA = '+json_text+';\n','utf-8')
(BROWSER/'icon-data.json').write_text(json_text+'\n','utf-8')
counts={}
for i in items: counts[i['source']]=counts.get(i['source'],0)+1
meta=[]
for src,count in sorted(counts.items(),key=lambda kv:(SOURCE_INFO.get(kv[0],('', 'z'))[1], SOURCE_INFO.get(kv[0],(kv[0],))[0])):
    label,kind=SOURCE_INFO.get(src,(src.title(),'ui')); meta.append({'source':src,'label':label,'kind':kind,'count':count})
(BROWSER/'source-meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf-8')
(BROWSER/'source-meta.js').write_text('window.SOURCE_META = '+json.dumps(meta,ensure_ascii=False,separators=(',',':'))+';\n','utf-8')
print('Built icon index:',len(items),counts)
if not items: sys.exit(2)
