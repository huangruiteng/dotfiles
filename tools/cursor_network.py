#!/usr/bin/env python3
"""Opt-in Cursor/local-proxy settings and macOS bypass rules; preview by default."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
import uuid

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / 'profiles/personal-mac/cursor-network.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def no_symlinks(path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('Network configuration paths must not contain symlinks')


def load_profile(path, proxy_url=None):
    data = json.loads(path.read_text())
    if data.get('version') != 1 or data.get('veee_mode') != 'global':
        raise ValueError('Expected version 1 profile with Veee global mode')
    settings = data['cursor_settings']
    if settings != {'cursor.general.disableHttp2': True, 'http.proxySupport': 'override',
                    'http.proxyStrictSSL': True}:
        raise ValueError('Profile must use HTTP/1.1, proxy override and TLS validation')
    address = proxy_url or data['proxy_url']
    try:
        url = urlsplit(address)
        port = url.port
    except ValueError:
        raise ValueError('Invalid local proxy URL; do not pass credentials or subscriptions') from None
    if (url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost', '::1')
            or url.username or url.password or not port
            or url.path not in ('', '/') or url.query or url.fragment):
        raise ValueError('Proxy must be a credential-free local HTTP listener with an explicit port')
    domains = data['bypass_domains']
    if not isinstance(domains, list) or not domains or any(
            not isinstance(d, str) or not d or any(c.isspace() or c == '\x00' for c in d)
            for d in domains):
        raise ValueError('Bypass domains must be nonempty strings without whitespace or NUL')
    return {'settings': {**settings, 'http.proxy': address},
            'domains': list(dict.fromkeys(domains))}


def read_cursor(path):
    no_symlinks(path)
    raw = path.read_bytes() if path.exists() else None
    try:
        settings = json.loads(raw) if raw is not None else {}
    except ValueError:
        raise ValueError('Cursor settings must be plain JSON; preserve JSONC comments and merge manually') from None
    if not isinstance(settings, dict):
        raise ValueError('Cursor settings must be a JSON object')
    return raw, settings


def read_bypass(service):
    result = subprocess.run(['networksetup', '-getproxybypassdomains', service],
                            capture_output=True, text=True, check=True)
    if 'Error:' in result.stdout or 'not a recognized network service' in result.stdout:
        raise ValueError('Unknown network service; check networksetup -listallnetworkservices')
    if 'There aren\'t any bypass domains set' in result.stdout:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def set_bypass(service, domains):
    subprocess.run(['networksetup', '-setproxybypassdomains', service, *(domains or ['Empty'])],
                   capture_output=True, text=True, check=True)


def write_atomic(path, data, mode=0o600):
    no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        temporary = Path(f.name)
        try:
            os.fchmod(f.fileno(), mode)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def save_receipt(path, record):
    write_atomic(path, (json.dumps(record, indent=2) + '\n').encode())


def configure(home, profile, service, apply=False):
    cursor = home / 'Library/Application Support/Cursor/User/settings.json'
    before, current = read_cursor(cursor)
    domains = read_bypass(service)
    after = dict(current, **profile['settings'])
    desired_domains = list(dict.fromkeys(domains + profile['domains']))
    cursor_changed = after != current
    bypass_changed = domains != desired_domains
    plan = {'cursor_keys_to_update': [k for k, v in profile['settings'].items() if current.get(k) != v],
            'proxy_url': profile['settings']['http.proxy'], 'network_service': service,
            'bypass_domains_to_add': [d for d in desired_domains if d not in domains],
            'veee_mode_requirement': 'global; verify in the App, not changed by this command'}
    if not apply or not (cursor_changed or bypass_changed):
        return {'applied': False, 'already_configured': not (cursor_changed or bypass_changed), **plan}
    directory = home / '.local/state/dotfiles/network' / uuid.uuid4().hex
    no_symlinks(directory)
    directory.mkdir(parents=True, mode=0o700)
    receipt = directory / 'receipt.json'
    encoded = (json.dumps(after, ensure_ascii=False, indent=4) + '\n').encode()
    record = {'version': 1, 'status': 'applying', 'home': str(home), 'service': service,
              'cursor_changed': cursor_changed, 'cursor_before_exists': before is not None,
              'cursor_before_sha256': digest(before) if before is not None else None,
              'cursor_after_sha256': digest(encoded), 'bypass_before': domains,
              'bypass_after': desired_domains, 'bypass_changed': bypass_changed}
    if before is not None:
        write_atomic(directory / 'cursor-settings.prior.json', before)
    save_receipt(receipt, record)
    try:
        if read_cursor(cursor)[0] != before or read_bypass(service) != domains:
            raise ValueError('Configuration changed after preview; no settings were written')
        if cursor_changed:
            mode = cursor.stat().st_mode & 0o777 if cursor.exists() else 0o600
            write_atomic(cursor, encoded, mode)
        if bypass_changed:
            set_bypass(service, desired_domains)
        if read_cursor(cursor)[1] != after or read_bypass(service) != desired_domains:
            raise ValueError('Configuration readback did not match')
    except (OSError, ValueError, subprocess.SubprocessError):
        # Both expected before/after states remain in the receipt for partial recovery.
        raise ValueError(f'Apply incomplete; inspect and preview rollback with --rollback {receipt}') from None
    record['status'] = 'applied'
    save_receipt(receipt, record)
    return {'applied': True, 'receipt': str(receipt), 'readback_verified': True, **plan}


def rollback(home, receipt, apply=False):
    state = home / '.local/state/dotfiles/network'
    receipt = receipt.absolute()
    if not receipt.is_relative_to(state) or receipt.name != 'receipt.json':
        raise ValueError('Receipt must belong to this home\'s dotfiles network state')
    no_symlinks(receipt)
    record = json.loads(receipt.read_text())
    if record.get('version') != 1 or record.get('home') != str(home):
        raise ValueError('Receipt home/version mismatch')
    cursor = home / 'Library/Application Support/Cursor/User/settings.json'
    current, _ = read_cursor(cursor)
    current_hash = digest(current) if current is not None else None
    expected = (record['cursor_before_sha256'], record['cursor_after_sha256'])
    domains = read_bypass(record['service'])
    if ((record['cursor_changed'] and current_hash not in expected)
            or domains not in (record['bypass_before'], record['bypass_after'])):
        raise ValueError('Configuration changed since apply; rollback refuses to overwrite later edits')
    prior = receipt.parent / 'cursor-settings.prior.json'
    no_symlinks(prior)
    before = prior.read_bytes() if record['cursor_before_exists'] else None
    if (digest(before) if before is not None else None) != record['cursor_before_sha256']:
        raise ValueError('Cursor backup checksum mismatch')
    if not apply:
        return {'rolled_back': False, 'preview': True, 'network_service': record['service']}
    if record['cursor_changed'] and current_hash != record['cursor_before_sha256']:
        if before is None:
            cursor.unlink()
        else:
            write_atomic(cursor, before, cursor.stat().st_mode & 0o777)
    if domains != record['bypass_before']:
        set_bypass(record['service'], record['bypass_before'])
    if read_cursor(cursor)[0] != before and record['cursor_changed']:
        raise ValueError('Cursor rollback readback did not match')
    if read_bypass(record['service']) != record['bypass_before']:
        raise ValueError('Bypass rollback readback did not match')
    record['status'] = 'rolled-back'
    save_receipt(receipt, record)
    return {'rolled_back': True, 'readback_verified': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, default=DEFAULT_PROFILE)
    parser.add_argument('--proxy-url', help='override the local HTTP listener, never a subscription or credential')
    parser.add_argument('--network-service', default='Wi-Fi')
    parser.add_argument('--apply', action='store_true', help='write only after preview; default is read-only')
    parser.add_argument('--check', action='store_true', help='read settings and probe the local proxy listener')
    parser.add_argument('--rollback', type=Path, help='preview or apply rollback using a local receipt')
    args = parser.parse_args()
    try:
        if sys.platform != 'darwin':
            raise ValueError('This profile requires macOS networksetup')
        if args.check and (args.apply or args.rollback):
            raise ValueError('--check is read-only; do not combine with --apply or --rollback')
        home = Path.home().resolve()
        if args.rollback:
            result = rollback(home, args.rollback.expanduser(), args.apply)
        else:
            profile = load_profile(args.profile, args.proxy_url)
            result = configure(home, profile, args.network_service, args.apply)
            if args.check:
                url = urlsplit(profile['settings']['http.proxy'])
                try:
                    with socket.create_connection((url.hostname, url.port), timeout=2):
                        result['proxy_listener_reachable'] = True
                except OSError:
                    result['proxy_listener_reachable'] = False
                result['ok'] = result['already_configured'] and result['proxy_listener_reachable']
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(args.check and not result['ok'])
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        # Do not dump settings or command output; either may contain unrelated private values.
        exc = sys.exc_info()[1]
        message = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, json.JSONDecodeError) else 'Could not read/apply network configuration; inspect the local files and service'
        print(json.dumps({'error': message}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
