#!/usr/bin/env python3
"""Record and compare content hashes for an iOS build without storing local input paths.

Example: python3 scripts/build_manifest.py create build/inputs.json \
    --input profile=dm/games/<id>/game.tsv --input chain=dm/gfx/tools/dmsh_chain.lock \
    --input dependencies=cpmfile.json --artifact build/Game.ipa
Repeat with a second build and compare the two JSON documents. A signed .app can be
passed with --signed-app; codesign and its entitlements are checked and fingerprinted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def digest(path):
    """Hash bytes and relative names, not timestamps or machine-specific absolute paths."""
    path = Path(path)
    if path.is_symlink(): raise ValueError(f'symlink input is unsupported: {path}')
    if path.is_file():
        files = [('file', path)]
    elif path.is_dir():
        files = [(p.relative_to(path).as_posix(), p) for p in path.rglob('*') if p.is_file()]
        if any(p.is_symlink() for p in path.rglob('*')): raise ValueError(f'symlink input is unsupported: {path}')
        files.sort()
    else:
        raise ValueError(f'missing input: {path}')
    h = hashlib.sha256(); total = 0
    for name, p in files:
        raw_name = name.encode('utf-8', 'surrogateescape')
        h.update(len(raw_name).to_bytes(8, 'little')); h.update(raw_name)
        size = p.stat().st_size; total += size; h.update(size.to_bytes(8, 'little'))
        with p.open('rb') as f:
            while chunk := f.read(1 << 20): h.update(chunk)
    return {'sha256': h.hexdigest(), 'bytes': total, 'files': len(files)}


def signature(app):
    app = str(app)
    checked = subprocess.run(['codesign', '--verify', '--deep', '--strict', app], capture_output=True, text=True)
    if checked.returncode: raise ValueError(f'codesign verification failed: {checked.stderr.strip()}')
    ent = subprocess.run(['codesign', '-d', '--entitlements', '-', app], capture_output=True)
    if ent.returncode: raise ValueError(f'cannot read signed entitlements: {ent.stderr.decode(errors="replace").strip()}')
    return {'verified': True, 'entitlements_sha256': hashlib.sha256(ent.stdout).hexdigest()}


def make(inputs, artifact=None, signed_app=None):
    rows = {}
    for item in inputs:
        label, sep, path = item.partition('=')
        if not sep or not label or not path or label in rows: raise ValueError(f'expected a unique label=path: {item!r}')
        rows[label] = digest(path)
    if not rows: raise ValueError('at least one --input is required')
    out = {'format': 1, 'inputs': dict(sorted(rows.items()))}
    if artifact: out['artifact'] = digest(artifact)
    if signed_app: out['signature'] = signature(signed_app)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=('create', 'verify'))
    ap.add_argument('manifest', type=Path)
    ap.add_argument('--input', action='append', default=[], help='label=path; repeated, absolute paths are not recorded')
    ap.add_argument('--artifact', help='IPA or app whose bytes must match')
    ap.add_argument('--signed-app', help='signed .app to check with codesign and fingerprint its entitlements')
    a = ap.parse_args(argv)
    try:
        current = make(a.input, a.artifact, a.signed_app)
        if a.action == 'verify':
            expected = json.loads(a.manifest.read_text())
            if current != expected: raise ValueError('build manifest differs from current inputs, artifact or signature')
        else:
            a.manifest.parent.mkdir(parents=True, exist_ok=True)
            fd, temp = tempfile.mkstemp(prefix=a.manifest.name + '.', dir=a.manifest.parent)
            try:
                with os.fdopen(fd, 'w') as f: json.dump(current, f, indent=2, sort_keys=True); f.write('\n')
                os.replace(temp, a.manifest)
            finally:
                if os.path.exists(temp): os.unlink(temp)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        ap.exit(1, f'[RED] {e}\n')
    print(f'{a.action}: {a.manifest} OK')


if __name__ == '__main__': main()
