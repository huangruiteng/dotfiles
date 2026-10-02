import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]

class ShellTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.home=Path(self.tmp.name)
  (self.home/'.zshrc').symlink_to(ROOT/'zshrc')
  (self.home/'.zprofile').symlink_to(ROOT/'zprofile')
  self.env={'HOME':str(self.home),'ZDOTDIR':str(self.home),'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','TERM':'xterm-256color','DOTFILES_SKIP_LOCAL':'1'}
 def run_shell(self,cmd,interactive=True):
  r=subprocess.run(['/bin/zsh','-ic' if interactive else '-c',cmd],env=self.env,text=True,capture_output=True,timeout=20)
  self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stderr,'');return r.stdout
 def test_quiet_start_and_cached_completion(self):
  self.assertEqual(self.run_shell('exit'),'')
  dump=next(self.home.glob('.zcompdump-*'));before=dump.stat().st_mtime_ns
  self.assertEqual(self.run_shell('exit'),'');self.assertEqual(dump.stat().st_mtime_ns,before)
 def test_source_is_idempotent_and_not_noisy(self):
  self.assertEqual(self.run_shell('source ~/.zshrc; print -- ${#precmd_functions}'),'1\n')
 def test_activated_python_precedes_fallback(self):
  venv=self.home/'venv/bin';venv.mkdir(parents=True)
  for name in ['python','python3']:
   p=venv/name;p.write_text('#!/bin/sh\nexit 0\n');p.chmod(0o755)
  self.env['PATH']=str(venv)+':'+self.env['PATH'];self.env['VIRTUAL_ENV']=str(venv.parent)
  self.assertEqual(self.run_shell('command -v python'),str(venv/'python')+'\n')
 def test_local_hook_cannot_mask_active_environment(self):
  venv=self.home/'venv/bin';venv.mkdir(parents=True)
  python=venv/'python';python.write_text('#!/bin/sh\nexit 0\n');python.chmod(0o755)
  other=self.home/'other/bin';other.mkdir(parents=True)
  wrong=other/'python';wrong.write_text('#!/bin/sh\nexit 1\n');wrong.chmod(0o755)
  (self.home/'.zshrc_local').write_text(f'path=("{other}" $path)\n')
  self.env['DOTFILES_SKIP_LOCAL']='0';self.env['VIRTUAL_ENV']=str(venv.parent)
  self.env['PATH']=str(venv)+':'+self.env['PATH']
  self.assertEqual(self.run_shell('command -v python'),str(python)+'\n')
 def test_noninteractive_source_only_sets_path(self):
  self.assertEqual(self.run_shell('source ~/.zshrc; print -- ${_DOTFILES_SHELL_LOADED:-no}',False),'no\n')
  self.assertEqual(list(self.home.glob('.zcompdump-*')),[])
 def test_key_bindings_and_completion(self):
  s=self.run_shell("print -- $+functions[compdef]; bindkey -M viins '^A'; bindkey -M viins '^R'")
  self.assertIn('1\n',s);self.assertIn('beginning-of-line',s);self.assertIn('history',s)
 def test_prompt_escapes_percent_and_keeps_status(self):
  s=self.run_shell("MY_ENV='test%F{red}'; false; _dotfiles_precmd; print -r -- $PROMPT")
  self.assertIn('1 ',s);self.assertIn('test%%F{red}',s)

if __name__=='__main__':unittest.main()
