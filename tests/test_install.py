import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('installer',ROOT/'tools/install.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class InstallTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name).resolve();self.home=self.root/'home';self.home.mkdir()
  self.source=self.root/'source';self.source.write_text('original')
  self.dest=self.home/'.zshrc';self.links=[(self.source,self.dest)]
 def test_dry_run(self):
  m.install(self.links,self.home);self.assertFalse(self.dest.exists());self.assertFalse((self.home/'.local').exists())
 def test_idempotent_link_and_edit_visible(self):
  m.install(self.links,self.home,True);self.assertTrue(self.dest.is_symlink())
  self.dest.write_text('edited');self.assertEqual(self.source.read_text(),'edited')
  self.assertEqual(m.install(self.links,self.home,True)['changes'],[])
 def test_conflict_preflight_does_not_partially_install(self):
  self.dest.write_text('personal')
  with self.assertRaises(ValueError): m.install([(self.source,self.home/'new'),*self.links],self.home,True)
  self.assertFalse((self.home/'new').exists());self.assertEqual(self.dest.read_text(),'personal')
 def test_backup_and_rollback(self):
  self.dest.write_text('personal');r=m.install(self.links,self.home,True,True)
  m.rollback(Path(r['receipt']),True);self.assertFalse(self.dest.is_symlink());self.assertEqual(self.dest.read_text(),'personal')
 def test_dangling_symlink_preserved(self):
  self.dest.symlink_to(self.root/'missing')
  r=m.install(self.links,self.home,True,True);m.rollback(Path(r['receipt']),True)
  self.assertTrue(self.dest.is_symlink());self.assertEqual(self.dest.readlink(),self.root/'missing')
 def test_rollback_does_not_overwrite_changed_destination(self):
  r=m.install(self.links,self.home,True);self.dest.unlink();self.dest.write_text('new personal content')
  with self.assertRaises(ValueError):m.rollback(Path(r['receipt']),True)
  self.assertEqual(self.dest.read_text(),'new personal content')
 def test_parent_symlink_refused(self):
  alias=self.home/'redirect';alias.symlink_to(self.root,target_is_directory=True)
  with self.assertRaises(ValueError):m.install([(self.source,alias/'file')],self.home,True)
 def test_default_preferences_preflight_and_rollback(self):
  target=self.home/'.tmux.conf';target.write_text('my tmux')
  argv=[sys.executable,str(ROOT/'tools/install.py'),'--shell-only','--home',str(self.home),'--apply']
  rejected=subprocess.run(argv,capture_output=True,text=True)
  self.assertNotEqual(rejected.returncode,0);self.assertFalse(self.dest.exists())
  accepted=subprocess.run(argv+['--replace'],capture_output=True,text=True,check=True)
  result=json.loads(accepted.stdout);self.assertTrue(target.is_symlink())
  self.assertTrue(self.dest.is_symlink())
  if sys.platform=='darwin':
   self.assertTrue((self.home/'Library/Application Support/iTerm2/DynamicProfiles/dotfiles-personal.json').is_symlink())
  m.rollback(Path(result['receipt']),True)
  self.assertEqual(target.read_text(),'my tmux');self.assertFalse(self.dest.exists())
 def test_skill_digest_and_extra_files(self):
  repo=self.root/'repo';skill=repo/'.codex/skills/demo';skill.mkdir(parents=True)
  text='---\nname: demo\ndescription: Example\n---\n';(skill/'SKILL.md').write_text(text)
  manifest=repo/'note-system/skills/manifest.json';manifest.parent.mkdir(parents=True)
  manifest.write_text(json.dumps({'version':1,'skills':[{'name':'demo','files':{'SKILL.md':hashlib.sha256(text.encode()).hexdigest()}}]}))
  self.assertEqual(len(m.skill_links(repo,self.home/'skills')),1)
  (skill/'private.txt').write_text('not reviewed')
  with self.assertRaises(ValueError):m.skill_links(repo,self.home/'skills')
  (skill/'private.txt').unlink();(skill/'SKILL.md').write_text('changed')
  with self.assertRaises(ValueError):m.skill_links(repo,self.home/'skills')

if __name__=='__main__':unittest.main()
