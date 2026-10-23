#!/usr/bin/env python3
"""Safely populate an existing, empty StreamDock M18 gallery scene."""
import argparse, copy, json, os, shutil, subprocess, uuid
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROFILES=Path.home()/'Library/Application Support/HotSpot/StreamDock/profiles'

def choose_profile(scene: str, explicit: Path | None):
    if explicit:
        candidates=[explicit/'manifest.json' if explicit.is_dir() else explicit]
    else:
        candidates=list(PROFILES.glob('*.sdProfile/manifest.json'))
    matches=[]
    for path in candidates:
        try: d=json.loads(path.read_text())
        except (OSError, ValueError): continue
        if d.get('DeviceUUID')=='M18V25E' and d.get('Name')==scene:
            matches.append((path,d))
    if len(matches)!=1:
        raise SystemExit(f'Expected exactly one M18V25E scene named {scene!r}; found {len(matches)}. '
                         'Create an empty scene in StreamDock first, or pass --profile PATH.')
    return matches[0]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene',default='岩点陈列柜',help='exact name of an empty M18 scene')
    parser.add_argument('--profile',type=Path,help='explicit .sdProfile directory or manifest.json')
    args=parser.parse_args()
    if subprocess.run(['pgrep','-x','StreamDock'],capture_output=True).returncode==0:
        raise SystemExit('Quit StreamDock completely before installation, then rerun.')
    path,data=choose_profile(args.scene,args.profile)
    if data.get('Actions'):
        raise SystemExit('Scene is not empty. Refusing to overwrite existing actions; create a fresh scene.')
    holds=json.loads((ROOT/'gallery.json').read_text())
    if len(holds)!=15 or len({h['id'] for h in holds})!=15:
        raise SystemExit('gallery.json must contain 15 unique hold IDs.')
    app=ROOT/'dist'/'ClimbingHoldCard.app'
    if not app.is_dir(): raise SystemExit('Build the app with python3 scripts/build.py first.')
    for h in holds:
        if not (ROOT/'assets'/f"{h['id']}-key.png").is_file(): raise SystemExit(f"Missing key image {h['id']}")
        if not (ROOT/'dist'/'launchers'/f"{h['id']}.app").is_dir(): raise SystemExit(f"Missing launcher {h['id']}")
    backup=ROOT/'backups';backup.mkdir(exist_ok=True)
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy2(path, backup/f'{path.parent.stem}-{stamp}-before-install.json')
    images=path.parent/'Images';images.mkdir(exist_ok=True)
    actions={}
    for i,h in enumerate(holds):
        ident=h['id'];img=f'm18-hold-{i+1:02d}-{ident}.png'
        shutil.copy2(ROOT/'assets'/f'{ident}-key.png',images/img)
        actions[f'{i%5},{2-i//5}']={
            'ActionID':str(uuid.uuid4()),'Controller':'Keypad','Name':'Open',
            'Settings':{'path':str((ROOT/'dist'/'launchers'/f'{ident}.app').resolve())},
            'State':0,'States':[{'FontFamily':'HarmonyOS Sans','FontSize':8,
                        'FontStyle':'Regular','FontUnderline':False,
                        'Image':img,'MultiActionImage':'','Name':'',
                        'ShowTitle':False,'Title':'',
                        'TitleAlignment':'bottom','TitleColor':'#ffffff'}],
            'UUID':'com.hotspot.streamdock.system.open'}
    updated=copy.deepcopy(data); updated['Actions']=actions
    temp=path.with_name('manifest.json.m18-new')
    temp.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n')
    os.replace(temp,path)
    print(f'Installed {len(actions)} keys into {args.scene}; reopen StreamDock. Backup in {backup}/')

if __name__=='__main__':main()
