#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, os, stat, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION=(ROOT/'VERSION').read_text('utf-8').strip()

EXCLUDE_DIRS={'.git','.github','dist','build','cache','vendor','__pycache__','.pytest_cache','.idea','.vscode'}
EXCLUDE_FILES={'.omni-install-state.json','README-FIRST.txt'}
GENERATED={
    'browser/icon-data.json','browser/icon-data.js','browser/source-meta.json','browser/source-meta.js',
    'favicons/registry.json'
}

def include(rel:Path, source:bool=False)->bool:
    parts=set(rel.parts)
    if any(x in EXCLUDE_DIRS for x in rel.parts):
        if not (source and '.github' in rel.parts): return False
    if rel.name in EXCLUDE_FILES: return False
    s=rel.as_posix()
    if s in GENERATED: return False
    if s.startswith('browser/assets/favicons/') and rel.name!='.gitkeep': return False
    if s.startswith('licenses/upstream/') and rel.name!='.gitkeep': return False
    if s.startswith('browser/assets/') and rel.suffix.lower() in ('.ttf','.otf','.woff','.woff2'): return False
    if not source and s.startswith('tests/'): return False
    if not source and s.startswith('scripts/'): return False
    return True

def write_entry(zf:zipfile.ZipFile,path:Path,arcname:str):
    data=path.read_bytes()
    zi=zipfile.ZipInfo(arcname)
    zi.date_time=(2026,1,1,0,0,0)
    mode=path.stat().st_mode
    if path.suffix in ('.sh','.command','.py') or path.name=='omni': mode |= stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH
    zi.external_attr=(mode & 0xFFFF)<<16
    zi.compress_type=zipfile.ZIP_DEFLATED
    zf.writestr(zi,data,compresslevel=9)

def build_zip(out:Path,platform_name:str,source:bool=False):
    prefix=f'omni-icon-vault-{VERSION}'
    with zipfile.ZipFile(out,'w') as zf:
        quick={
            'windows':'Double-click INSTALL_WINDOWS.cmd\r\nThen open a new terminal and run: omni-icons open\r\n',
            'macos':'Double-click INSTALL_MAC.command\nThen run: omni-icons open\n',
            'linux':'Run: ./INSTALL_LINUX.sh\nThen run: omni-icons open\n',
            'source':'See README.md and docs/PUBLISHING.md.\n'
        }[platform_name]
        zi=zipfile.ZipInfo(f'{prefix}/README-FIRST.txt');zi.compress_type=zipfile.ZIP_DEFLATED;zf.writestr(zi,quick)
        for p in sorted(ROOT.rglob('*')):
            if not p.is_file(): continue
            rel=p.relative_to(ROOT)
            if not include(rel,source=source): continue
            write_entry(zf,p,f'{prefix}/{rel.as_posix()}')
        # Keep empty runtime dirs present in installer bundles.
        for d in ('cache','vendor','licenses/upstream','browser/assets/favicons'):
            zi=zipfile.ZipInfo(f'{prefix}/{d}/');zi.external_attr=(0o40755 & 0xFFFF)<<16;zf.writestr(zi,b'')

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dist',default=str(ROOT/'dist'));a=ap.parse_args()
    dist=Path(a.dist).resolve();dist.mkdir(parents=True,exist_ok=True)
    outputs=[]
    for name,source in [('source',True),('windows',False),('macos',False),('linux',False)]:
        out=dist/f'Omni-Icon-Vault-{VERSION}-{name}.zip';build_zip(out,name,source);outputs.append(out);print(out)
    sums=dist/'SHA256SUMS.txt'
    sums.write_text(''.join(f'{sha256(p)}  {p.name}\n' for p in outputs),'utf-8')
    print(sums)
    return 0
if __name__=='__main__':raise SystemExit(main())
