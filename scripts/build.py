#!/usr/bin/env python3
"""Build macOS card app and 15 open-action launchers from user assets."""
import json, plistlib, shutil, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT/'dist'

def run(*args): subprocess.run(args, check=True)

def main():
    holds=json.loads((ROOT/'gallery.json').read_text())
    assert len(holds)==15 and len({h['id'] for h in holds})==15, 'M18 needs 15 unique hold IDs'
    for h in holds:
        for suffix in ('.png','-key.png'):
            if not (ROOT/'assets'/f"{h['id']}{suffix}").is_file():
                raise SystemExit(f"Missing assets/{h['id']}{suffix}; run prepare_assets.py first")
    if DIST.exists(): shutil.rmtree(DIST)
    app=DIST/'ClimbingHoldCard.app'; content=app/'Contents'
    (content/'MacOS').mkdir(parents=True); (content/'Resources'/'icons').mkdir(parents=True)
    info={'CFBundleName':'Climbing Hold Card','CFBundleDisplayName':'Climbing Hold Card',
          'CFBundleExecutable':'ClimbingHoldCard','CFBundleIdentifier':'local.github.m18climbingholds.card',
          'CFBundlePackageType':'APPL','CFBundleVersion':'1.0','CFBundleShortVersionString':'1.0',
          'LSUIElement':True,
          'CFBundleURLTypes':[{'CFBundleURLName':'Climbing Hold Card','CFBundleURLSchemes':['climbhold']}]}
    with (content/'Info.plist').open('wb') as f: plistlib.dump(info,f)
    shutil.copy2(ROOT/'gallery.json',content/'Resources'/'gallery.json')
    for h in holds: shutil.copy2(ROOT/'assets'/f"{h['id']}.png",content/'Resources'/'icons'/f"{h['id']}.png")
    run('swiftc','-O',str(ROOT/'ClimbingHoldCard.swift'),'-o',str(content/'MacOS'/'ClimbingHoldCard'))
    run('codesign','--force','--deep','--sign','-',str(app))
    launch=DIST/'launchers';launch.mkdir()
    binary=DIST/'HoldLauncher'
    run('swiftc','-O',str(ROOT/'HoldLauncher.swift'),'-o',str(binary))
    for h in holds:
        identifier=h['id']; bundle=launch/f'{identifier}.app'; dest=bundle/'Contents'
        (dest/'MacOS').mkdir(parents=True)
        shutil.copy2(binary,dest/'MacOS'/'HoldLauncher')
        metadata={'CFBundleName':f'Hold {identifier}','CFBundleExecutable':'HoldLauncher',
                  'CFBundleIdentifier':f'local.github.m18climbingholds.launcher.{identifier}',
                  'CFBundlePackageType':'APPL','CFBundleVersion':'1.0','LSUIElement':True,
                  'ClimbingHoldID':identifier}
        with (dest/'Info.plist').open('wb') as f:plistlib.dump(metadata,f)
        run('codesign','--force','--sign','-',str(bundle))
    binary.unlink()
    print(f'Built {app} and {len(holds)} launchers. The app is ad-hoc signed for local use only.')

if __name__=='__main__':main()
