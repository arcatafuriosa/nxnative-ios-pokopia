#!/usr/bin/env python3
"""Summarize PSO seed/user coverage and optional runtime counters without starting the game.

Usage: python3 scripts/pso_preheat_audit.py pso_manifest.tsv pso_user.tsv --log log.txt
The JSON contains counts only; shader and pipeline keys stay in the local input files.
"""
import argparse
import json
from pathlib import Path
import re


def rows(path):
    seen = set(); lines = 0; duplicates = 0
    for raw in Path(path).read_text().splitlines():
        if not raw or raw.startswith('#'): continue
        cells = raw.split('\t')
        if cells[0] == 'S' and len(cells) >= 3 and cells[1] and cells[2].isdigit(): key = tuple(cells[:3])
        elif cells[0] in ('R', 'C') and len(cells) >= 2 and cells[1]: key = tuple(cells[:2])
        else: raise ValueError(f'{path}: invalid PSO manifest row {lines + 1}')
        lines += 1
        if key in seen: duplicates += 1
        seen.add(key)
    return seen, lines, duplicates


def log_stats(path):
    text = Path(path).read_text(errors='replace')
    num = lambda pat: [float(x) for x in re.findall(pat, text)]
    hits = num(r'archive lookups found (\d+) /'); misses = num(r'found none (\d+) /')
    waits = num(r'pipeline wait ([\d.]+) ms')
    return {'submit_pso_ms': round(sum(num(r'on the submit thread pipelines ([\d.]+) ms')), 1),
            'archive_hits': int(sum(hits)), 'archive_misses': int(sum(misses)),
            'archive_hit_rate': round(sum(hits) / (sum(hits) + sum(misses)), 4) if hits or misses else None,
            'logged_waits_over_20ms': len(waits), 'logged_wait_max_ms': max(waits, default=0)}


def audit(seed, user, log=None):
    a, al, ad = rows(seed); b, bl, bd = rows(user)
    result = {'seed_rows': al, 'seed_unique': len(a), 'seed_duplicates': ad,
              'user_rows': bl, 'user_unique': len(b), 'user_duplicates': bd,
              'user_already_seeded': len(a & b), 'user_new': len(b - a),
              'prewarm_unique': len(a | b)}
    for kind in 'SRC': result[f'prewarm_{kind}'] = sum(1 for row in a | b if row[0] == kind)
    if log: result['runtime'] = log_stats(log)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('seed'); ap.add_argument('user'); ap.add_argument('--log')
    a = ap.parse_args(argv)
    try: print(json.dumps(audit(a.seed, a.user, a.log), indent=2, sort_keys=True))
    except (OSError, ValueError) as e: ap.exit(1, f'[RED] {e}\n')


if __name__ == '__main__': main()
