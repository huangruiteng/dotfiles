#!/usr/bin/env python3
"""Check common local Markdown link/image destinations, independently of a reader UI."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


def destinations(text):
    # This smoke checker intentionally supports inline links and reference links,
    # not the entire CommonMark grammar. Code examples must not become false links.
    fenced = False
    for line in text.splitlines():
        if re.match(r'^\s*(`{3,}|~{3,})', line):
            fenced = not fenced
            continue
        if fenced or line.startswith(('    ', '\t')):
            continue
        line = re.sub(r'`[^`]*`', '', line)
        for match in re.finditer(r'!?\[[^\]\n]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)', line):
            yield match.group(1) or match.group(2)
        match = re.match(r'^\s{0,3}\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))', line)
        if match:
            yield match.group(1) or match.group(2)


def check_markdown(file):
    file = file.expanduser().resolve(strict=True)
    checked, missing, unsupported = [], [], []
    for target in destinations(file.read_text(encoding='utf-8')):
        uri = urlsplit(target)
        if uri.scheme or uri.netloc or not uri.path:
            continue
        if '\\' in uri.path or '\x00' in unquote(uri.path):
            unsupported.append(target)
            continue
        path = file.parent / unquote(uri.path)
        checked.append(target)
        if not path.exists():
            missing.append(target)
    return {'ok': not missing and not unsupported, 'local_destinations': len(checked),
            'missing': missing, 'unsupported': unsupported,
            'ui_verified': False, 'note': 'File existence does not verify Cmd-click, rendering or anchor navigation'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path)
    a = p.parse_args()
    try:
        result = check_markdown(a.file)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(not result['ok'])
    except (OSError, ValueError):
        print(json.dumps({'ok': False, 'error': 'Could not inspect UTF-8 Markdown'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
