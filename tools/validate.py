"""Validate built asset references and source parity; this is not an engine test."""
import json,zipfile,hashlib,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];BP=R/'packs/MonsterPlus_BP';RP=R/'packs/MonsterPlus_RP'
def read(p):return json.loads(p.read_text())
files=list((R/'packs').rglob('*.json'))
for p in files:read(p)
mobs=read(R/'source/mobs.json');assert len(mobs)==18
geos={}
for p in (RP/'models/entity').glob('*.json'):
 g=read(p)['minecraft:geometry'][0];geos[g['description']['identifier']]=g
 names=[b['name'] for b in g['bones']];assert len(names)==len(set(names)),p
 for b in g['bones']:
  if 'parent'in b:assert b['parent'] in names,(p,b)
  for c in b.get('cubes',[]):assert all(math.isfinite(x) for x in c['origin']+c['size']),p
controllers=read(RP/'render_controllers/monsterplus.render_controllers.json')['render_controllers'];animations=read(RP/'animations/monsterplus.animation.json')['animations']
for m in mobs:
 id=m['id'];b=read(BP/f'entities/{id}.json')['minecraft:entity'];d=read(RP/f'entity/{id}.entity.json')['minecraft:client_entity']['description']
 assert b['description']['identifier']==d['identifier']=='monsterplus:'+id
 assert b['components']['minecraft:health']['max']==m['attributes']['MAX_HEALTH']
 for name,prop in b['description']['properties'].items():
  if prop['type']=='float':
   assert isinstance(prop['default'],float),(id,name,'Bedrock rejects integer defaults for float properties')
   assert all(isinstance(v,float) for v in prop['range']),(id,name,'Float property range must serialize as floats')
 for ref in d['geometry'].values():assert ref in geos,ref
 for ref in d['textures'].values():assert (RP/(ref+'.png')).is_file(),ref
 for ref in d['render_controllers']:assert ref in controllers,ref
 names={b['name'] for b in geos[d['geometry']['default']]['bones']}
 for ref in d['animations'].values():assert ref in animations and set(animations[ref]['bones'])<=names,(id,ref)
 assert (RP/f'entity/{id}.entity.json').is_file()
 egg=read(BP/f'items/{id}_spawn_egg.json')['minecraft:item']
 assert egg['description']['identifier']=='monsterplus:'+id+'_spawn_egg'
 assert egg['description']['menu_category']['category']=='nature'
 assert egg['components']['minecraft:entity_placer']['entity']=='monsterplus:'+id
 assert b['description']['is_summonable'] is True and b['description']['is_spawnable'] is False
# Byte-for-byte texture and OGG preservation.
for p in (R/'source/assets').rglob('*'):
 if p.suffix in ['.png','.ogg']:
  target=RP/p.relative_to(R/'source/assets');assert target.is_file() and p.read_bytes()==target.read_bytes(),p
sounds=read(RP/'sounds/sound_definitions.json')['sound_definitions']
for k,v in sounds.items():
 for f in v['sounds']:assert (RP/(f+'.ogg')).is_file(),(k,f)
for p in (BP/'loot_tables/entities').glob('*.json'):
 for pool in read(p)['pools']:
  for e in pool['entries']:
   if e['name'].startswith('monsterplus:'):assert (BP/f'items/{e["name"].split(":")[1]}.json').is_file(),(p,e)
eggs=(BP/'functions/monsterplus/eggs.mcfunction').read_text().splitlines()
assert {line for line in eggs if line.startswith('give ')}=={f'give @s monsterplus:{m["id"]}_spawn_egg 1' for m in mobs}
# Exactly these three creatures are source summons, not ambient spawns.
assert {p.stem for p in (BP/'spawn_rules').glob('*.json')}=={m['id'] for m in mobs}-{'spectral_skeleton','opalescent_eye','ancient_hero_skull'}
# Stable UUIDs, linked RP, and stable API dependency.
bpm=read(BP/'manifest.json');rpm=read(RP/'manifest.json');assert bpm['dependencies'][0]['uuid']==rpm['header']['uuid']
uuids=[p['uuid'] for m in [bpm,rpm] for p in [m['header']]+m['modules']];assert len(uuids)==len(set(uuids))
archive=R/'dist/MonsterPlus-Bedrock-0.1.2.mcaddon'
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for p in (R/'packs').rglob('*'):
  if p.is_file():assert z.read(str(p.relative_to(R/'packs')))==p.read_bytes(),p
print(f'PASS: {len(files)} JSON files; 18 mob definitions and source health values; geometry, texture, animation, sound, loot, spawn and archive references')
