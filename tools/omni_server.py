#!/usr/bin/env python3
"""Local HTTP server and search API for Omni Icon Vault."""
from __future__ import annotations
import argparse,json,os,random,re,sys
from collections import Counter
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs,unquote,urlparse

sys.path.insert(0,str(Path(__file__).resolve().parent))
from version import version

DEFAULT_PORT=17836
API_REVISION=4
ALIASES={
    'gear':['settings','cog'],'cog':['settings','gear'],'trash':['delete','bin'],'bin':['delete','trash'],
    'photo':['image','picture','camera'],'picture':['image','photo'],'account':['user','person','profile'],
    'person':['user','profile'],'magnify':['search'],'hamburger':['menu'],'close':['x','cancel'],
    'edit':['pencil','write'],'save':['disk','floppy'],'code':['developer','terminal'],'logo':['brand'],
}

def norm(value):
    return re.sub(r'[-_]+',' ',str(value or '')).strip().lower()

def icon_format(i):
    if i.get('svg'): return 'svg'
    if i.get('raster'): return 'raster'
    return 'font'

def icon_capabilities(i):
    """Return copy/export capabilities backed by real icon data."""
    caps=['id','manifest']
    if i.get('svg'):
        caps.extend(['svg','react'])
    if i.get('char'): caps.append('glyph')
    if i.get('html'): caps.append('html')
    if i.get('css'): caps.append('css')
    if i.get('raster'): caps.append('asset')
    # Smart is available for every indexed icon because ID is its final fallback.
    caps.append('smart')
    return caps

def supports_capability(i, capability):
    return capability in ('','all','smart') or capability in icon_capabilities(i)

class IconStore:
    def __init__(self,root):
        self.root=root;self.path=root/'browser'/'icon-data.json';self.meta_path=root/'browser'/'source-meta.json'
        self.mtime=None;self.items=[];self.by_id={};self.counts={};self.meta=[];self.stats={};self.reload(True)

    def reload(self,force=False):
        if not self.path.exists():
            raise RuntimeError(f'Icon index missing: {self.path}. Run the Omni installer first (install.py / platform installer).')
        mt=self.path.stat().st_mtime_ns
        if not force and mt==self.mtime:return
        data=json.loads(self.path.read_text('utf-8'))
        if not isinstance(data,list):raise RuntimeError('icon-data.json must be an array')
        self.items=data;self.by_id={i.get('id'):i for i in data if i.get('id')};self.counts=dict(Counter(i.get('source','unknown') for i in data));self.mtime=mt
        if self.meta_path.exists():
            try:self.meta=json.loads(self.meta_path.read_text('utf-8'))
            except Exception:self.meta=[]
        if not self.meta:self.meta=[{'source':s,'label':s.title(),'kind':'ui','count':n} for s,n in sorted(self.counts.items())]
        kinds=Counter(i.get('kind','ui') for i in data);formats=Counter(icon_format(i) for i in data);styles=Counter(i.get('style','') or 'default' for i in data)
        capabilities=Counter(cap for i in data for cap in icon_capabilities(i))
        self.stats={'total':len(data),'sourceCount':len(self.counts),'kinds':dict(kinds),'formats':dict(formats),'capabilities':dict(capabilities),'styles':dict(styles),'sources':self.counts}

    @staticmethod
    def score(i,q):
        q=norm(q)
        if not q:return 1
        raw_tokens=q.split();tokens=[]
        for token in raw_tokens:
            tokens.append(token);tokens.extend(ALIASES.get(token,[]))
        fields=[i.get('name',''),i.get('label',''),i.get('source',''),i.get('sourceLabel',''),i.get('style',''),i.get('kind',''),i.get('url','')]+list(i.get('terms',[]))
        hay=norm(' '.join(map(str,fields)));raw_match=all(t in hay for t in raw_tokens)
        alias_match=all(any(candidate in hay for candidate in [t,*ALIASES.get(t,[])]) for t in raw_tokens)
        if not raw_match and not alias_match:return 0
        name=norm(i.get('name',''));label=norm(i.get('label',''));s=10
        if name==q:s+=1100
        elif label==q:s+=1000
        elif name.startswith(q):s+=560
        elif label.startswith(q):s+=520
        elif q in name:s+=340
        elif q in label:s+=300
        if raw_match:s+=30
        if i.get('svg'):s+=4
        elif i.get('raster'):s+=2
        return s

    def _filter(self,source='all',fmt='all',capability='all'):
        self.reload();xs=self.items
        if source.startswith('kind:'):
            kind=source.split(':',1)[1]
            if kind=='brand':xs=[i for i in xs if i.get('kind') in ('brand','favicon')]
            else:xs=[i for i in xs if i.get('kind')==kind]
        elif source not in ('','all'):
            xs=[i for i in xs if i.get('source')==source]
        if fmt not in ('','all'):
            xs=[i for i in xs if icon_format(i)==fmt]
        if capability not in ('','all','smart'):
            xs=[i for i in xs if supports_capability(i,capability)]
        return xs

    def search(self,q='',source='all',fmt='all',sort='relevance',offset=0,limit=80,capability='all'):
        limit=max(1,min(int(limit),500));offset=max(0,int(offset));xs=self._filter(source,fmt,capability)
        if q.strip():
            ranked=[(self.score(i,q),i) for i in xs];ranked=[x for x in ranked if x[0]>0]
            if sort=='relevance':ranked.sort(key=lambda x:(-x[0],norm(x[1].get('label')),norm(x[1].get('style'))));xs=[i for _,i in ranked]
            else:xs=[i for _,i in ranked]
        if sort=='name':xs=sorted(xs,key=lambda i:(norm(i.get('label') or i.get('name')),norm(i.get('sourceLabel')),norm(i.get('style'))))
        elif sort=='pack':xs=sorted(xs,key=lambda i:(norm(i.get('sourceLabel') or i.get('source')),norm(i.get('label') or i.get('name')),norm(i.get('style'))))
        total=len(xs);return xs[offset:offset+limit],total

    def random(self,source='all',fmt='all',capability='all'):
        xs=self._filter(source,fmt,capability);return random.choice(xs) if xs else None

    @staticmethod
    def summary(i,preview=False):
        keys=('id','source','sourceLabel','kind','name','label','style','code','char','figmaType','fontFamily','fontStyle','raster','render','url','terms')
        out={k:i.get(k) for k in keys if i.get(k) not in (None,'',[])}
        out['format']=icon_format(i)
        out['capabilities']=icon_capabilities(i)
        if preview and i.get('svg'):out['svg']=i['svg']
        return out

class Handler(SimpleHTTPRequestHandler):
    server_version=f'OmniIconVault/{version()}'
    def log_message(self,fmt,*args):
        if not getattr(self.server,'quiet',False):super().log_message(fmt,*args)
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Methods','GET, OPTIONS');self.send_header('Access-Control-Allow-Headers','*')
        if self.path.startswith('/api/') or self.path.startswith('/browser/'):
            self.send_header('Cache-Control','no-store, no-cache, must-revalidate')
        else:
            self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
        super().end_headers()
    def do_OPTIONS(self):self.send_response(204);self.end_headers()
    def json_response(self,p,status=200):
        b=json.dumps(p,ensure_ascii=False,separators=(',',':')).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    @staticmethod
    def qint(qs,key,default):
        try:return int(qs.get(key,[str(default)])[0])
        except Exception:return default
    def do_GET(self):
        parsed=urlparse(self.path);path=unquote(parsed.path);qs=parse_qs(parsed.query);store=self.server.store
        try:
            if path=='/api/health':
                store.reload();return self.json_response({'ok':True,'product':'Omni Icon Vault','version':version(),'apiRevision':API_REVISION,'pid':os.getpid(),'root':str(store.root),'icons':len(store.items),'sources':store.counts,'sourceCount':len(store.counts)})
            if path=='/api/stats':
                store.reload();return self.json_response({'ok':True,**store.stats})
            if path=='/api/search':
                q=qs.get('q',[''])[0];source=qs.get('source',['all'])[0];fmt=qs.get('format',['all'])[0];sort=qs.get('sort',['relevance'])[0];capability=qs.get('capability',['all'])[0]
                offset=self.qint(qs,'offset',0);limit=self.qint(qs,'limit',80);preview=qs.get('include',[''])[0]=='preview'
                xs,total=store.search(q,source,fmt,sort,offset,limit,capability)
                return self.json_response({'ok':True,'apiRevision':API_REVISION,'query':q,'source':source,'format':fmt,'capability':capability,'appliedFilters':{'source':source,'format':fmt,'capability':capability},'sort':sort,'offset':offset,'count':len(xs),'total':total,'items':[store.summary(i,preview) for i in xs]})
            if path=='/api/icon':
                icon_id=qs.get('id',[''])[0];store.reload();i=store.by_id.get(icon_id)
                return self.json_response({'ok':True,'icon':i}) if i else self.json_response({'ok':False,'error':'Icon not found','id':icon_id},404)
            if path=='/api/batch':
                raw=qs.get('ids',[''])[0];ids=[x for x in raw.split(',') if x][:250];preview=qs.get('include',[''])[0]=='preview';store.reload()
                xs=[store.by_id[x] for x in ids if x in store.by_id]
                return self.json_response({'ok':True,'count':len(xs),'items':[store.summary(i,preview) for i in xs]})
            if path=='/api/random':
                source=qs.get('source',['all'])[0];fmt=qs.get('format',['all'])[0];capability=qs.get('capability',['all'])[0];i=store.random(source,fmt,capability)
                return self.json_response({'ok':True,'icon':i}) if i else self.json_response({'ok':False,'error':'No icons match that filter'},404)
            if path=='/api/sources':
                store.reload();return self.json_response({'ok':True,'sources':store.meta,'counts':store.counts})
            if path=='/':
                self.send_response(302);self.send_header('Location','/browser/index.html');self.end_headers();return
            return super().do_GET()
        except BrokenPipeError:return
        except Exception as e:return self.json_response({'ok':False,'error':str(e)},500)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--host',default='127.0.0.1');ap.add_argument('--port',type=int,default=DEFAULT_PORT);ap.add_argument('--quiet',action='store_true');a=ap.parse_args();root=Path(a.root).resolve()
    try:store=IconStore(root)
    except Exception as e:print('Omni Icon Vault:',e,file=sys.stderr);return 2
    os.chdir(root);httpd=ThreadingHTTPServer((a.host,a.port),Handler);httpd.store=store;httpd.quiet=a.quiet;print(f'Omni Icon Vault API: http://{a.host}:{a.port}/ ({len(store.items):,} icons)')
    try:httpd.serve_forever()
    except KeyboardInterrupt:pass
    finally:httpd.server_close()
    return 0
if __name__=='__main__':raise SystemExit(main())
