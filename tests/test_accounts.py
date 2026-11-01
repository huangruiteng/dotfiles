"""Synthetic login caches only; never load a developer's real accounts."""
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import personal_accounts as accounts
from loopx_codex_provider_routing import native_account_store as store
from loopx_codex_provider_routing import native_app as native_app
import personal_apps as apps

def fake_login(subject, rotation='initial'):
    claims = base64.urlsafe_b64encode(json.dumps({'sub': 'synthetic-' + subject}).encode()).decode().rstrip('=')
    return accounts.encoded({'auth_mode': 'chatgpt', 'tokens': {
        'id_token': 'synthetic.' + claims + '.not-a-signature',
        'access_token': 'synthetic-access-' + rotation,
        'refresh_token': 'synthetic-refresh-' + rotation, 'account_id': 'synthetic-personal'}})

class AccountAdapterTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name).resolve() / 'home with spaces'
        self.home.mkdir()
        apps.prepare(self.home, apply=True)
        self.spec = apps.route(self.home, 'gpt')
        self.idle = Mock()
        self.manager = accounts.Accounts(self.home, self.spec, self.idle,
                                         lambda: '/synthetic/bin/codex', apps.clean_env)
        self.a, self.b = fake_login('a'), fake_login('b')
        accounts.atomic(self.manager.auth, self.a)

    def current(self):
        return self.manager.enroll('a', current=True)

    def enroll_b(self):
        def login(cmd, env):
            self.assertEqual(cmd, ['/synthetic/bin/codex', 'login'])
            stage = Path(env['CODEX_HOME'])
            self.assertNotEqual(stage, self.spec['home'])
            self.assertEqual((stage / 'config.toml').read_text(),
                             'cli_auth_credentials_store="file"\nforced_login_method="chatgpt"\n')
            accounts.atomic(stage / 'auth.json', self.b)
            return subprocess.CompletedProcess(cmd, 0)
        with patch.object(store.subprocess, 'run', side_effect=login):
            return self.manager.enroll('b')

    def ready(self):
        self.current()
        self.enroll_b()

    def test_routed_cli_holds_inheritable_credential_lease_during_exec(self):
        def execute(*args):
            with self.assertRaises(BlockingIOError):
                with accounts.credential_lock(self.home):
                    pass
        with patch.object(apps.shutil, 'which', return_value='/synthetic/bin/codex'), patch.object(apps.os, 'execvpe', side_effect=execute), patch.object(apps.os, 'set_inheritable', wraps=apps.os.set_inheritable) as inherit:
            apps.cli(self.home, 'gpt', ['--version'])
        self.assertTrue(inherit.call_args.args[1])

    def test_real_exec_retains_shared_lease_until_cli_exits(self):
        binary = self.home / 'bin/codex'
        binary.parent.mkdir()
        binary.write_text('#!/bin/sh\nprintf "synthetic-ready\\n"\nread answer\n')
        binary.chmod(0o755)
        env = dict(os.environ, PATH=str(binary.parent) + os.pathsep + os.environ['PATH'])
        code = ('import sys; from pathlib import Path; '
                'sys.path.insert(0, sys.argv[1]); import personal_apps; '
                'personal_apps.cli(Path(sys.argv[2]), "gpt", ["exec"])')
        with subprocess.Popen([sys.executable, '-c', code, str(ROOT / 'tools'), str(self.home)],
                              env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True) as child:
            self.assertEqual(child.stdout.readline().strip(), 'synthetic-ready')
            with self.assertRaises(BlockingIOError):
                with accounts.credential_lock(self.home):
                    pass
            child.communicate('done\n', timeout=5)
            self.assertEqual(child.returncode, 0)
        with accounts.credential_lock(self.home):
            pass

    def test_cli_parser_local_switch_and_launch_failure_reports_commit(self):
        with patch.object(apps, 'account_command', return_value={'slot':'a'} ) as call, patch.object(sys, 'argv', ['personal-apps','accounts','switch','a','--local','--no-launch']), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(apps.main(), 0)
            self.assertTrue(call.call_args.args[1].no_launch)
        args = type('Args', (), {'account_action':'switch','slot':'b','dry_run':False,'no_launch':False})()
        with patch.object(apps, 'account_idle'), patch.object(accounts.Accounts, 'switch', return_value={'slot':'b','history_untouched':True}), patch.object(apps, 'open_app', side_effect=ValueError('synthetic launch failure')):
            result = apps.account_command(self.home, args)
        self.assertTrue(result['launch_failed'])
        self.assertEqual(result['slot'], 'b')

    def test_adapter_reuses_the_loopx_owner_and_existing_vault(self):
        self.ready()
        canonical = store.Accounts(self.home, native_app.route(self.home), self.idle, None, None)
        self.assertIs(accounts.identity, store.identity)
        self.assertIs(accounts.Accounts.switch, store.Accounts.switch)
        self.assertEqual(canonical.root, self.manager.root)
        self.assertEqual(canonical.status()['active_slot'], 'a')
        with accounts.credential_lock(self.home, shared=True):
            with self.assertRaises(BlockingIOError):
                canonical.switch('b')
        canonical.switch('b')
        self.assertEqual(self.manager.status()['active_slot'], 'b')
        self.manager.recover(rollback=True)
        self.assertEqual(canonical.auth.read_bytes(), self.a)

    def test_api_and_native_return_are_the_same_transaction_owner(self):
        self.current()
        canonical = store.Accounts(self.home, native_app.route(self.home), self.idle, None, None)
        self.manager.enroll_api('api', api_key='sk-loopx-relay-synthetic-adapter-token', base_url='http://127.0.0.1:32100/v1')
        canonical.switch('api')
        apps.check_provider(self.spec, 'gpt')
        self.assertEqual(self.manager.status()['slot_kinds']['api'], 'api')
        self.manager.switch('a')
        self.assertEqual(canonical.auth.read_bytes(), self.a)
        self.assertNotIn('openai_base_url', self.manager.config.read_text())

if __name__ == '__main__':
    unittest.main()
