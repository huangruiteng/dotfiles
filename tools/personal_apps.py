#!/usr/bin/env python3
"""Portable macOS App routes. No account/session migration or bundle patching."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ROLES = ('gpt', 'ds', 'loopx', 'ego', 'typora')
APP_NAMES = {'gpt': ('ChatGPT.app', 'Codex.app'), 'ds': ('ChatGPT.app', 'Codex.app'),
             'loopx': ('LoopX.app',), 'ego': ('ego lite.app',), 'typora': ('Typora.app',)}


def managed_path(raw, home):
    path = Path(str(raw).replace('~/', str(home) + '/', 1)).absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('App state paths must not contain symlinks')
    return path


def overlaps(a, b):
    return a == b or a in b.parents or b in a.parents


def settings(home):
    path = managed_path(home / '.config/personal/apps.json', home)
    source = path if path.exists() else ROOT / 'profiles/personal-mac/apps.example.json'
    raw = json.loads(source.read_text())
    if raw.get('version') != 1 or set(raw['apps']) != set(ROLES):
        raise ValueError('Expected version 1 App settings with exactly five roles')
    result = {}
    state_paths = []
    for role in ROLES:
        item = raw['apps'][role]
        if set(item) - {'app', 'home', 'frontend'}:
            raise ValueError('App settings contain an unsupported field')
        result[role] = {'app': item.get('app', '')}
        if role in ('gpt', 'ds'):
            for key in ('home', 'frontend'):
                p = managed_path(item[key], home)
                if not p.is_relative_to(home) or p == home:
                    raise ValueError('Codex state must be below the current user home')
                if any(overlaps(p, other) for other in state_paths):
                    raise ValueError('Codex homes and frontends must be separate, non-nested directories')
                state_paths.append(p)
                result[role][key] = p
    return result


def route(home, role, account=None):
    spec = dict(settings(home)[role])
    if account:
        if role != 'gpt' or not re.fullmatch(r'[a-z][a-z0-9-]{0,23}', account):
            raise ValueError('Account labels are GPT-only: lowercase letters, digits and hyphens')
        # Each optional account owns a fresh home; credentials are never copied.
        spec['home'] = managed_path(str(spec['home']) + '-account-' + account, home)
        spec['frontend'] = managed_path(str(spec['frontend']) + '-account-' + account, home)
        others = settings(home)
        for other in others.values():
            for key in ('home', 'frontend'):
                if key in other and any(overlaps(spec[k], other[key]) for k in ('home', 'frontend')):
                    raise ValueError('Account state overlaps another App route')
        if overlaps(spec['home'], spec['frontend']):
            raise ValueError('Account home overlaps its frontend')
    return spec


def app_bundle(spec, role, home):
    if spec['app']:
        path = managed_path(spec['app'], home)
        if path.is_dir() and path.suffix == '.app':
            return path
        raise ValueError('Configured App bundle is missing')
    for root in (Path('/Applications'), home / 'Applications'):
        for name in APP_NAMES[role]:
            if (root / name).is_dir():
                return root / name
    raise ValueError(f'{role} App missing; see profiles/personal-mac/APP_WORKFLOW.md')


def executable(bundle):
    info = plistlib.loads((bundle / 'Contents/Info.plist').read_bytes())
    name = info.get('CFBundleExecutable', '')
    if not name or '/' in name or name in ('.', '..'):
        raise ValueError('Invalid App executable metadata')
    path = bundle / 'Contents/MacOS' / name
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError('App executable is missing or not executable')
    return path


def clean_env(spec):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('CODEX_', 'OPENAI_', 'DEEPSEEK_', 'ELECTRON_', 'DYLD_'))
           and k not in ('NODE_OPTIONS', 'DISABLE_AUTO_UPDATE')}
    env['CODEX_HOME'] = str(spec['home'])
    return env


def owners(exe, frontend, ps_text):
    """Exact frontend ownership, including a Finder root identified by its child."""
    rows = {}
    for line in ps_text.splitlines():
        fields = line.strip().split(maxsplit=2)
        if len(fields) == 3 and fields[0].isdigit() and fields[1].isdigit():
            rows[int(fields[0])] = (int(fields[1]), fields[2])
    marker = re.compile(re.escape('--user-data-dir=' + str(frontend)) + r'(?=$|\s--|\s*$)')
    roots = {pid for pid, (_, cmd) in rows.items()
             if re.match(r'^/.*?/Contents/MacOS/\S+(?=\s|$)', cmd) and ' --type=' not in cmd}
    found = set()
    for pid, (_, cmd) in rows.items():
        if not marker.search(cmd):
            continue
        current, seen = pid, set()
        while current in rows and current not in seen:
            if current in roots:
                command = rows[current][1]
                if not (command == str(exe) or command.startswith(str(exe) + ' ')):
                    raise ValueError('Frontend is owned by a different App executable')
                found.add(current)
                break
            seen.add(current)
            current = rows[current][0]
        # A frontend owned by a different App build must not launch a second writer.
        if current not in roots:
            raise ValueError('Frontend owner could not be identified; inspect before opening')
    if len(found) > 1:
        raise ValueError('Multiple App processes own this frontend; inspect before opening')
    return next(iter(found), None)


FOCUS = '''ObjC.import("AppKit");
function run(argv) {
  var app = $.NSRunningApplication.runningApplicationWithProcessIdentifier(Number(argv[0]));
  if (!app || app.isTerminated) throw Error("App terminated");
  var target = $.NSAppleEventDescriptor.descriptorWithProcessIdentifier(Number(argv[0]));
  var event = $.NSAppleEventDescriptor.appleEventWithEventClassEventIDTargetDescriptorReturnIDTransactionID(
    0x61657674, 0x72617070, target, -1, 0);
  var error = Ref(); event.sendEventWithOptionsTimeoutError(1, 5, error);
  if (ObjC.unwrap(error[0]) || !app.activateWithOptions(3)) throw Error("Could not focus App");
}'''


def check_provider(spec, role):
    try:
        import tomllib
    except ImportError:
        raise ValueError('App commands require Python 3.11+; install the profile Python runtime') from None
    config = managed_path(spec['home'] / 'config.toml', Path.home())
    if not config.is_file():
        raise ValueError('Route is not initialized; run personal-apps init (preview), then --apply')
    # Never emit config values: DS config may contain its locally entered key.
    try:
        cfg = tomllib.loads(config.read_text())
    except tomllib.TOMLDecodeError:
        raise ValueError('Invalid local Codex TOML; repair it locally without printing secrets') from None
    if role == 'gpt':
        if (cfg.get('model_provider', 'openai') != 'openai' or cfg.get('model_catalog_json')
                or cfg.get('model_providers')):
            raise ValueError('GPT route requires the native OpenAI provider and catalog')
    else:
        from urllib.parse import urlsplit
        p = (cfg.get('model_providers') or {}).get('deepseek', {})
        url = urlsplit(p.get('base_url', ''))
        key = p.get('experimental_bearer_token', '')
        if (cfg.get('model_provider') != 'deepseek' or p.get('wire_api') != 'responses'
                or url.scheme != 'https' or url.hostname != 'api.deepseek.com'
                or url.username or url.password):
            raise ValueError('DS route needs the official DeepSeek Responses configuration')
        if not key or key == 'REPLACE_LOCALLY':
            raise ValueError('Enter the DS key locally in its private config; never pass it as a command argument')
        if config.stat().st_mode & 0o077:
            raise ValueError('DS config holds a key; restrict it to mode 600 before use')
        catalog = cfg.get('model_catalog_json')
        catalog_path = managed_path(catalog, Path.home()) if catalog else None
        if not catalog_path or not catalog_path.is_relative_to(spec['home']) or not catalog_path.is_file():
            raise ValueError('Install the current public DS model catalog in the DS home')
        try:
            models = json.loads(catalog_path.read_text()).get('models', [])
            available = [item.get('slug') for item in models if isinstance(item, dict)]
        except (ValueError, AttributeError, TypeError):
            raise ValueError('Invalid DS model catalog; validate its public JSON locally') from None
        if cfg.get('model') not in available:
            raise ValueError('DS model is absent from the local catalog; refresh the public metadata')


def prepare(home, role=None, account=None, apply=False):
    cfg = home / '.config/personal/apps.json'
    files = []
    if not cfg.exists():
        files.append((cfg, (ROOT / 'profiles/personal-mac/apps.example.json').read_text()))
    for name in ((role,) if role else ('gpt', 'ds')):
        spec = route(home, name, account)
        path = spec['home'] / 'config.toml'
        managed_path(path, home)
        if path.exists():
            continue  # Existing settings/auth/state are never overwritten.
        if name == 'gpt':
            content = '# Fresh native profile. Choose the model in the App.\nmodel_provider = "openai"\n'
        else:
            content = (ROOT / 'profiles/personal-mac/codex-ds.example.toml').read_text()
            content = content.replace('"@CATALOG@"', json.dumps(str(spec['home'] / 'models.json')))
        files.append((path, content))
    for path, _ in files:
        managed_path(path, home)
    if apply:
        for path, content in files:
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with open(path, 'x', opener=lambda p, flags: os.open(p, flags, 0o600)) as f:
                f.write(content)
    return {'applied': apply, 'create': [str(p) for p, _ in files], 'existing_preserved': True}


def shortcuts(home, apply=False):
    """Fresh Finder/Dock entry points, without modifying the vendor App bundle."""
    entry = home / '.local/bin/personal-apps'
    if not entry.is_file():
        raise ValueError('Install the bootstrap command link before creating shortcuts')
    targets = [(role, managed_path(home / 'Applications' / f'Codex {label} Personal.app', home))
               for role, label in (('gpt', 'GPT'), ('ds', 'DS'))]
    if any(p.exists() for _, p in targets):
        raise ValueError('A shortcut already exists; preserve it and inspect before replacing')
    if apply:
        import shlex
        for role, target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            shell_command = shlex.join([str(entry), 'open', role])
            # JSON quoting gives the required AppleScript string escaping here.
            script = 'do shell script ' + json.dumps(shell_command, ensure_ascii=False) + '\n'
            subprocess.run(['/usr/bin/osacompile', '-o', str(target), '-'],
                           input=script, text=True, check=True, capture_output=True)
    return {'applied': apply, 'create': [str(p) for _, p in targets]}


def running(exe, spec):
    ps = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,command='],
                        capture_output=True, text=True, check=True).stdout
    return owners(exe, spec['frontend'], ps)


def open_app(home, role, files, account=None, dry_run=False):
    spec = route(home, role, account)
    bundle = app_bundle(spec, role, home)
    if role not in ('gpt', 'ds'):
        if files and role != 'typora':
            raise ValueError('Only Typora accepts file arguments')
        paths = [str(Path(p).expanduser().resolve(strict=True)) for p in files]
        cmd = ['/usr/bin/open', '-a', str(bundle), *paths]
        if not dry_run:
            subprocess.run(cmd, check=True)
        return {'action': 'preview' if dry_run else 'open-requested', 'role': role, 'command': cmd}
    if files:
        raise ValueError('Codex routes accept no workspace argument yet; select the project inside the App')
    exe = executable(bundle)
    check_provider(spec, role)
    pid = running(exe, spec)
    result = {'action': 'focus' if pid else 'launch', 'role': role,
              'home': str(spec['home']), 'frontend': str(spec['frontend']), 'pid': pid}
    if dry_run:
        return dict(result, preview=True)
    lock_dir = managed_path(home / '.local/state/personal-apps', home)
    lock_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = managed_path(lock_dir / 'launch.lock', home)
    with open(lock_path, 'a', opener=lambda p, flags: os.open(p, flags, 0o600)) as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pid = running(exe, spec)
        if pid:
            subprocess.run(['/usr/bin/osascript', '-l', 'JavaScript', '-', str(pid)],
                           input=FOCUS, text=True, check=True, capture_output=True)
            return dict(result, action='focused', pid=pid)
        subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(bundle)],
                       check=True, capture_output=True)
        spec['frontend'].mkdir(mode=0o700, parents=True, exist_ok=True)
        env = clean_env(spec)
        env['CODEX_ELECTRON_USER_DATA_PATH'] = str(spec['frontend'])
        child = subprocess.Popen([str(exe), '--user-data-dir=' + str(spec['frontend'])],
                                 env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True)
        # Hold the lock until the child owns its frontend, preventing a double-click race.
        import time
        for _ in range(50):
            if child.poll() is not None:
                raise ValueError('App exited during startup; inspect the App locally')
            if running(exe, spec) == child.pid:
                return dict(result, action='launch-requested', pid=child.pid)
            time.sleep(0.1)
        raise ValueError('App ownership was not confirmed within five seconds; inspect before retrying')


def cli(home, role, args, account=None):
    spec = route(home, role, account)
    check_provider(spec, role)
    binary = shutil.which('codex')
    if not binary:
        raise ValueError('Install the official Codex CLI first')
    os.execvpe(binary, [binary, *args], clean_env(spec))


def status(home):
    report = []
    for role in ROLES:
        spec = route(home, role)
        row = {'role': role}
        try:
            bundle = app_bundle(spec, role, home)
            row['app'] = str(bundle)
            row['installed'] = True
            if role in ('gpt', 'ds'):
                row.update(home=str(spec['home']), frontend=str(spec['frontend']))
                row['pid'] = running(executable(bundle), spec)
                try:
                    check_provider(spec, role)
                    row['config_ready'] = True
                except ValueError as exc:
                    row.update(config_ready=False, next_action=str(exc))
        except (OSError, ValueError) as exc:
            row.update(installed=False, next_action=str(exc))
        report.append(row)
    return {'apps': report, 'note': 'Installed/configured is not proof of a successful GUI request'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('status', help='Read-only App and route status; never prints auth/config contents')
    shortcut = sub.add_parser('shortcuts', help='Preview fresh Finder/Dock launchers; no bundle cloning')
    shortcut.add_argument('--apply', action='store_true')
    init = sub.add_parser('init', help='Preview fresh local settings; preserve existing files')
    init.add_argument('--apply', action='store_true')
    init.add_argument('--account', help='Optional GPT account label; gets its own fresh state')
    launch = sub.add_parser('open', help='Focus one running Codex route or request an App launch')
    launch.add_argument('role', choices=ROLES)
    launch.add_argument('--dry-run', action='store_true')
    launch.add_argument('--account')
    launch.add_argument('files', nargs='*')
    native = sub.add_parser('cli', help='Invoke the installed native CLI with one isolated home')
    native.add_argument('role', choices=('gpt', 'ds'))
    native.add_argument('--account')
    native.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        home = Path.home().resolve()
        if args.action == 'init':
            result = prepare(home, 'gpt' if args.account else None, args.account, args.apply)
        elif args.action == 'shortcuts':
            if sys.platform != 'darwin':
                raise ValueError('App shortcuts support macOS only')
            result = shortcuts(home, args.apply)
        elif args.action == 'open':
            if sys.platform != 'darwin':
                raise ValueError('App launching supports macOS only')
            result = open_app(home, args.role, args.files, args.account, args.dry_run)
        elif args.action == 'cli':
            tail = args.args[1:] if args.args[:1] == ['--'] else args.args
            cli(home, args.role, tail, args.account)
            return 0
        else:
            result = status(home)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        # subprocess exceptions can contain captured output or argv; never render them.
        message = str(exc) if isinstance(exc, ValueError) else 'App command failed; inspect local installation and settings'
        print(json.dumps({'error': message}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
