"""Build Bedrock packs from the recovered Java model and entity data."""
import json,math,shutil,uuid,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'source';BP=ROOT/'packs/MonsterPlus_BP';RP=ROOT/'packs/MonsterPlus_RP'
def load(p):return json.loads(p.read_text())
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+'\n')
for folder in [BP/'entities',BP/'items',BP/'spawn_rules',BP/'loot_tables',BP/'functions',RP]:
 if folder.exists():shutil.rmtree(folder)
 folder.mkdir(parents=True,exist_ok=True)
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/JagerB01/MobPorts/'+s))
mobs=load(SRC/'mobs.json');models=load(SRC/'models.json')
fly={'opalescent_eye','demon_eye','ender_eye','ancient_hero_skull','spectral_skull','wisp','soul','lava_squid','mother_lava_squid'}
neutral={'ender_eye','wisp','soul','lava_squid'}
casters={'abyssologer','desert_acolyte','desert_sorceress'}
ranged={'glow_skeleton','overgrown_skeleton'}
textures=dict(abyssologer='abyssologer',glow_skeleton='glow_skeleton',swamp_zombie='swamp_zombie',opalescent_eye='opalescent_eye',spectral_skeleton='spectre',lava_squid='lava_squid',mother_lava_squid='lava_squid',crystal_zombie='crystal_zombie',overgrown_skeleton='overgrown_skeleton_new',demon_eye='demon_eye/demon_eye_red',ender_eye='demon_eye/ender_eye',ancient_hero='ancient_hero',ancient_hero_skull='ancient_hero',wisp='wisp',soul='soul',desert_sorceress='desert_sorceress',desert_acolyte='desert_acolyte',spectral_skull='spectral_skull')
emissive=dict(abyssologer='abyssologer_crystal',crystal_zombie='crystal_zombie_crystals',ancient_hero='ancient_hero_emissive',ancient_hero_skull='ancient_hero_emissive',overgrown_skeleton='overgrown_skeleton_emissive',ender_eye='demon_eye/ender_eye_overlay')
translucent=dict(swamp_zombie='swamp_zombie_outer',opalescent_eye='opalescent_eye',demon_eye='demon_eye/demon_eye_translucent',ender_eye='demon_eye/ender_eye_overlay1',wisp='wisp_outer',soul='soul_outer')
scales=dict(mother_lava_squid=6,ancient_hero=1.1,ancient_hero_skull=1.1,wisp=.4,soul=.4)
for pack,kind in [(RP,'resources'),(BP,'data')]:
 modules=[dict(type=kind,uuid=uid(kind+'module'),version=[0,1,2])]
 if pack==BP:modules.append(dict(type='script',language='javascript',entry='scripts/main.js',uuid=uid('scriptmodule'),version=[0,1,2]))
 manifest=dict(format_version=2,header=dict(name='Monster Plus '+('Resources' if pack==RP else 'Behaviors'),description='All 18 Monster Plus mobs — Bedrock port candidate',uuid=uid(kind),version=[0,1,2],min_engine_version=[1,21,90]),modules=modules)
 if pack==BP:manifest['dependencies']=[dict(uuid=uid('resources'),version=[0,1,2]),dict(module_name='@minecraft/server',version='2.0.0')]
 write(pack/'manifest.json',manifest)
for folder in ['textures','sounds']:
 shutil.copytree(SRC/'assets'/folder,RP/folder,dirs_exist_ok=True)
# Numeric Java boxes retain their UV coordinates and hierarchy. Reflect the Y axis.
def geometry(model,id):
 original={b['name']:b for b in model['bones']};world={}
 def origin(name):
  if name in world:return world[name]
  b=original[name];p=origin(b['parent']) if b.get('parent') else [0,0,0]
  world[name]=[p[i]+b['pivot'][i] for i in range(3)];return world[name]
 bones=[]
 for b in model['bones']:
  p=origin(b['name']);bone=dict(name=b['name'],pivot=[p[0],24-p[1],p[2]])
  if b.get('parent'):bone['parent']=b['parent']
  r=b.get('rotation',[0,0,0]);bone['rotation']=[-r[0]*180/math.pi,r[1]*180/math.pi,-r[2]*180/math.pi]
  cs=[]
  for c in b['cubes']:
   x,y,z=c['origin'];w,h,d=c['size'];cc=dict(origin=[p[0]+x,24-p[1]-y-h,p[2]+z],size=[w,h,d],uv=c['uv'])
   if c.get('inflate'):cc['inflate']=c['inflate']
   if c.get('mirror'):cc['mirror']=True
   cs.append(cc)
  if cs:bone['cubes']=cs
  bones.append(bone)
 if any(b['name']=='right_arm' for b in bones):
  arm=next(b for b in bones if b['name']=='right_arm');pivot=arm['pivot']
  bones.append(dict(name='rightItem',parent='right_arm',pivot=[pivot[0],pivot[1]-10,pivot[2]+1]))
 if any(b['name']=='left_arm' for b in bones):
  arm=next(b for b in bones if b['name']=='left_arm');pivot=arm['pivot']
  bones.append(dict(name='leftItem',parent='left_arm',pivot=[pivot[0],pivot[1]-10,pivot[2]+1]))
 return dict(format_version='1.12.0',**{'minecraft:geometry':[dict(description=dict(identifier='geometry.monsterplus.'+id,texture_width=model['texture_size'][0],texture_height=model['texture_size'][1],visible_bounds_width=16,visible_bounds_height=16,visible_bounds_offset=[0,2,0]),bones=bones)]})
def filt(family):return {'test':'is_family','subject':'other','value':family}
lang=['pack.name=Monster Plus','pack.description=Monster Plus Bedrock port candidate']
render={};animations={};client_sounds={};audit=[]
for m in mobs:
 id=m['id'];a=m['attributes'];key='monsterplus:'+id;model=models[m['model']];scale=scales.get(id,1)
 g=geometry(model,id)
 # Halo shell uses a different deformation or UV region, not another opaque copy of the base.
 write(RP/f'models/entity/{id}.geo.json',g)
 geos={'default':'geometry.monsterplus.'+id};tex={'default':'textures/entities/'+textures[id]};materials={'default':'entity_alphatest'};controllers=['controller.render.monsterplus.'+id]
 base=dict(geometry='Geometry.default',materials=[{'*':'Material.default'}],textures=['Texture.default'])
 if id=='ancient_hero':base['part_visibility']=[{'hat':"q.property('monsterplus:phase') == 0"},{'crest':"q.property('monsterplus:phase') == 0"},{'head':"q.property('monsterplus:phase') < 2"},{'mouth':"q.property('monsterplus:phase') < 2"}]+[{b:"q.property('monsterplus:phase') < 3"} for b in ['body_armour','right_arm_armour','left_arm_armour','cape']]
 if id in casters:base['part_visibility']=[{'arms':"!q.property('monsterplus:casting')"},{'arms_rotation':"!q.property('monsterplus:casting')"},{'arms_flipped':"!q.property('monsterplus:casting')"},{'left_arm':"q.property('monsterplus:casting')"},{'right_arm':"q.property('monsterplus:casting')"}]
 if id=='demon_eye':
  colors=['red','purple','green','yellow','blue','teeth','teeth_closed']
  for i,c in enumerate(colors):tex['variant'+str(i)]='textures/entities/demon_eye/demon_eye_'+c
  base['arrays']={'textures':{'Array.eyes':['Texture.variant'+str(i) for i in range(7)]}};base['textures']=["Array.eyes[q.variant == 5 ? (math.mod(math.floor(q.life_time * 20), 12) < 8 ? 5 : 6) : q.variant]"]
 if id in ['spectral_skeleton','wisp','soul','opalescent_eye']:materials['default']='entity_alphablend'
 if id=='demon_eye':
  iris=['red','purple','green','yellow','blue']
  for i,c in enumerate(iris):tex['iris'+str(i)]='textures/entities/demon_eye/demon_eye_'+c+'_iris'
  tex['iris5']='textures/entities/demon_eye/empty';materials['iris']='entity_emissive_alpha'
  rc='controller.render.monsterplus.demon_eye_iris';controllers.append(rc)
  render[rc]={'arrays':{'textures':{'Array.irises':['Texture.iris'+str(i) for i in range(6)]}},'geometry':'Geometry.default','materials':[{'*':'Material.iris'}],'textures':['Array.irises[q.variant]']}
 render['controller.render.monsterplus.'+id]=base
 for layer,mapping,material in [('glow',emissive,'entity_emissive_alpha'),('shell',translucent,'entity_alphablend')]:
  if id not in mapping:continue
  texture='textures/entities/'+mapping[id]
  if not (RP/(texture+'.png')).exists():raise ValueError('Missing layer '+texture)
  tex[layer]=texture;materials[layer]=material
  layer_model=json.loads(json.dumps(model))
  if id=='opalescent_eye':
   for b in layer_model['bones']:
    for c in b['cubes']:c['uv']=[32,0];c['inflate']=.5
  if id in ['wisp','soul']:
   for b in layer_model['bones']:
    for c in b['cubes']:c['inflate']=2.02 if b['name']=='body' else .5
  if layer=='shell' and id=='swamp_zombie':
   for b in layer_model['bones']:
    for c in b['cubes']:c['inflate']=.25
  geom_id=id+'_'+layer;geos[layer]='geometry.monsterplus.'+geom_id
  write(RP/f'models/entity/{geom_id}.geo.json',geometry(layer_model,geom_id))
  rc='controller.render.monsterplus.'+geom_id;controllers.append(rc)
  r=dict(geometry='Geometry.'+layer,materials=[{'*':'Material.'+layer}],textures=['Texture.'+layer])
  if id=='ancient_hero':r['part_visibility']=base['part_visibility']
  render[rc]=r
 # Procedural animation uses recovered named bones rather than a vanilla model substitution.
 names={b['name'] for b in model['bones']};bones={}
 walk="math.cos(q.modified_distance_moved * 38.17) * q.modified_move_speed * 57.3"
 for b in names:
  if b in ['right_leg','left_leg']:bones[b]={'rotation':[walk+(' * -1' if b=='left_leg' else ''),0,0]}
  if b in ['right_arm','left_arm']:
   if id in casters:bones[b]={'rotation':["q.property('monsterplus:casting') ? -140 : 0",0,(-25 if b=='right_arm' else 25)]}
   elif id in ['swamp_zombie','crystal_zombie']:bones[b]={'rotation':[-90,0,0]}
   elif id in ranged:bones[b]={'rotation':["q.property('monsterplus:ranged') && q.has_target ? -90 : "+walk,0,0]}
   else:bones[b]={'rotation':[walk+(' * -1' if b=='right_arm' else ''),0,0]}
  if b=='head':bones[b]={'rotation':['q.target_x_rotation','q.target_y_rotation',0]}
  if b=='hat' and not any(x.get('parent')=='head' and x['name']=='hat' for x in model['bones']):bones[b]={'rotation':['q.target_x_rotation','q.target_y_rotation',0]}
  if b=='mouth':bones[b]={'position':[0,'-2.5 * math.cos(q.life_time * 286.48)',0]}
  if b.startswith('tentacle'):bones[b]={'rotation':['15 + 20 * math.sin(q.life_time * 160)',0,0]}
  if b=='tendrils_child':bones[b]={'rotation':['q.target_x_rotation * 0.5','15 * math.cos(q.life_time * 114.59) - q.target_y_rotation * 0.75',0]}
  if b in ['eye','tendrils']:bones[b]={'scale':"q.property('monsterplus:iris_scale')",'rotation':['q.target_x_rotation * 0.15','q.target_y_rotation * 0.5',0]}
  if b=='cape':bones[b]={'rotation':['15 + 10 * math.cos(q.life_time * 114.59)',0,0]}
 anim='animation.monsterplus.'+id;animations[anim]=dict(loop=True,bones=bones)
 desc=dict(identifier=key,materials=materials,textures=tex,geometry=geos,animations={'movement':anim},scripts={'animate':['movement'],'scale':f"{scale} * q.property('monsterplus:body_scale')"},render_controllers=controllers,enable_attachables=True,spawn_egg={'base_color':'#43354D','overlay_color':'#A188C4'})
 write(RP/f'entity/{id}.entity.json',dict(format_version='1.10.0',**{'minecraft:client_entity':{'description':desc}}))
 fam=['monsterplus','mob',id]
 if id not in neutral:fam.append('monster')
 if id in ['swamp_zombie','crystal_zombie']:fam.append('undead')
 if id.endswith('skeleton') or id in ['ancient_hero','ancient_hero_skull','spectral_skull']:fam.extend(['undead','skeleton'])
 props={'monsterplus:casting':dict(type='bool',default=False,client_sync=True),'monsterplus:phase':dict(type='int',range=[0,3],default=0,client_sync=True),'monsterplus:ranged':dict(type='bool',default=False,client_sync=True),'monsterplus:body_scale':dict(type='float',range=[0.5,2.0],default=1.0,client_sync=True),'monsterplus:iris_scale':dict(type='float',range=[0.9,1.25],default=1.0,client_sync=True)}
 comp={'minecraft:type_family':{'family':fam},'minecraft:health':{'value':a['MAX_HEALTH'],'max':a['MAX_HEALTH']},'minecraft:collision_box':{'width':m['width'],'height':m['height']},'minecraft:movement':{'value':a['MOVEMENT_SPEED']},'minecraft:follow_range':{'value':a['FOLLOW_RANGE']},'minecraft:attack':{'damage':a.get('ATTACK_DAMAGE',2)},'minecraft:knockback_resistance':{'value':min(1,a.get('KNOCKBACK_RESISTANCE',0))},'minecraft:physics':{'has_gravity':id not in fly},'minecraft:pushable':{'is_pushable':True,'is_pushable_by_piston':True},'minecraft:jump.static':{},'minecraft:nameable':{},'minecraft:despawn':{'despawn_from_distance':{}},'minecraft:behavior.look_at_player':{'priority':9,'look_distance':8},'minecraft:behavior.random_look_around':{'priority':10},'minecraft:behavior.hurt_by_target':{'priority':1}}
 comp['minecraft:experience_reward']={'on_death':f'query.last_hit_by_player ? '+str({'ancient_hero':30,'ancient_hero_skull':10,'abyssologer':10,'desert_acolyte':10,'desert_sorceress':15,'demon_eye':7,'wisp':1,'soul':1}.get(id,5))+' : 0'}
 if id in fly:
  comp.update({'minecraft:can_fly':{},'minecraft:movement.fly':{},'minecraft:flying_speed':{'value':.15},'minecraft:navigation.fly':{'can_path_over_water':True,'avoid_damage_blocks':False},'minecraft:behavior.random_fly':{'priority':8,'xz_dist':8,'y_dist':4,'y_offset':0,'speed_multiplier':1}})
 else:
  comp.update({'minecraft:movement.basic':{},'minecraft:navigation.walk':{'avoid_water':False,'can_path_over_water':True},'minecraft:behavior.random_stroll':{'priority':8,'speed_multiplier':.6},'minecraft:behavior.float':{'priority':0}})
 if id not in neutral:comp['minecraft:behavior.nearest_attackable_target']={'priority':2,'must_see':True,'reselect_targets':True,'within_radius':a['FOLLOW_RANGE'],'entity_types':[{'filters':{'any_of':[filt('player'),filt('irongolem')]+([filt('villager')] if id in casters or id in ['swamp_zombie','crystal_zombie'] else [])},'max_dist':a['FOLLOW_RANGE']}]}
 if id=='ender_eye':comp['minecraft:behavior.nearest_attackable_target']={'priority':3,'entity_types':[{'filters':filt('endermite'),'max_dist':15}]}
 if id in casters:
  comp['minecraft:behavior.avoid_mob_type']={'priority':3,'entity_types':[{'filters':filt('player'),'max_dist':8,'walk_speed_multiplier':.6,'sprint_speed_multiplier':1}],'max_dist':8}
 elif id in ranged:pass
 elif id not in fly:comp['minecraft:behavior.melee_box_attack']={'priority':4,'track_target':True,'speed_multiplier':1}
 if id in ['glow_skeleton','swamp_zombie','crystal_zombie','demon_eye']:comp['minecraft:burns_in_daylight']={}
 if id in ['lava_squid','mother_lava_squid','wisp','soul','ancient_hero','ancient_hero_skull','desert_acolyte','desert_sorceress']:
  comp['minecraft:fire_immune']={};comp['minecraft:damage_sensor']={'triggers':[{'cause':'fall','deals_damage':'no'}]}
 if id=='ancient_hero':comp['minecraft:boss']={'name':m['name'],'hud_range':50,'should_darken_sky':False}
 groups={};events={}
 if id=='ancient_hero':
  groups['monsterplus:combat_melee']={'minecraft:behavior.melee_box_attack':comp.pop('minecraft:behavior.melee_box_attack')}
  events['minecraft:entity_spawned']={'add':{'component_groups':['monsterplus:combat_melee']}}
  events['monsterplus:combat_melee']={'add':{'component_groups':['monsterplus:combat_melee']},'set_property':{'monsterplus:ranged':False}}
  events['monsterplus:combat_ranged']={'remove':{'component_groups':['monsterplus:combat_melee']},'set_property':{'monsterplus:ranged':True}}
 if id in ranged:
  choices=[('bow',1),('stone_sword',1)] if id=='glow_skeleton' else [('bow',2),('wooden_sword',1),('empty',1)]
  for item,weight in choices:
   group={'minecraft:equipment':{'table':f'loot_tables/equipment/{id}_{item}.json'}}
   entry={'type':'empty'} if item=='empty' else {'type':'item','name':'minecraft:'+item}
   write(BP/f'loot_tables/equipment/{id}_{item}.json',{'pools':[{'rolls':1,'entries':[entry]}]})
   if item=='bow':group.update({'minecraft:shooter':{'def':'minecraft:arrow','sound':'bow'},'minecraft:behavior.ranged_attack':{'priority':4,'attack_interval_min':1.0,'attack_interval_max':3.0,'attack_radius':15.0}})
   else:group['minecraft:behavior.melee_box_attack']={'priority':4,'track_target':True,'speed_multiplier':1.2}
   groups['monsterplus:weapon_'+item]=group
  events['minecraft:entity_spawned']={'randomize':[{'weight':weight,'add':{'component_groups':['monsterplus:weapon_'+item]},'set_property':{'monsterplus:ranged':item=='bow'}} for item,weight in choices]}
 if id in ['swamp_zombie','ancient_hero']:
  comp['minecraft:equipment']={'table':f'loot_tables/equipment/{id}.json'}
  entries=[{'type':'item','name':'monsterplus:ancient_broken_sword'}] if id=='ancient_hero' else [{'type':'empty','weight':5}]+[{'type':'item','name':'minecraft:'+item,'weight':1} for item in ['wooden_sword','stone_sword','stone_shovel','wooden_axe','wooden_shovel']]
  write(BP/f'loot_tables/equipment/{id}.json',{'pools':[{'rolls':1,'entries':entries}]})
 if id in ['demon_eye','ender_eye','wisp','soul']:
  for i in range(31):
   factor=.5+i*.05;name='monsterplus:collision_'+str(i)
   groups[name]={'minecraft:collision_box':{'width':m['width']*factor,'height':m['height']*factor}}
   events[name]={'remove':{'component_groups':['monsterplus:collision_'+str(j) for j in range(31)]},'add':{'component_groups':[name]}}
  for tier,bonus,speed in [('small',0,.02),('normal',0,0),('large',4,0),('giant',8,0)]:
   name='monsterplus:size_'+tier;groups[name]={'minecraft:health':{'value':a['MAX_HEALTH']+bonus,'max':a['MAX_HEALTH']+bonus},'minecraft:movement':{'value':a['MOVEMENT_SPEED']+speed}}
   events[name]={'add':{'component_groups':[name]}}
 if id=='demon_eye':
  for v in range(6):groups['monsterplus:variant_'+str(v)]={'minecraft:variant':{'value':v},'minecraft:attack':{'damage':a['ATTACK_DAMAGE']+(2 if v==5 else 0)}}
  events['minecraft:entity_spawned']={'randomize':[{'weight':[8,6,4,2,1,3][v],'add':{'component_groups':['monsterplus:variant_'+str(v)]}} for v in range(6)]}
 for phase in range(4):
  groups[f'monsterplus:phase_{phase}']={'minecraft:movement':{'value':a['MOVEMENT_SPEED']+.01*phase},'minecraft:knockback_resistance':{'value':.6 if phase==0 else .3 if phase<3 else 0}}
  events[f'monsterplus:phase_{phase}']={'remove':{'component_groups':[f'monsterplus:phase_{i}' for i in range(4)]},'add':{'component_groups':[f'monsterplus:phase_{phase}']}}
 if (SRC/f'java_data/loot_table/entities/{id}.json').exists():comp['minecraft:loot']={'table':f'loot_tables/entities/{id}.json'}
 write(BP/f'entities/{id}.json',dict(format_version='1.21.90',**{'minecraft:entity':{'description':dict(identifier=key,is_spawnable=False,is_summonable=True,is_experimental=False,properties=props),'component_groups':groups,'components':comp,'events':events}}))
 sound='wisp' if id in ['wisp','soul'] else 'desert_sorceress' if id in ['desert_sorceress','desert_acolyte'] else None
 if sound:client_sounds[key]={'events':{ev:{'sound':f'monsterplus.entity.{sound}.{java}'} for ev,java in [('ambient','ambient'),('hurt','hurt'),('death','death')]}}
 if not sound:
  vanilla='drowned' if id=='swamp_zombie' else 'zombie' if id=='crystal_zombie' else 'evocation_illager' if id=='abyssologer' else 'squid' if id in ['lava_squid','mother_lava_squid'] else 'endermen' if id=='ender_eye' else 'phantom' if id in ['opalescent_eye','demon_eye'] else 'skeleton'
  client_sounds[key]={'events':{ev:{'sound':f'mob.{vanilla}.{ev}'} for ev in ['ambient','hurt','death']}}
 lang += [f'entity.{key}.name={m["name"]}',f'item.spawn_egg.entity.{key}.name=Spawn {m["name"]}']
 audit.append(dict(id=id,geometry=m['model'],cubes=sum(len(b['cubes']) for b in model['bones']),health=a['MAX_HEALTH'],scale=scale))
# Custom projectiles use actual Java textures; collision and ownership handled by native projectile component.
projectiles={'purple_fireball':('textures/item/fireball_purple',4,4),'curseflame_fireball':('textures/item/curseflame_powder',4,3),'soulflame_fireball':('textures/item/soulflame_powder',5,3),'spectral_skull_projectile':('textures/entities/spectral_skull',4,1),'flame':('textures/item/blaze_powder',1,1)}
for id,(texture,damage,frames) in projectiles.items():
 assert (RP/(texture+'.png')).is_file(),texture
 rc='controller.render.monsterplus.'+id
 if id=='spectral_skull_projectile':geo=geometry(models['SkullProjectileModel'],id)
 else:
  geo={'format_version':'1.12.0','minecraft:geometry':[{'description':{'identifier':'geometry.monsterplus.'+id,'texture_width':16,'texture_height':16*frames},'bones':[{'name':'body','pivot':[0,0,0],'cubes':[{'origin':[-4,-4,0],'size':[8,8,0],'uv':{'north':{'uv':[0,0],'uv_size':[16,16]},'south':{'uv':[0,0],'uv_size':[16,16]}}}]}]}]}
 write(RP/f'models/entity/{id}.geo.json',geo)
 desc={'identifier':'monsterplus:'+id,'materials':{'default':'entity_emissive_alpha'},'textures':{'default':texture},'geometry':{'default':'geometry.monsterplus.'+id},'render_controllers':[rc]}
 if id!='spectral_skull_projectile':desc.update({'animations':{'flying':'animation.actor.billboard'},'scripts':{'animate':['flying'],'scale':'0.8'}})
 write(RP/f'entity/{id}.entity.json',{'format_version':'1.10.0','minecraft:client_entity':{'description':desc}})
 render[rc]={'geometry':'Geometry.default','materials':[{'*':'Material.default'}],'textures':['Texture.default']}
 if frames>1:render[rc]['uv_anim']={'offset':[0,f'math.mod(math.floor(query.life_time * 20 / 6), {frames}) / {frames}'],'scale':[1,1]}
 write(BP/f'entities/{id}.json',{'format_version':'1.21.90','minecraft:entity':{'description':{'identifier':'monsterplus:'+id,'is_summonable':True,'is_spawnable':False},'components':{'minecraft:collision_box':{'width':.25,'height':.25},'minecraft:physics':{'has_gravity':False},'minecraft:projectile':{'power':1,'gravity':0,'inertia':1,'liquid_inertia':1,'on_hit':({'impact_damage':{'damage':damage,'knockback':True}} if id=='flame' else {'impact_damage':{'damage':damage,'knockback':True},'remove_on_hit':{}})},'minecraft:timer':{'time':6 if id=='spectral_skull_projectile' else 8,'looping':False,'time_down_event':{'event':'monsterplus:expire','target':'self'}}},'events':{'monsterplus:expire':{'add':{'component_groups':['monsterplus:expired']}}},'component_groups':{'monsterplus:expired':{'minecraft:instant_despawn':{}}}}})
render['controller.render.monsterplus.projectile']={'geometry':'Geometry.default','materials':[{'*':'Material.default'}],'textures':['Texture.default']}
# Crystal spike is rendered using the recovered 42-bone model, not vanilla evoker fangs.
write(RP/'models/entity/crystal_spikes.geo.json',geometry(models['CrystalSpikesModel'],'crystal_spikes'))
write(RP/'entity/crystal_spikes.entity.json',{'format_version':'1.10.0','minecraft:client_entity':{'description':{'identifier':'monsterplus:crystal_spikes','materials':{'default':'entity_alphablend'},'textures':{'default':'textures/entities/crystal_spike'},'geometry':{'default':'geometry.monsterplus.crystal_spikes'},'render_controllers':['controller.render.monsterplus.projectile'],'scripts':{'scale':'0.75'}}}})
write(BP/'entities/crystal_spikes.json',{'format_version':'1.21.90','minecraft:entity':{'description':{'identifier':'monsterplus:crystal_spikes','is_summonable':True,'is_spawnable':False},'components':{'minecraft:collision_box':{'width':.01,'height':.01},'minecraft:physics':{'has_gravity':False,'has_collision':False},'minecraft:timer':{'time':1.5,'looping':False,'time_down_event':{'event':'monsterplus:expire','target':'self'}}},'component_groups':{'monsterplus:expired':{'minecraft:instant_despawn':{}}},'events':{'monsterplus:expire':{'add':{'component_groups':['monsterplus:expired']}}}}})
write(RP/'render_controllers/monsterplus.render_controllers.json',{'format_version':'1.8.0','render_controllers':render})
write(RP/'animations/monsterplus.animation.json',{'format_version':'1.8.0','animations':animations})
# Convert original sound definitions; retain original OGG files byte-for-byte.
sounds={}
for k,v in load(SRC/'assets/sounds.json').items():
 files=['sounds/'+s.split(':',1)[-1] for s in v['sounds']]
 sounds['monsterplus.'+k]={'category':'hostile','sounds':files}
write(RP/'sounds/sound_definitions.json',{'format_version':'1.14.0','sound_definitions':sounds})
write(RP/'sounds.json',{'entity_sounds':{'entities':client_sounds}})
(RP/'texts').mkdir(exist_ok=True);(RP/'texts/en_US.lang').write_text('\n'.join(lang)+'\n');write(RP/'texts/languages.json',['en_US'])
# Convert all entity drops, keeping custom items available as materials. Equipment mechanics are outside mob scope.
items=set()
def convert_fn(f):
 name=f['function'].split(':')[-1]
 if name=='set_count':
  count=f['count'];return dict(function='set_count',count={k:v for k,v in count.items() if k in ['min','max']} if isinstance(count,dict) else count)
 if name=='enchanted_count_increase':return dict(function='looting_enchant',count=f.get('count',{'min':0,'max':1}))
 return None
for p in (SRC/'java_data/loot_table/entities').glob('*.json'):
 pools=[]
 for pool in load(p).get('pools',[]):
  entries=[]
  for entry in pool.get('entries',[]):
   if entry.get('type')!='minecraft:item':continue
   name=entry['name'];items.add(name) if name.startswith('monsterplus:') else None
   e=dict(type='item',name=name,weight=entry.get('weight',1));fns=[convert_fn(f) for f in entry.get('functions',[])];e['functions']=[f for f in fns if f]
   entries.append(e)
  q={'rolls':pool.get('rolls',1),'entries':entries};conditions=[]
  for c in pool.get('conditions',[]):
   typ=c['condition'].split(':')[-1]
   if typ=='random_chance_with_enchanted_bonus':conditions.append(dict(condition='random_chance_with_looting',chance=c['unenchanted_chance'],looting_multiplier=c['enchanted_chance'].get('per_level_above_first',0)))
   elif typ=='killed_by_player':conditions.append(dict(condition='killed_by_player'))
   elif typ=='random_chance':conditions.append(dict(condition='random_chance',chance=c['chance']))
   elif typ=='entity_properties':
    # Variant-specific drops are dispatched by the death handler.
    conditions.append(dict(condition='random_chance',chance=0))
   else:raise ValueError('Unknown loot condition '+typ)
  if conditions:q['conditions']=conditions
  variant_conditions=[c for c in pool.get('conditions',[]) if c['condition'].endswith('entity_properties')]
  if variant_conditions:
   import re
   variant=int(re.search(r'EyeType:(\d+)',variant_conditions[0]['predicate']['nbt'])[1])
   q['conditions']=[c for c in conditions if c.get('chance')!=0]
   write(BP/f'loot_tables/entities/demon_eye_variant_{variant}.json',{'pools':[q]})
  elif entries:pools.append(q)
 write(BP/f'loot_tables/entities/{p.name}',{'pools':pools})
atlas={}
for name in sorted(items):
 short=name.split(':')[1];texture=SRC/f'assets/textures/item/{short}.png'
 if not texture.exists():texture=SRC/f'assets/textures/items/{short}.png'
 if not texture.exists():
  model=load(SRC/f'item_models/{short}.json');path=model['textures']['layer0'].split(':')[-1];texture=SRC/('assets/textures/'+path+'.png')
 if not texture.exists():raise ValueError('Missing item texture '+name)
 dest='textures/monsterplus_items/'+short;(RP/(dest+'.png')).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(texture,RP/(dest+'.png'));atlas[short]={'textures':dest}
 write(BP/f'items/{short}.json',{'format_version':'1.21.90','minecraft:item':{'description':{'identifier':name,'menu_category':{'category':'items'}},'components':{'minecraft:icon':short,'minecraft:display_name':{'value':load(SRC/'lang.json').get('item.monsterplus.'+short,short.replace('_',' ').title())},'minecraft:max_stack_size':64}}})
# Explicit spawn items have their own inventory registration; no generated-egg lookup is required.
atlas['monsterplus_spawn_egg']={'textures':'textures/item/monsterplus_spawn_egg'}
for m in mobs:
 id=m['id'];name='monsterplus:'+id+'_spawn_egg'
 write(BP/f'items/{id}_spawn_egg.json',{'format_version':'1.21.90','minecraft:item':{'description':{'identifier':name,'menu_category':{'category':'nature'}},'components':{'minecraft:icon':{'textures':{'default':'monsterplus_spawn_egg'}},'minecraft:display_name':{'value':'Spawn '+m['name']},'minecraft:max_stack_size':64,'minecraft:entity_placer':{'entity':'monsterplus:'+id,'use_on':[],'dispense_on':[]}}}})
write(RP/'textures/item_texture.json',{'resource_pack_name':'monsterplus','texture_name':'atlas.items','texture_data':atlas})
# Translate biome filters and source weights; Java biome tags do not map one-to-one to Bedrock.
for p in (SRC/'java_data/neoforge/biome_modifier').glob('*.json'):
 id=p.stem;s=load(p)['spawners'];conditions={'minecraft:weight':{'default':s['weight']},'minecraft:herd':{'min_size':s['minCount'],'max_size':s['maxCount']},'minecraft:difficulty_filter':{'min':'easy','max':'hard'},'minecraft:distance_filter':{'min':24,'max':128}}
 biome={'test':'has_biome_tag','operator':'==','value':'overworld'}
 if id in ['lava_squid','mother_lava_squid','soul']:biome={'test':'has_biome_tag','operator':'==','value':'nether'}
 if id in ['desert_acolyte','desert_sorceress']:biome={'test':'has_biome_tag','operator':'==','value':'desert'}
 if id in ['swamp_zombie','wisp']:biome={'test':'has_biome_tag','operator':'==','value':'swamp'}
 if id=='overgrown_skeleton':biome={'any_of':[{'test':'has_biome_tag','operator':'==','value':v} for v in ['jungle','lush_caves']]}
 if id=='ender_eye':biome={'any_of':[{'test':'has_biome_tag','operator':'==','value':v} for v in ['overworld','the_end']]}
 if id in ['lava_squid','mother_lava_squid']:biome={'all_of':[biome,{'test':'has_biome_tag','operator':'!=','value':'soulsand_valley'},{'test':'has_biome_tag','operator':'!=','value':'warped_forest'}]}
 if id=='soul':biome={'test':'has_biome_tag','operator':'==','value':'soulsand_valley'}
 conditions['minecraft:biome_filter']=biome
 if id in ['lava_squid','mother_lava_squid']:conditions['minecraft:spawns_lava']={}
 else:conditions.update({'minecraft:spawns_on_surface':{},'minecraft:spawns_underground':{},'minecraft:brightness_filter':{'min':0,'max':7,'adjust_for_weather':True}})
 max_height={'ancient_hero':12,'crystal_zombie':40,'abyssologer':40,'spectral_skull':40,'glow_skeleton':40}.get(id)
 if max_height is not None:conditions['minecraft:height_filter']={'min':-64,'max':max_height}
 write(BP/f'spawn_rules/{id}.json',{'format_version':'1.8.0','minecraft:spawn_rules':{'description':{'identifier':'monsterplus:'+id,'population_control':'monster'},'conditions':[conditions]}})
gallery=BP/'functions/monsterplus/gallery.mcfunction';gallery.parent.mkdir(parents=True,exist_ok=True)
gallery.write_text('# Run in Creative in a disposable test world. Spawns all 18 source mob types.\n'+'\n'.join(f'summon monsterplus:{m["id"]} ~{(i%6)*5} ~2 ~{(i//6)*5}' for i,m in enumerate(mobs))+'\n')
eggs=BP/'functions/monsterplus/eggs.mcfunction'
eggs.write_text('# Give the executing player every generated Monster Plus spawn egg.\n'+'\n'.join(f'give @s monsterplus:{m["id"]}_spawn_egg 1' for m in mobs)+'\n')
status=BP/'functions/monsterplus/status.mcfunction'
status.write_text('tellraw @s {"rawtext":[{"text":"Monster Plus 0.1.2 loaded. Use /function monsterplus/eggs for all 18 eggs."}]}\n')
# Runtime data contains only source-derived values, with explicit Bedrock flags.
(BP/'scripts/data.js').write_text('export const mobs = '+json.dumps({m['id']:{**m,'flying':m['id'] in fly,'neutral':m['id'] in neutral} for m in mobs},indent=2)+';\n')
write(ROOT/'source/conversion-audit.json',audit)
dist=ROOT/'dist';dist.mkdir(exist_ok=True)
for name in ['MonsterPlus_BP','MonsterPlus_RP']:
 with zipfile.ZipFile(dist/(name+'.mcpack'),'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted((ROOT/'packs'/name).rglob('*')):
   if p.is_file():z.write(p,p.relative_to(ROOT/'packs'/name))
with zipfile.ZipFile(dist/'MonsterPlus-Bedrock-0.1.2.mcaddon','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((ROOT/'packs').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(ROOT/'packs'))
print('Built 18 mobs, 6 attack entities,',len(items),'drop items, 15 natural spawn rules')
