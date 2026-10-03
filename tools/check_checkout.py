#!/usr/bin/env python3
"""Verify a full local Git worktree without fetching, resetting or printing identity."""
import argparse
import json
import os
from pathlib import Path
import stat
import subprocess


def git(repo, *args):
    p = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, timeout=30)
    return p.returncode, p.stdout


def check_checkout(repo):
    repo = repo.expanduser().resolve(strict=True)
    if not (repo / '.git').exists():
        raise ValueError('Expected a Git checkout, not a reviewed file subset or exported archive')
    code, top = git(repo, 'rev-parse', '--show-toplevel')
    if code or Path(os.fsdecode(top).strip()).resolve() != repo:
        raise ValueError('Expected the repository root')
    code, records = git(repo, 'ls-files', '--stage', '-z')
    if code:
        raise ValueError('Could not inspect the Git index')
    entries = {}
    for record in records.split(b'\0'):
        if record:
            meta, name = record.split(b'\t', 1)
            entries[os.fsdecode(name)] = meta.split()[0]
    missing, wrong_type, broken_links, submodules = [], [], [], 0
    for name, mode in entries.items():
        if mode == b'160000':
            submodules += 1  # Optional legacy plugin submodules are not required.
            continue
        path = repo / name
        try:
            info = path.lstat()  # A tracked broken symlink is present, not a missing entry.
        except FileNotFoundError:
            missing.append(name)
            continue
        expected = stat.S_ISLNK(info.st_mode) if mode == b'120000' else stat.S_ISREG(info.st_mode)
        if not expected:
            wrong_type.append(name)
        elif mode == b'120000' and not path.exists():
            broken_links.append(name)
    _, value = git(repo, 'config', '--bool', '--get', 'core.sparseCheckout')
    sparse = value.strip() == b'true'
    return {'ok': bool(entries) and not missing and not wrong_type and not sparse,
            'tracked_entries': len(entries), 'optional_submodules': submodules,
            'missing': missing, 'wrong_type': wrong_type, 'sparse_checkout': sparse,
            'broken_tracked_symlinks': broken_links}


def require_checkout(repo):
    result = check_checkout(repo)
    if not result['ok']:
        raise ValueError('Incomplete checkout: missing=%d wrong_type=%d sparse=%s; preserve local changes and repair before linking' %
                         (len(result['missing']), len(result['wrong_type']), result['sparse_checkout']))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('repo', type=Path)
    a = p.parse_args()
    try:
        result = check_checkout(a.repo)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(not result['ok'])
    except (OSError, ValueError, subprocess.SubprocessError):
        print(json.dumps({'ok': False, 'error': 'Could not verify a full local Git checkout'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
