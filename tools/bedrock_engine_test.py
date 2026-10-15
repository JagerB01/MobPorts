"""Test native egg registration/dispensing using an installed official Bedrock dedicated server.
The runner creates only its own disposable world and a separate harness pack. It never patches the tested add-on.
"""
import argparse,json,zipfile,shutil,subprocess,threading,queue,time,os,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--server-dir',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);args=p.parse_args();base=args.server_dir.resolve();archive=args.archive.resolve()
version=json.loads((R/'package.json').read_text())['version'];world_name='MobPortsEggTest_'+version.replace('.','_')
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for folder,kind in [('MonsterPlus_BP','behavior_packs'),('MonsterPlus_RP','resource_packs')]:
  dest=base/kind/folder
  if dest.exists():shutil.rmtree(dest)
  for n in z.namelist():
   if n.startswith(folder+'/') and not n.endswith('/'):
    path=dest/n[len(folder)+1:];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(n))
harness=base/'behavior_packs/MobPortsEggTest';harness.mkdir(exist_ok=True)
main=json.loads((base/'behavior_packs/MonsterPlus_BP/manifest.json').read_text());resource=json.loads((base/'resource_packs/MonsterPlus_RP/manifest.json').read_text())
harness_id='a5b8f404-2858-4c58-a5ac-f199f8452c03'
manifest={'format_version':2,'header':{'name':'Native egg regression harness','description':'Local integration tests only','uuid':harness_id,'version':[1,0,0],'min_engine_version':[1,21,90]},'modules':[{'type':'data','uuid':'f2f39e0e-3767-426b-910a-12b253fdbb89','version':[1,0,0]},{'type':'script','language':'javascript','entry':'scripts/test.js','uuid':'c39f1dd7-0200-47ee-92df-f44feb503d1b','version':[1,0,0]}],'dependencies':[{'module_name':'@minecraft/server','version':'2.0.0'}]}
(harness/'manifest.json').write_text(json.dumps(manifest));(harness/'scripts').mkdir(exist_ok=True)
ids=[m['id'] for m in json.loads((R/'source/mobs.json').read_text())]
(harness/'scripts/test.js').write_text((R/'tools/engine_fixture/egg_test.js').read_text().replace('__MOB_IDS__',json.dumps(ids)))
world=base/'worlds'/world_name
if world.exists():shutil.rmtree(world) # Dedicated, runner-owned disposable world only.
world.mkdir(parents=True)
(world/'world_behavior_packs.json').write_text(json.dumps([{'pack_id':main['header']['uuid'],'version':main['header']['version']},{'pack_id':harness_id,'version':[1,0,0]}]))
(world/'world_resource_packs.json').write_text(json.dumps([{'pack_id':resource['header']['uuid'],'version':resource['header']['version']}]))
props=base/'server.properties';s=props.read_text();settings={'level-name':world_name,'online-mode':'false','allow-list':'false','enable-lan-visibility':'false','allow-cheats':'true','difficulty':'normal','gamemode':'creative','content-log-file-enabled':'true','content-log-console-output-enabled':'true','max-threads':'2'}
lines=[]
for line in s.splitlines():
 k=line.split('=',1)[0]
 if k in settings:line=k+'='+settings.pop(k)
 lines.append(line)
lines.extend(k+'='+v for k,v in settings.items());props.write_text('\n'.join(lines)+'\n')
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(base)
proc=subprocess.Popen([str(base/'bedrock_server')],cwd=base,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
q=queue.Queue();captured=[]
def reader():
 for line in proc.stdout:q.put(line)
threading.Thread(target=reader,daemon=True).start();deadline=time.monotonic()+75;result=None;started=False
try:
 while time.monotonic()<deadline:
  try:line=q.get(timeout=1)
  except queue.Empty:
   if proc.poll() is not None:break
   continue
  captured.append(line)
  if 'Server started.' in line and not started:
   started=True;proc.stdin.write('scriptevent mobports:eggs\n');proc.stdin.flush()
  if 'MP_EGG_PASS ' in line:print(line.strip(),flush=True)
  if 'MP_EGG_TEST_FAILURE ' in line:raise RuntimeError(line.strip())
  if 'MP_EGG_TEST_RESULT ' in line:
   result=json.loads(line.split('MP_EGG_TEST_RESULT ',1)[1].strip());break
 if result is None:raise RuntimeError('Native egg test did not produce a result before timeout')
 assert result['passed']==result['total']==18,result
 bad=[x for x in captured if ' ERROR]' in x and any(mark in x for mark in ['[Actor]','[Json]','[Scripting]','[Item]'])]
 assert not bad,'Content errors:\n'+''.join(bad)
 result.update(archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),nativeContentErrors=0,method='Each real egg placed in a powered native dispenser; entitySpawn observed; item consumption checked.')
 (R/'validation').mkdir(exist_ok=True);(R/'validation'/f'bedrock-eggs-{version}.json').write_text(json.dumps(result,indent=2)+'\n')
 print(f'PASS: Bedrock 1.26.52.3 spawned all 18 mobs from the actual egg items; no native content errors.')
finally:
 if proc.poll() is None:
  try:proc.stdin.write('stop\n');proc.stdin.flush();proc.wait(timeout=15)
  except (BrokenPipeError,subprocess.TimeoutExpired):proc.kill();proc.wait()
 while not q.empty():captured.append(q.get_nowait())
 (R/'validation').mkdir(exist_ok=True);(R/'validation'/f'bedrock-eggs-{version}.log').write_text(''.join(captured))
