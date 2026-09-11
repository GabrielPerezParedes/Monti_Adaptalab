"""Fetch pinned public PhET sources, apply MONTI integration and build locally.

Run from any directory: python scripts/setup_phet.py [--fetch-only].
Source checkouts and generated HTML are deliberately excluded from this repository.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.phet'

def run(args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True)

def fetch(item):
    name, config = item
    path = WORK / name
    if not path.exists():
        run(['git', 'init', '--quiet', str(path)])
        run(['git', 'remote', 'add', 'origin', config['url']], path)
    current = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=path, capture_output=True, text=True)
    if current.stdout.strip() != config['sha']:
        dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=path, text=True)
        if dirty:
            raise RuntimeError(f'{path} contains changes. Preserve them before changing the pinned revision.')
        run(['git', 'fetch', '--quiet', '--depth', '1', 'origin', config['sha']], path)
        run(['git', 'checkout', '--quiet', '--detach', 'FETCH_HEAD'], path)
    print(f'Ready: {name}', flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch-only', action='store_true')
    args = parser.parse_args()
    lock = json.loads((ROOT / 'integrations/phet/sources.lock.json').read_text())
    WORK.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch, lock['repositories'].items()))
    if args.fetch_only:
        return
    run(['node', str(ROOT / 'integrations/phet/apply-adapter.mjs'), str(WORK / 'projectile-motion')])
    npm = shutil.which('npm')
    if not npm:
        raise RuntimeError('Install Node.js 22.12+ and npm before building PhET.')
    for name in ['chipper', 'perennial-alias', 'projectile-motion']:
        run([npm, 'ci', '--no-audit', '--no-fund'], WORK / name)
    # Run the upstream build task through tsx's Node loader. This avoids the CLI's
    # unnecessary IPC listener and works in environments that restrict sockets.
    loader = (WORK / 'perennial-alias/node_modules/tsx/dist/loader.mjs').resolve().as_uri()
    run(['node', '--import', loader, str((WORK / 'chipper/js/grunt/tasks/build.ts').resolve()),
         '--brands=adapted-from-phet', '--locales=es'], WORK / 'projectile-motion')
    built = WORK / 'projectile-motion/build/adapted-from-phet/projectile-motion_es_adapted-from-phet.html'
    if not built.is_file():
        raise RuntimeError(f'Expected PhET output missing: {built}')
    target = ROOT / 'apps/web/public/phet'
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built, target / 'projectile-motion.html')
    shutil.copy2(WORK / 'projectile-motion/LICENSE', target / 'LICENSE.txt')
    print(f'PhET ready: {target / "projectile-motion.html"}')

if __name__ == '__main__':
    main()
