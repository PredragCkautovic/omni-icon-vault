#!/usr/bin/env python3
import argparse,json,os,re,sys
from collections import Counter
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from version import version
from urllib.parse import parse_qs,unquote,urlparse
DEFAULT_PORT=17836
class IconStore:
    def __init__(self,root):self.root=root;self.path=root/'browser'/'icon-data.json';self.meta_path=root/'browser'/'source-meta.json';self.mtime=None;self.items=[];self.by_id={};self.counts={};self.meta=[];self.reload(True)
    def reload(self,force=False):
        if not self.path.exists():raise RuntimeError(f'Icon index missing: {self.path}. Run the Omni installer first (install.py / platform installer).')
        mt=self.path.stat().st_mtime_ns
        if not force and mt==self.mtime:return
        data=json.loads(self.path.read_text('utf-8'))
        if not isinstance(data,list):raise RuntimeError('icon-data.json must be an array')
        self.items=data;self.by_id={i.get('id'):i for i in data if i.get('id')};self.counts=dict(Counter(i.get('source','unknown') for i in data));self.mtime=mt
        if self.meta_path.exists():
            try:self.meta=json.loads(self.meta_path.read_text('utf-8'))
            except Exception:self.meta=[]
        if not self.meta:
            self.meta=[{'source':s,'label':s.title(),'kind':'ui','count':n} for s,n in sorted(self.counts.items())]
    @staticmethod
    def score(i,q):
        q=q.strip().lower()
        if not q:return 1
        fields=[i.get('name',''),i.get('label',''),i.get('source',''),i.get('sourceLabel',''),i.get('style',''),i.get('kind',''),i.get('url','')]+list(i.get('terms',[]))
        hay=' '.join(map(str,fields)).lower();toks=q.split()
        if not all(t in hay for t in toks):return 0
        name=str(i.get('name','')).lower();label=str(i.get('label','')).lower();s=10
        if name==q:s+=1000
        elif label==q:s+=900
        elif name.startswith(q):s+=500
        elif label.startswith(q):s+=450
        elif q in name:s+=300
        elif q in label:s+=250
        if i.get('svg'):s+=3
        elif i.get('raster'):s+=2
        return s
    def search(self,q='',source='all',limit=80):
        self.reload();limit=max(1,min(int(limit),500))
        if source.startswith('kind:'):
            kind=source.split(':',1)[1]
            if kind=='brand':xs=[i for i in self.items if i.get('kind') in ('brand','favicon')]
            else:xs=[i for i in self.items if i.get('kind')==kind]
        else:xs=self.items if source in ('','all') else [i for i in self.items if i.get('source')==source]
        if q.strip():
            ranked=[(self.score(i,q),i) for i in xs];ranked=[x for x in ranked if x[0]>0];ranked.sort(key=lambda x:(-x[0],x[1].get('label',''),x[1].get('style','')));xs=[i for _,i in ranked]
        return xs[:limit]
    @staticmethod
    def summary(i):
        keys=('id','source','sourceLabel','kind','name','label','style','code','char','figmaType','fontFamily','fontStyle','raster','render','url')
        return {k:i.get(k) for k in keys if i.get(k) not in (None,'')}
class Handler(SimpleHTTPRequestHandler):
    server_version=f'OmniIconVault/{version()}'
    def log_message(self,fmt,*args):
        if not getattr(self.server,'quiet',False):super().log_message(fmt,*args)
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Methods','GET, OPTIONS');self.send_header('Access-Control-Allow-Headers','*');self.send_header('Cache-Control','no-store');super().end_headers()
    def do_OPTIONS(self):self.send_response(204);self.end_headers()
    def json_response(self,p,status=200):
        b=json.dumps(p,ensure_ascii=False,separators=(',',':')).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        parsed=urlparse(self.path);path=unquote(parsed.path);qs=parse_qs(parsed.query);store=self.server.store
        try:
            if path=='/api/health':store.reload();return self.json_response({'ok':True,'version':version(),'icons':len(store.items),'sources':store.counts})
            if path=='/api/search':
                q=qs.get('q',[''])[0];source=qs.get('source',['all'])[0]
                try:limit=int(qs.get('limit',['80'])[0])
                except Exception:limit=80
                xs=store.search(q,source,limit);return self.json_response({'ok':True,'query':q,'source':source,'count':len(xs),'items':[store.summary(i) for i in xs]})
            if path=='/api/icon':
                icon_id=qs.get('id',[''])[0];store.reload();i=store.by_id.get(icon_id)
                return self.json_response({'ok':True,'icon':i}) if i else self.json_response({'ok':False,'error':'Icon not found','id':icon_id},404)
            if path=='/api/sources':store.reload();return self.json_response({'ok':True,'sources':store.meta,'counts':store.counts})
            if path=='/':self.send_response(302);self.send_header('Location','/browser/index.html');self.end_headers();return
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
