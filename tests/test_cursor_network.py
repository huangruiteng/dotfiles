import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cursor_network', ROOT / 'tools/cursor_network.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class NetworkTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name).resolve() / 'home with spaces'
        self.home.mkdir()
        self.cursor = self.home / 'Library/Application Support/Cursor/User/settings.json'
        self.cursor.parent.mkdir(parents=True)
        self.before = b'{"editor.fontSize": 14, "fixture.private": "keep locally"}\n'
        self.cursor.write_bytes(self.before)
        self.profile = m.load_profile(m.DEFAULT_PROFILE)
        self.domains = ['*.local', 'custom.example']
        self.addCleanup(patch.stopall)
        self.read = patch.object(m, 'read_bypass', side_effect=lambda service: list(self.domains)).start()
        self.write = patch.object(m, 'set_bypass', side_effect=self.set_domains).start()

    def set_domains(self, service, domains):
        self.domains = list(domains)

    def apply(self):
        return m.configure(self.home, self.profile, 'Wi-Fi', True)

    def test_preview_does_not_write_or_expose_unrelated_settings(self):
        preview = m.configure(self.home, self.profile, 'Wi-Fi')
        self.assertFalse(preview['applied'])
        self.assertNotIn('keep locally', json.dumps(preview))
        self.assertEqual(self.cursor.read_bytes(), self.before)
        self.assertFalse((self.home / '.local').exists())
        self.write.assert_not_called()

    def test_apply_preserves_preferences_rules_and_is_idempotent(self):
        result = self.apply()
        settings = json.loads(self.cursor.read_text())
        self.assertEqual(settings['editor.fontSize'], 14)
        self.assertEqual(settings['fixture.private'], 'keep locally')
        self.assertEqual(settings['http.proxy'], 'http://127.0.0.1:15236')
        self.assertIs(settings['cursor.general.disableHttp2'], True)
        self.assertIs(settings['http.proxyStrictSSL'], True)
        self.assertEqual(settings['http.proxySupport'], 'override')
        self.assertIn('custom.example', self.domains)
        self.assertIn('*.cn', self.domains)
        self.assertEqual(len(self.domains), len(set(self.domains)))
        receipt = Path(result['receipt'])
        self.assertEqual(receipt.stat().st_mode & 0o777, 0o600)
        self.assertEqual(receipt.parent.stat().st_mode & 0o777, 0o700)
        backup = receipt.parent / 'cursor-settings.prior.json'
        self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
        self.assertEqual(backup.read_bytes(), self.before)
        self.assertTrue(self.apply()['already_configured'])
        self.assertEqual(len(list(receipt.parent.parent.iterdir())), 1)
        self.assertEqual(self.write.call_count, 1)

    def test_rollback_restores_exact_original_bytes_and_rules(self):
        receipt = Path(self.apply()['receipt'])
        self.assertTrue(m.rollback(self.home, receipt)['preview'])
        self.assertNotEqual(self.cursor.read_bytes(), self.before)
        self.assertTrue(m.rollback(self.home, receipt, True)['readback_verified'])
        self.assertEqual(self.cursor.read_bytes(), self.before)
        self.assertEqual(self.domains, ['*.local', 'custom.example'])
        self.assertTrue(m.rollback(self.home, receipt, True)['rolled_back'])

    def test_rollback_preserves_later_cursor_or_network_edits(self):
        receipt = Path(self.apply()['receipt'])
        self.cursor.write_text(self.cursor.read_text() + ' ')
        before_rollback = self.cursor.read_bytes()
        with self.assertRaisesRegex(ValueError, 'later edits'):
            m.rollback(self.home, receipt, True)
        self.assertEqual(self.cursor.read_bytes(), before_rollback)
        self.cursor.write_bytes(before_rollback[:-1])
        self.domains.append('later.example')
        with self.assertRaisesRegex(ValueError, 'later edits'):
            m.rollback(self.home, receipt, True)
        self.assertIn('later.example', self.domains)

    def test_failed_system_write_has_recoverable_partial_receipt(self):
        self.write.side_effect = subprocess.CalledProcessError(1, ['networksetup'])
        with self.assertRaisesRegex(ValueError, 'Apply incomplete'):
            self.apply()
        receipt = next((self.home / '.local/state/dotfiles/network').glob('*/receipt.json'))
        self.assertEqual(json.loads(receipt.read_text())['status'], 'applying')
        self.assertNotEqual(self.cursor.read_bytes(), self.before)
        self.write.side_effect = self.set_domains
        m.rollback(self.home, receipt, True)
        self.assertEqual(self.cursor.read_bytes(), self.before)
        self.assertEqual(self.domains, ['*.local', 'custom.example'])

    def test_jsonc_and_symlink_stop_before_any_write(self):
        self.cursor.write_text('{\n // preserve this comment\n "editor.fontSize": 14\n}')
        with self.assertRaisesRegex(ValueError, 'merge manually'):
            self.apply()
        self.assertFalse((self.home / '.local').exists())
        self.write.assert_not_called()
        self.cursor.unlink()
        outside = self.home / 'outside.json'
        outside.write_bytes(self.before)
        self.cursor.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            self.apply()
        self.assertEqual(outside.read_bytes(), self.before)

    def test_foreign_receipt_and_modified_backup_are_refused(self):
        receipt = Path(self.apply()['receipt'])
        with self.assertRaisesRegex(ValueError, 'this home'):
            m.rollback(self.home, self.home / 'foreign/receipt.json', True)
        (receipt.parent / 'cursor-settings.prior.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            m.rollback(self.home, receipt, True)

    def test_missing_cursor_file_can_be_created_and_owned_rollback_removes_it(self):
        self.cursor.unlink()
        receipt = Path(self.apply()['receipt'])
        self.assertTrue(self.cursor.exists())
        m.rollback(self.home, receipt, True)
        self.assertFalse(self.cursor.exists())

    def test_profile_rejects_credentials_remote_proxy_and_tls_disable(self):
        for address in ['http://user:password@127.0.0.1:1234', 'http://remote.example:1234',
                        'socks5://127.0.0.1:1234', 'http://127.0.0.1:bad']:
            with self.assertRaises(ValueError):
                m.load_profile(m.DEFAULT_PROFILE, address)
        path = self.home / 'profile.json'
        data = json.loads(m.DEFAULT_PROFILE.read_text())
        data['cursor_settings']['http.proxyStrictSSL'] = False
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'TLS validation'):
            m.load_profile(path)


if __name__ == '__main__':
    unittest.main()
