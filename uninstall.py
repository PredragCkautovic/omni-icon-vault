#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from platform_utils import cli_bin_dir, font_dir, refresh_fonts, remove_windows_user_path, stop_server, system_name

STATE=ROOT/'.omni-install-state.json'

def remove_path(p:Path):
    try:
        if p.is_dir(): shutil.rmtree(p)
        else: p.unlink(missing_ok=True)
    except Exception as e: print(f'WARN: could not remove {p}: {e}',file=sys.stderr)

def stop_os_autostart():
    system=system_name()
    if system=='linux' and shutil.which('systemctl'):
        subprocess.run(['systemctl','--user','disable','--now','omni-icon-vault.service'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        subprocess.run(['systemctl','--user','daemon-reload'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
    elif system=='darwin' and shutil.which('launchctl'):
        agent=Path.home()/'Library'/'LaunchAgents'/'local.omniiconvault.server.plist'
        subprocess.run(['launchctl','unload',str(agent)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)

def main():
    ap=argparse.ArgumentParser(description='Remove Omni Icon Vault integrations and optionally downloaded data.')
    ap.add_argument('--purge-data',action='store_true',help='also delete cache, vendor assets and generated index (custom icons/favicons are preserved)')
    a=ap.parse_args()
    stop_server(); stop_os_autostart()
    state={}
    if STATE.exists():
        try: state=json.loads(STATE.read_text('utf-8'))
        except Exception: pass
    for x in state.get('created',[]): remove_path(Path(x))
    for x in state.get('fonts',[]):
        p=Path(x)
        if system_name()=='windows':
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows NT\CurrentVersion\Fonts',0,winreg.KEY_ALL_ACCESS) as key:
                    try: winreg.DeleteValue(key,f'Omni Icon Vault - {p.stem}')
                    except FileNotFoundError: pass
            except Exception: pass
        remove_path(p)
    refresh_fonts()
    if state.get('windows_path_modified'):
        try: remove_windows_user_path(cli_bin_dir())
        except Exception as e: print(f'WARN: could not remove PATH entry: {e}',file=sys.stderr)
    if STATE.exists(): STATE.unlink()
    if a.purge_data:
        for d in (ROOT/'cache',ROOT/'vendor'): 
            shutil.rmtree(d,ignore_errors=True); d.mkdir(exist_ok=True); (d/'.gitkeep').touch()
        for asset in (ROOT/'browser'/'assets'/'nerd-symbols.ttf', ROOT/'browser'/'assets'/'material-symbols-outlined.ttf'):
            asset.unlink(missing_ok=True)
        for f,content in ((ROOT/'browser'/'icon-data.json','[]\n'),(ROOT/'browser'/'icon-data.js','window.ICON_DATA=[];\n'),(ROOT/'browser'/'source-meta.json','[]\n'),(ROOT/'browser'/'source-meta.js','window.OMNI_SOURCE_META=[];\n')):
            f.write_text(content,'utf-8')
    print('Removed Omni Icon Vault CLI, desktop/startup integration and installed fonts.')
    print('The repository folder, custom-icons/ and favicons/ were left intact.')
    if a.purge_data: print('Downloaded vendor/cache data was also removed.')
    return 0
if __name__=='__main__': raise SystemExit(main())
