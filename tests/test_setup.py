import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
checkout = load('check_checkout'); markdown = load('check_markdown')
lark = load('check_lark_auth')


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def test_missing_tracked_file_and_sparse_are_rejected(self):
        self.git('init'); (self.root/'README.md').write_text('# Repo'); self.git('add', '.')
        self.assertTrue(checkout.check_checkout(self.root)['ok'])
        (self.root/'README.md').unlink()
        self.assertFalse(checkout.check_checkout(self.root)['ok'])
        (self.root/'README.md').write_text('# Repo'); self.git('config', 'core.sparseCheckout', 'true')
        self.assertFalse(checkout.check_checkout(self.root)['ok'])

    def test_export_and_directory_replacing_tracked_file_are_rejected(self):
        with self.assertRaises(ValueError): checkout.check_checkout(self.root)
        self.git('init'); p=self.root/'file'; p.write_text('file'); self.git('add', '.')
        p.unlink(); p.mkdir()
        self.assertFalse(checkout.check_checkout(self.root)['ok'])

    def test_broken_tracked_symlink_is_present_but_reported(self):
        self.git('init'); (self.root/'old-link').symlink_to('not-transferred'); self.git('add', '.')
        result=checkout.check_checkout(self.root)
        self.assertTrue(result['ok']); self.assertEqual(result['missing'], [])
        self.assertEqual(result['broken_tracked_symlinks'], ['old-link'])

    def test_markdown_relative_to_source_with_chinese_spaces_and_url_encoding(self):
        folder=self.root/'中文 notes'; folder.mkdir(); (folder/'目标.md').write_text('# Target')
        note=self.root/'README.md'
        note.write_text('[中文](<中文 notes/目标.md>)\n[编码](%E4%B8%AD%E6%96%87%20notes/%E7%9B%AE%E6%A0%87.md)\n[站点](https://example.com/)\n```sh\n[示例](missing.md)\n```\n', encoding='utf-8')
        result=markdown.check_markdown(note)
        self.assertTrue(result['ok']);self.assertEqual(result['local_destinations'],2)
        self.assertFalse(result['ui_verified'])
        (folder/'目标.md').unlink(); self.assertFalse(markdown.check_markdown(note)['ok'])

    def test_reading_fixture_links_resolve(self):
        self.assertTrue(markdown.check_markdown(ROOT/'profiles/personal-mac/smoke/reading.md')['ok'])
        self.assertTrue(markdown.check_markdown(ROOT/'profiles/personal-mac/smoke/中文 notes/目标.md')['ok'])

    def test_lark_user_verification_never_echoes_identity(self):
        data={'identity':'user','verified':True,'identities':{'user':{'available':True,'status':'ready','tokenStatus':'valid','verified':True,'openId':'PRIVATE-ID','userName':'PRIVATE-NAME','scope':'PRIVATE-SCOPE'}}}
        result=lark.summarize(data,0)
        self.assertTrue(result['ok']);self.assertNotIn('PRIVATE',json.dumps(result))
        data['identity']='bot'
        self.assertFalse(lark.summarize(data,0)['ok'])
        data['identity']='user';data['identities']['user']['verified']=False
        self.assertFalse(lark.summarize(data,0)['ok'])
        self.assertFalse(lark.summarize(data,1)['ok'])


if __name__ == '__main__': unittest.main()
