#!/usr/bin/env python3
"""Measure actual interactive login startup without recording shell output."""
import argparse
import json
import os
import statistics
import subprocess
import time
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--repeat',type=int,default=5)
p.add_argument('--zdotdir',help='optional directory containing candidate .zshrc/.zprofile')
a=p.parse_args()
if not 1 <= a.repeat <= 20: p.error('--repeat must be 1..20')
env=os.environ.copy()
if a.zdotdir: env['ZDOTDIR']=os.path.abspath(a.zdotdir)
rows=[]
for _ in range(a.repeat):
 start=time.perf_counter()
 try:
  r=subprocess.run(['/bin/zsh','-lic','exit'],env=env,capture_output=True,timeout=30)
 except subprocess.TimeoutExpired:
  print(json.dumps({'error':'startup timeout after 30s'}));raise SystemExit(1)
 rows.append({'seconds':round(time.perf_counter()-start,4),'exit':r.returncode,'stdout_bytes':len(r.stdout),'stderr_bytes':len(r.stderr)})
print(json.dumps({'samples':rows,'median_seconds':statistics.median(r['seconds'] for r in rows)},indent=2))
raise SystemExit(int(any(r['exit'] for r in rows)))
