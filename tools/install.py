#!/usr/bin/env python3
"""Link reviewed shell/skill sources; preview by default, preserve conflicts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]


def no_link_parents(path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f'symlink in destination parent: {part}')


def skill_links(repo, dest):
    repo = repo.resolve(strict=True)
    manifest = json.loads((repo / 'note-system/skills/manifest.json').read_text())
    if manifest.get('version') != 1:
        raise ValueError('unsupported skill manifest version')
    links, seen = [], set()
    for item in manifest['skills']:
        name = item['name']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or name in seen:
            raise ValueError('invalid or duplicate skill name')
        seen.add(name)
        source = repo / '.codex/skills' / name
        if source.is_symlink() or not source.is_dir() or not source.resolve().is_relative_to(repo):
            raise ValueError(f'skill source must be a real directory: {name}')
        files = item['files']
        actual = set()
        for p in source.rglob('*'):
            if p.is_symlink():
                raise ValueError(f'symlink inside skill source: {name}')
            if p.is_file():
                actual.add(p.relative_to(source).as_posix())
        if actual != set(files) or 'SKILL.md' not in files:
            raise ValueError(f'skill file allowlist mismatch: {name}')
        for rel, expected in files.items():
            p = source / rel
            if p.resolve().is_relative_to(source.resolve()) is False:
                raise ValueError('skill path escapes source')
            if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                raise ValueError(f'skill content changed; review and refresh manifest: {name}/{rel}')
        links.append((source, dest / name))
    if not links:
        raise ValueError('empty skill manifest')
    return links


def same_link(dest, source):
    return dest.is_symlink() and dest.resolve() == source.resolve()


def install(links, home, apply=False, replace=False):
    changes = []
    for source, dest in links:
        if not source.exists():
            raise ValueError(f'missing source: {source}')
        no_link_parents(dest.parent)
        if same_link(dest, source):
            continue
        if os.path.lexists(dest) and not replace:
            raise ValueError(f'conflict (preserved): {dest}; review, then use --replace to back it up')
        changes.append((source, dest))
    plan = [{'source': str(s), 'link': str(d), 'backup_required': os.path.lexists(d)} for s, d in changes]
    if not apply or not changes:
        return {'applied': False, 'changes': plan}
    state = home / '.local/state/dotfiles'
    no_link_parents(state)
    backup_dir = state / uuid.uuid4().hex
    backup_dir.mkdir(parents=True, mode=0o700)
    receipt = backup_dir / 'receipt.json'
    record = {'version': 1, 'status': 'applying', 'links': []}
    receipt.write_text(json.dumps(record, indent=2) + '\n')
    try:
        for index, (source, dest) in enumerate(changes):
            dest.parent.mkdir(parents=True, exist_ok=True)
            no_link_parents(dest.parent)
            backup = backup_dir / str(index) if os.path.lexists(dest) else None
            row = {'source': str(source), 'link': str(dest), 'backup': str(backup) if backup else None}
            # Persist recovery intent before mutating a destination.
            record['links'].append(row)
            receipt.write_text(json.dumps(record, indent=2) + '\n')
            if backup:
                dest.rename(backup)
            dest.symlink_to(source, target_is_directory=source.is_dir())
        record['status'] = 'installed'
        receipt.write_text(json.dumps(record, indent=2) + '\n')
    except Exception:
        # Reverse only links still owned by this invocation; leave recoverable backups.
        for row in reversed(record['links']):
            dest, source = Path(row['link']), Path(row['source'])
            if same_link(dest, source):
                dest.unlink()
            if row['backup'] and os.path.lexists(row['backup']) and not os.path.lexists(dest):
                Path(row['backup']).rename(dest)
        record['status'] = 'failed'
        receipt.write_text(json.dumps(record, indent=2) + '\n')
        raise
    return {'applied': True, 'changes': plan, 'receipt': str(receipt)}


def rollback(receipt, apply=False):
    record = json.loads(receipt.read_text())
    if record.get('status') != 'installed':
        raise ValueError('receipt is not an installed transaction')
    for row in record['links']:
        dest = Path(row['link'])
        no_link_parents(dest.parent)
        if not same_link(dest, Path(row['source'])):
            raise ValueError(f'destination changed; rollback stopped: {dest}')
        if row['backup'] and not os.path.lexists(row['backup']):
            raise ValueError('missing rollback backup')
    if apply:
        for row in reversed(record['links']):
            dest = Path(row['link']); dest.unlink()
            if row['backup']:
                Path(row['backup']).rename(dest)
        record['status'] = 'rolled-back'
        receipt.write_text(json.dumps(record, indent=2) + '\n')
    return {'rolled_back': apply, 'count': len(record['links'])}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--skills-repo', type=Path, help='reviewed CS-Notes checkout; required unless --shell-only')
    p.add_argument('--skills-dir', type=Path, help='default: HOME/.agents/skills')
    p.add_argument('--home', type=Path, default=Path.home(), help='target home, useful for isolated validation')
    p.add_argument('--shell-only', action='store_true')
    p.add_argument('--skills-only', action='store_true')
    p.add_argument('--apply', action='store_true', help='apply the displayed plan; default is read-only')
    p.add_argument('--replace', action='store_true', help='back up conflicts; never overwrite without backup')
    p.add_argument('--no-preferences', action='store_true', help='skip tmux and the macOS iTerm dynamic profile')
    p.add_argument('--allow-export', action='store_true', help='explicitly allow reviewed non-Git exports; full checkout completeness cannot be verified')
    p.add_argument('--rollback', type=Path, help='preview or apply rollback from a local receipt')
    args = p.parse_args()
    try:
        if args.rollback:
            result = rollback(args.rollback, args.apply)
        else:
            if args.shell_only and args.skills_only:
                p.error('choose only one of --shell-only / --skills-only')
            home = args.home.expanduser().absolute()
            # Canonicalize only the home; reject redirected child directories.
            home = home.resolve()
            if not args.allow_export:
                from check_checkout import require_checkout
                require_checkout(ROOT)
                if not args.shell_only and args.skills_repo:
                    require_checkout(args.skills_repo)
            links = [] if args.skills_only else [(ROOT / 'zshrc', home / '.zshrc'), (ROOT / 'zprofile', home / '.zprofile'),
                                                (ROOT / 'tools/personal-apps', home / '.local/bin/personal-apps')]
            if not args.skills_only and not args.no_preferences:
                links.append((ROOT / 'tmux.conf', home / '.tmux.conf'))
                if sys.platform == 'darwin':
                    links.append((ROOT / 'profiles/personal-mac/iterm2.json',
                                  home / 'Library/Application Support/iTerm2/DynamicProfiles/dotfiles-personal.json'))
            if not args.shell_only:
                if not args.skills_repo:
                    p.error('--skills-repo is required; use --shell-only to install just the shell')
                dest = args.skills_dir.expanduser().absolute() if args.skills_dir else home / '.agents/skills'
                links += skill_links(args.skills_repo, dest)
            result = install(links, home, args.apply, args.replace)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
