#!/usr/bin/env python3
"""Verify Lark user auth server-side without printing identity or credentials.

Uses the official lark-cli auth status contract verified with v1.0.97.
Does not initiate login, request more scopes or modify remote resources.
"""
import json
import os
import subprocess


def summarize(data, exit_code):
    user = data.get('identities', {}).get('user', {})
    if not isinstance(user, dict):
        user = {}
    checks = {'command_succeeded': exit_code == 0,
              'user_identity': data.get('identity') == 'user',
              'user_available': user.get('available') is True,
              'user_ready': user.get('status') == 'ready',
              'token_valid': user.get('tokenStatus') == 'valid',
              'server_verified': data.get('verified') is True and user.get('verified') is True}
    return {'ok': all(checks.values()), **checks}


def main():
    env = dict(os.environ, LARKSUITE_CLI_NO_UPDATE_NOTIFIER='1', LARKSUITE_CLI_NO_SKILLS_NOTIFIER='1')
    try:
        result = subprocess.run(['lark-cli', 'auth', 'status', '--json', '--verify'],
                                capture_output=True, text=True, timeout=30, env=env)
        data = json.loads(result.stdout) if result.returncode == 0 else {}
        if not isinstance(data, dict):
            raise ValueError('Unexpected status shape')
        summary = summarize(data, result.returncode)
    except (OSError, ValueError, TypeError, AttributeError, subprocess.SubprocessError):
        summary = {'ok': False, 'error': 'Could not verify user auth; inspect login locally'}
    print(json.dumps(summary))
    return int(not summary['ok'])


if __name__ == '__main__':
    raise SystemExit(main())
