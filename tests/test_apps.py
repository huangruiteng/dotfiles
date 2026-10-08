import importlib.util
import json
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('apps', ROOT / 'tools/personal_apps.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve() / 'home with spaces'
        self.home.mkdir()
        self.bundle = self.home / 'Applications/ChatGPT.app'
        self.exe = self.bundle / 'Contents/MacOS/ChatGPT'
        self.exe.parent.mkdir(parents=True)
        self.exe.write_text('#!/bin/sh\nexit 0\n')
        self.exe.chmod(0o755)
        (self.bundle / 'Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleExecutable': 'ChatGPT'}))

    def initialize(self):
        return m.prepare(self.home, apply=True)

    def ds_ready(self):
        self.initialize()
        spec = m.route(self.home, 'ds')
        config = spec['home'] / 'config.toml'
        config.write_text(config.read_text().replace('REPLACE_LOCALLY', 'unit-test-value'))
        (spec['home'] / 'models.json').write_text('{"models": [{"slug": "deepseek-flash"}]}')
        return spec

    def test_init_preview_has_no_side_effects(self):
        self.assertEqual(len(m.prepare(self.home)['create']), 3)
        self.assertFalse((self.home / '.config').exists())
        self.assertFalse((self.home / '.codex-gpt').exists())

    def test_init_preserves_existing_state_and_is_idempotent(self):
        gpt = self.home / '.codex-gpt'
        gpt.mkdir()
        (gpt / 'config.toml').write_text('model_provider="openai"\n')
        (gpt / 'auth.json').write_text('not-a-credential')
        self.initialize()
        self.assertEqual((gpt / 'auth.json').read_text(), 'not-a-credential')
        self.assertEqual((gpt / 'config.toml').read_text(), 'model_provider="openai"\n')
        self.assertEqual(m.prepare(self.home, apply=True)['create'], [])
        self.assertEqual((self.home / '.codex-ds/config.toml').stat().st_mode & 0o777, 0o600)

    def test_symlink_state_refused_before_any_write(self):
        (self.home / '.codex-ds').symlink_to(self.home / 'outside')
        with self.assertRaises(ValueError):
            self.initialize()
        self.assertFalse((self.home / '.config').exists())
        self.assertFalse((self.home / '.codex-gpt').exists())

    def test_overlapping_state_refused(self):
        self.initialize()
        path = self.home / '.config/personal/apps.json'
        data = json.loads(path.read_text())
        data['apps']['ds']['home'] = '~/.codex-gpt/child'
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            m.settings(self.home)

    def test_init_has_one_gpt_home_and_preserves_existing_login(self):
        self.initialize()
        gpt = m.route(self.home, 'gpt')
        (gpt['home'] / 'auth.json').write_text('private-test-cache')
        m.prepare(self.home, apply=True)
        self.assertEqual(m.route(self.home, 'gpt')['home'], gpt['home'])
        self.assertEqual((gpt['home'] / 'auth.json').read_text(), 'private-test-cache')
        self.assertEqual(list(self.home.glob('.codex-gpt-account-*')), [])

    def test_environment_removes_session_and_api_overrides(self):
        with patch.dict(os.environ, {'CODEX_HOME': '/old', 'CODEX_THREAD_ID': 'old',
                                     'CODEX_APP_TOOLS_PIPE_PATH': '/old/pipe',
                                     'OPENAI_API_KEY': 'private', 'DEEPSEEK_API_KEY': 'private',
                                     'NODE_OPTIONS': '--require=old', 'HTTPS_PROXY': 'http://localhost:1234'}):
            env = m.clean_env({'home': self.home / '.codex-gpt'}, self.home)
        self.assertEqual(env['CODEX_HOME'], str(self.home / '.codex-gpt'))
        for key in ('CODEX_THREAD_ID', 'CODEX_APP_TOOLS_PIPE_PATH', 'OPENAI_API_KEY', 'DEEPSEEK_API_KEY', 'NODE_OPTIONS'):
            self.assertNotIn(key, env)
        self.assertIn('HTTPS_PROXY', env)

    def test_finder_path_includes_user_tools_without_masking_active_environment(self):
        tools = self.home / '.local/bin'; tools.mkdir(parents=True)
        active = self.home / 'project-venv/bin'; active.mkdir(parents=True)
        with patch.dict(os.environ, {'PATH': str(active) + ':/usr/bin:/bin'}):
            env = m.clean_env({'home': self.home / 'nested/.codex-gpt'}, self.home)
        paths = env['PATH'].split(os.pathsep)
        self.assertEqual(paths[0], str(active))
        self.assertIn(str(tools), paths)
        self.assertEqual(len(paths), len(set(paths)))

    def test_exact_frontend_and_finder_child_ownership(self):
        frontend = self.home / 'Library/Application Support/Codex GPT'
        ps = (f'10 1 {self.exe}\n'
              f'11 10 {self.bundle}/Contents/Frameworks/Helper.app/Contents/MacOS/Helper --type=renderer --user-data-dir={frontend}\n'
              f'20 1 {self.exe} --user-data-dir={frontend} Extra\n')
        self.assertEqual(m.owners(self.exe, frontend, ps), 10)
        self.assertIsNone(m.owners(self.exe, Path(str(frontend) + ' Other'), ps))

    def test_foreign_frontend_owner_and_duplicate_are_refused(self):
        frontend = self.home / 'data'
        with self.assertRaises(ValueError):
            m.owners(self.exe, frontend, f'3 1 /other/ChatGPT.app/Contents/MacOS/ChatGPT\n4 3 /other/Helper.app/Contents/MacOS/Helper --type=renderer --user-data-dir={frontend}')
        with self.assertRaises(ValueError):
            m.owners(self.exe, frontend, f'3 1 {self.exe} --user-data-dir={frontend}\n4 1 {self.exe} --user-data-dir={frontend}')

    def test_open_preview_never_launches(self):
        self.initialize()
        with patch.object(m, 'running', return_value=None), patch.object(m.subprocess, 'Popen') as launch:
            result = m.open_app(self.home, 'gpt', [], dry_run=True)
        self.assertTrue(result['preview'])
        launch.assert_not_called()
        self.assertFalse((self.home / '.local/state').exists())

    def test_running_route_uses_pid_focus_not_open_bundle(self):
        self.initialize()
        with patch.object(m, 'running', return_value=42), patch.object(m.subprocess, 'run') as run, patch.object(m.subprocess, 'Popen') as spawn:
            result = m.open_app(self.home, 'gpt', [])
        self.assertEqual(result['action'], 'focused')
        self.assertEqual(run.call_args.args[0][-1], '42')
        self.assertIn('NSRunningApplication', run.call_args.kwargs['input'])
        spawn.assert_not_called()

    def test_new_launch_has_separate_state_and_no_secret_argv(self):
        self.initialize()
        with patch.object(m, 'running', side_effect=[None, None, 100]), patch.object(m.subprocess, 'run'), patch.object(m.subprocess, 'Popen') as spawn:
            spawn.return_value.pid = 100
            spawn.return_value.poll.return_value = None
            result = m.open_app(self.home, 'gpt', [])
        self.assertEqual(result['action'], 'launch-requested')
        argv = spawn.call_args.args[0]
        env = spawn.call_args.kwargs['env']
        self.assertEqual(len(argv), 2)
        self.assertEqual(argv[1], '--user-data-dir=' + env['CODEX_ELECTRON_USER_DATA_PATH'])
        self.assertTrue(env['CODEX_HOME'].endswith('.codex-gpt'))
        self.assertTrue(spawn.call_args.kwargs['start_new_session'])

    def test_ds_placeholder_catalog_and_permissions_gates(self):
        self.initialize()
        spec = m.route(self.home, 'ds')
        with self.assertRaisesRegex(ValueError, 'key locally'):
            m.check_provider(spec, 'ds')
        self.ds_ready()
        m.check_provider(spec, 'ds')
        path = spec['home'] / 'config.toml'
        path.chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'mode 600'):
            m.check_provider(spec, 'ds')
        path.chmod(0o600)
        (spec['home'] / 'models.json').unlink()
        with self.assertRaisesRegex(ValueError, 'model catalog'):
            m.check_provider(spec, 'ds')

    def test_gpt_rejects_custom_provider(self):
        self.initialize()
        spec = m.route(self.home, 'gpt')
        (spec['home'] / 'config.toml').write_text('model_provider="deepseek"\n')
        with self.assertRaises(ValueError):
            m.check_provider(spec, 'gpt')

    def test_gpt_allows_unused_provider_and_preserves_config(self):
        self.initialize()
        spec = m.route(self.home, 'gpt')
        path = spec['home'] / 'config.toml'
        provider = ('# Optional transport; explicitly selected by another client.\n'
                    '[model_providers.optional_http]\nname="Optional HTTP"\n'
                    'wire_api="responses"\nrequires_openai_auth=true\n'
                    'supports_websockets=false\n')
        for default in ('', 'model_provider="openai"\n'):
            with self.subTest(default=default):
                raw = ('model="gpt-example"\n' + default + provider).encode()
                path.write_bytes(raw)
                m.check_provider(spec, 'gpt')
                with patch.object(m, 'app_bundle', return_value=self.bundle), patch.object(m, 'running', return_value=None):
                    result = m.open_app(self.home, 'gpt', [], dry_run=True)
                self.assertEqual(result['role'], 'gpt')
                self.assertEqual(path.read_bytes(), raw)

    def test_gpt_rejects_native_provider_shadow_and_catalog_override(self):
        self.initialize()
        spec = m.route(self.home, 'gpt')
        for config in ('model_catalog_json="models.json"\n',
                       '[model_providers.openai]\n',
                       '[model_providers.openai]\nbase_url="https://example.invalid"\n'):
            with self.subTest(config=config):
                (spec['home'] / 'config.toml').write_text(config)
                with self.assertRaisesRegex(ValueError, 'native OpenAI'):
                    m.check_provider(spec, 'gpt')

    def test_ds_catalog_has_to_contain_selected_model(self):
        spec = self.ds_ready()
        (spec['home'] / 'models.json').write_text('{"models": []}')
        with self.assertRaisesRegex(ValueError, 'absent'):
            m.check_provider(spec, 'ds')

    def test_invalid_secret_toml_never_echoed(self):
        spec = self.ds_ready()
        (spec['home'] / 'config.toml').write_text('experimental_bearer_token="DO_NOT_PRINT" garbage')
        with self.assertRaises(ValueError) as error:
            m.check_provider(spec, 'ds')
        self.assertNotIn('DO_NOT_PRINT', str(error.exception))

    def test_typora_space_and_leading_dash_file(self):
        bundle = self.home / 'Applications/Typora.app'
        bundle.mkdir()
        note = self.home / '-note with spaces.md'
        note.write_text('# Example')
        with patch.object(m.subprocess, 'run') as run:
            result = m.open_app(self.home, 'typora', [str(note)], dry_run=True)
        run.assert_not_called()
        self.assertEqual(result['command'][-1], str(note))

    def test_cli_routes_home_and_passes_native_arguments(self):
        self.initialize()
        with patch.object(m.shutil, 'which', return_value='/usr/local/bin/codex'), patch.object(m.os, 'execvpe') as execute:
            m.cli(self.home, 'gpt', ['exec', '--', 'prompt with spaces'])
        self.assertEqual(execute.call_args.args[1][1:], ['exec', '--', 'prompt with spaces'])
        self.assertEqual(execute.call_args.args[2]['CODEX_HOME'], str(self.home / '.codex-gpt'))

    def test_cli_finds_existing_user_install_from_finder_path(self):
        self.initialize()
        binary = self.home / '.local/bin/codex'
        binary.parent.mkdir(parents=True)
        binary.write_text('#!/bin/sh\nexit 0\n'); binary.chmod(0o755)
        with patch.dict(os.environ, {'PATH': '/usr/bin:/bin'}), patch.object(m.os, 'execvpe') as execute:
            m.cli(self.home, 'gpt', ['--version'])
        self.assertEqual(execute.call_args.args[0], str(binary))

    def test_shortcuts_preview_and_existing_preserved(self):
        entry = self.home / '.local/bin/personal-apps'
        entry.parent.mkdir(parents=True)
        entry.symlink_to(ROOT / 'tools/personal-apps')
        with patch.object(m.subprocess, 'run') as compile_app:
            result = m.shortcuts(self.home)
        self.assertEqual(len(result['create']), 2)
        compile_app.assert_not_called()
        Path(result['create'][0]).mkdir()
        with self.assertRaises(ValueError):
            m.shortcuts(self.home, True)

    @unittest.skipUnless(m.sys.platform == 'darwin', 'macOS AppleScript compiler')
    def test_finder_shortcuts_compile_without_launching_vendor_app(self):
        entry = self.home / '.local/bin/personal-apps'
        entry.parent.mkdir(parents=True)
        entry.symlink_to(ROOT / 'tools/personal-apps')
        result = m.shortcuts(self.home, True)
        self.assertTrue(result['applied'])
        for target in result['create']:
            self.assertTrue((Path(target) / 'Contents/Info.plist').is_file())

    def test_noninteractive_zsh_dispatch_and_native_passthrough(self):
        command = f'''DOTFILES_ROOT={json.dumps(str(ROOT))}; source "$DOTFILES_ROOT/shell/apps.zsh"
_dotfiles_apps() {{ printf '<%s>\\n' "$@"; }}
codex ds app --dry-run
codex app switch a --local --no-launch
codex app enroll b
codex app accounts
codex ds exec 'two words'
loopx app
ego lite app
typora app 'note with spaces.md'
'''
        r = subprocess.run(['/bin/zsh', '-c', command], text=True, capture_output=True, check=True)
        self.assertIn('<open>\n<ds>\n<--dry-run>', r.stdout)
        self.assertIn('<accounts>\n<switch>\n<a>\n<--local>\n<--no-launch>', r.stdout)
        self.assertIn('<accounts>\n<enroll>\n<b>', r.stdout)
        self.assertIn('<accounts>\n<status>', r.stdout)
        self.assertIn('<cli>\n<ds>\n<-->\n<exec>\n<two words>', r.stdout)
        self.assertIn('<open>\n<ego>', r.stdout)
        self.assertIn('<note with spaces.md>', r.stdout)

    def test_non_app_loopx_and_explicit_codex_native_bypass(self):
        bin_dir = self.home / 'bin'
        bin_dir.mkdir()
        for name in ('codex', 'loopx'):
            p = bin_dir / name
            p.write_text('#!/bin/sh\nprintf "native:<%s>\\n" "$@"\n')
            p.chmod(0o755)
        command = f'''DOTFILES_ROOT={json.dumps(str(ROOT))}; source "$DOTFILES_ROOT/shell/apps.zsh"
_dotfiles_apps() {{ return 98; }}
path=({json.dumps(str(bin_dir))} /usr/bin /bin)
codex --native --version
loopx --format json doctor
codex secondary app
'''
        r = subprocess.run(['/bin/zsh', '-c', command], env={'HOME':str(self.home), 'ZDOTDIR':str(self.home), 'PATH':str(bin_dir)+':/usr/bin:/bin'},
                           text=True, capture_output=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn('native:<--version>', r.stdout)
        self.assertIn('native:<--format>\nnative:<json>\nnative:<doctor>', r.stdout)

    def test_cli_fixed_home_parser(self):
        with patch.object(m, 'cli') as call, patch.object(m.sys, 'argv',
                ['personal-apps', 'cli', 'gpt', '--', 'exec', 'two words']):
            self.assertEqual(m.main(), 0)
        self.assertEqual(call.call_args.args[1:], ('gpt', ['exec', 'two words']))

    def test_installed_symlink_entry_and_receipt_rollback(self):
        r = subprocess.run([m.sys.executable, str(ROOT / 'tools/install.py'), '--home', str(self.home),
                            '--shell-only', '--apply'], check=True, capture_output=True, text=True)
        receipt = json.loads(r.stdout)['receipt']
        entry = self.home / '.local/bin/personal-apps'
        self.assertTrue(entry.is_symlink())
        env = dict(os.environ, HOME=str(self.home))
        preview = subprocess.run([str(entry), 'init'], env=env, check=True, capture_output=True, text=True)
        self.assertEqual(len(json.loads(preview.stdout)['create']), 3)
        self.assertFalse((self.home / '.config').exists())
        subprocess.run([m.sys.executable, str(ROOT / 'tools/install.py'), '--rollback', receipt, '--apply'],
                       check=True, capture_output=True)
        self.assertFalse(entry.exists())


if __name__ == '__main__':
    unittest.main()
