import './smoke.js';
import {world,system,GameMode,EntityDamageCause} from '@minecraft/server';
import {mobs} from './data.js';
import {delta,length,normalized,scaled,plus,phaseForHealth,skullInterval,spikePattern,ring,nextSpell,onHitEffects,javaArmorDamage,eyeSize,fireWallPattern,eyeSteering} from './combat.js';

/** @typedef {import('@minecraft/server').Entity} Entity */
/** @typedef {{age:number,cooldowns:Record<string,number>,target?:Entity,cast?:any,lastMelee:number,sweepAt:number,sweepUntil:number,phase:number,birth:number,anchor?:any,ranged:boolean,rangedUntil:number}} State */
/** @type {Map<string,State>} */ const states=new Map();
const markers=new Map();
const homing=new Map();
const flames=new Map();
const warned=new Set();
const flightEyes=new Set(['opalescent_eye','demon_eye','ender_eye','spectral_skull','ancient_hero_skull']);
function report(where,error) {if(!warned.has(where)){warned.add(where);console.warn(`[MonsterPlus] ${where}: ${error}`);}}
function idOf(e) {return e.typeId.startsWith('monsterplus:')?e.typeId.slice(12):'';}
function valid(e) {return e?.isValid&&e.getComponent('minecraft:health')?.currentValue>0;}
function state(e) {
 let s=states.get(e.id);
 if(!s){initialize(e);s={age:0,cooldowns:{teleport:120},lastMelee:0,sweepAt:10,sweepUntil:0,phase:Number(e.getProperty('monsterplus:phase')??0),birth:0,ranged:false,rangedUntil:240};states.set(e.id,s);}
 return s;
}
function initialize(e) {
 if(e.getDynamicProperty('monsterplus:initialized'))return;
 const id=idOf(e);
 if(id==='demon_eye'||id==='ender_eye'){
  const size=eyeSize();e.setProperty('monsterplus:body_scale',size.scale);e.setProperty('monsterplus:iris_scale',.9+.35*Math.random());
  e.triggerEvent('monsterplus:size_'+size.tier);e.triggerEvent('monsterplus:collision_'+Math.round((size.scale-.5)*20));
 }else if(id==='wisp'||id==='soul'){
  const scale=.5+Math.random();e.setProperty('monsterplus:body_scale',scale);e.triggerEvent('monsterplus:collision_'+Math.round((scale-.5)*20));
 }
 e.setDynamicProperty('monsterplus:initialized',true);
}
function enderTeleport(e,target) {
 const p=e.location;let destination;
 for(let i=0;i<64;i++){
  if(target){const away=normalized(delta(target.getHeadLocation(),e.getHeadLocation()));destination={x:p.x+(Math.random()-.5)*8-away.x*16,y:p.y+Math.floor(Math.random()*16)-8-away.y*16,z:p.z+(Math.random()-.5)*8-away.z*16};}
  else destination=plus(p,{x:(Math.random()-.5)*64,y:Math.floor(Math.random()*64)-32,z:(Math.random()-.5)*64});
  if(destination.y<=e.dimension.heightRange.min||destination.y>=e.dimension.heightRange.max-2)continue;
  let groundPos;
  try{const hit=e.dimension.getBlockFromRay(destination,{x:0,y:-1,z:0},{maxDistance:destination.y-e.dimension.heightRange.min-1,includeLiquidBlocks:true});if(hit&&hit.block.isSolid)groundPos={x:destination.x,y:hit.block.location.y+1,z:destination.z};}catch(_error){continue;}
  if(groundPos&&e.tryTeleport(groundPos,{checkForBlocks:true})){e.dimension.playSound('mob.endermen.portal',groundPos);return true;}
 }
 return false;
}
function activePlayer(e) {return e.typeId!=='minecraft:player'||![GameMode.Creative,GameMode.Spectator].includes(/** @type {import('@minecraft/server').Player} */(e).getGameMode());}
function allied(a,b) {
 const ai=idOf(a),bi=idOf(b),owner=a.getDynamicProperty('monsterplus:owner');
 if(owner===b.id||b.getDynamicProperty('monsterplus:owner')===a.id)return true;
 if(owner&&owner===b.getDynamicProperty('monsterplus:owner'))return true;
 if(ai===bi&&ai)return true;
 if(['lava_squid','mother_lava_squid'].includes(ai)&&['lava_squid','mother_lava_squid'].includes(bi))return true;
 if(['ancient_hero','ancient_hero_skull'].includes(ai)&&['ancient_hero','ancient_hero_skull'].includes(bi))return true;
 return false;
}
function sees(e,target) {
 const p=e.getHeadLocation(),d=delta(p,target.getHeadLocation());
 const hit=e.dimension.getBlockFromRay(p,normalized(d),{maxDistance:length(d),includeLiquidBlocks:false,includePassableBlocks:false});
 return !hit;
}
function targetFor(e,s,data) {
 const ownerId=e.getDynamicProperty('monsterplus:owner');
 if(typeof ownerId==='string'){
  const owner=world.getEntity(ownerId),t=owner&&states.get(owner.id)?.target;
  if(valid(t)&&!allied(e,t))return t;
 }
 if(valid(s.target)&&activePlayer(s.target)&&!allied(e,s.target)&&length(delta(e.location,s.target.location))<data.attributes.FOLLOW_RANGE*1.5)return s.target;
 s.target=undefined;
 const nearby=e.dimension.getEntities({location:e.location,maxDistance:data.attributes.FOLLOW_RANGE,excludeTypes:['minecraft:item','minecraft:xp_orb']});
 let best=Infinity;
 for(const t of nearby){
  if(t.id===e.id||!valid(t)||!activePlayer(t)||allied(e,t))continue;
  const allowed=data.neutral?(data.id==='ender_eye'&&t.typeId==='minecraft:endermite'):['minecraft:player','minecraft:iron_golem',...(['abyssologer','desert_acolyte','desert_sorceress','swamp_zombie','crystal_zombie'].includes(data.id)?['minecraft:villager','minecraft:villager_v2']:[])].includes(t.typeId);
  if(!allowed)continue;
  const distance=length(delta(e.location,t.location));
  if(distance<best&&sees(e,t)){best=distance;s.target=t;}
 }
 return s.target;
}
function setVelocity(e,v) {const old=e.getVelocity();e.applyImpulse(delta(old,v));}
function damage(owner,target,amount) {
 if(!valid(target)||allied(owner,target))return;
 target.applyDamage(amount,{cause:EntityDamageCause.magic,damagingEntity:owner});
}
function shoot(owner,target,type,speed=0.7,offset={x:0,y:1.5,z:0},jitter=0) {
 if(!owner.isValid||!valid(target))return;
 const p=plus(owner.location,offset),t=target.getHeadLocation();
 const aim=delta(p,t);aim.x+=(Math.random()-.5)*jitter;aim.z+=(Math.random()-.5)*jitter;
 const projectile=owner.dimension.spawnEntity(type,p),component=projectile.getComponent('minecraft:projectile');
 if(!component){projectile.remove();throw new Error(type+' missing projectile component');}
 component.owner=owner;component.shoot(scaled(normalized(aim),type==='monsterplus:spectral_skull_projectile'?.05:speed));
 if(type==='monsterplus:flame'){flames.set(projectile.id,{projectile,age:0,lifetime:idOf(owner)==='desert_sorceress'?18:15});projectile.setDynamicProperty('monsterplus:damage',idOf(owner)==='desert_sorceress'?2:1);}
 if(type==='monsterplus:spectral_skull_projectile')homing.set(projectile.id,{projectile,target,until:system.currentTick+120});
}
function ground(dim,p,minY) {
 const range=dim.heightRange;
 for(let y=Math.min(Math.floor(p.y+1),range.max-2);y>=Math.max(minY,range.min+1);y--){
  const b=dim.getBlock({x:Math.floor(p.x),y:y-1,z:Math.floor(p.z)}),space=dim.getBlock({x:Math.floor(p.x),y,z:Math.floor(p.z)});
  if(b?.isSolid&&!space?.isSolid)return {x:p.x,y,z:p.z};
 }
 return undefined;
}
function spike(owner,p,delay,damageAmount,minY) {
 const dim=owner.dimension,pos=ground(dim,p,minY);if(!pos)return;
 dim.spawnParticle('minecraft:dragon_breath_trail',plus(pos,{x:0,y:.1,z:0}));
 system.runTimeout(()=>{
  if(!owner.isValid)return;
  dim.spawnEntity('monsterplus:crystal_spikes',pos);
  for(const target of dim.getEntities({location:plus(pos,{x:0,y:.5,z:0}),maxDistance:1.15}))damage(owner,target,damageAmount);
 },Math.max(1,delay));
}
function summon(owner,type,count,lifetime) {
 for(let i=0;i<count;i++){
  const position=plus(owner.location,{x:Math.random()*4-2,y:1,z:Math.random()*4-2});
  const child=owner.dimension.spawnEntity('monsterplus:'+type,position);
  child.setDynamicProperty('monsterplus:owner',owner.id);
  if(lifetime)child.setDynamicProperty('monsterplus:expires',system.currentTick+600+Math.floor(Math.random()*1800));
 }
}
function castStart(e,s,spell) {
 e.setProperty('monsterplus:casting',true);s.cooldowns[spell.id]=s.age+spell.cooldown;
 s.cast={...spell,start:s.age,fired:false};
 e.dimension.playSound(idOf(e)==='abyssologer'?'mob.evocation_illager.prepare_attack':'monsterplus.entity.desert_sorceress.cast',e.location);
}
function performSpell(e,s,target) {
 const c=s.cast,elapsed=s.age-c.start;
 if(elapsed<c.warmup)return;
 const p=e.location,t=target.location,first=!c.fired;c.fired=true;
 if(c.id==='breath'||c.id==='barrage'){
  if(elapsed<c.warmup+c.duration&&(elapsed-c.warmup)%3===0)for(let i=0;i<(c.id==='breath'?3:1);i++)shoot(e,target,c.id==='breath'?'monsterplus:flame':'minecraft:small_fireball',c.id==='breath'?.1:.8,{x:0,y:c.id==='breath'?2.5:3.5,z:0},1.5);
 }else if(first){
  if(c.id==='eyes'||c.id==='skeletons'){
   const type=c.id==='eyes'?'opalescent_eye':'spectral_skeleton';
   const count=e.dimension.getEntities({type:'monsterplus:'+type,location:p,maxDistance:16}).filter(x=>x.getDynamicProperty('monsterplus:owner')===e.id).length;
   if(count<(type==='opalescent_eye'?6:5))summon(e,type,type==='opalescent_eye'?3:2,true);
  }else if(c.id==='darkness')target.addEffect('darkness',700,{showParticles:true});
  else if(c.id==='spikes')for(const pos of spikePattern(p,t,1+Math.floor(Math.random()*4)))spike(e,pos,25+pos.delay,4,Math.floor(Math.min(p.y,t.y))-1);
  else if(c.id==='fire_wall'){
   const points=fireWallPattern(p,t,Math.random()<.5?1:2);
   for(const pos of points)system.runTimeout(()=>{
    if(!e.isValid)return;
    const gp=ground(e.dimension,pos,Math.floor(Math.min(p.y,t.y))-1);if(!gp)return;
    // The Java fire spawner places real fire after four warmup ticks.
    if(world.gameRules.mobGriefing){const block=e.dimension.getBlock(gp);if(block?.isAir)block.setType('minecraft:fire');}
    e.dimension.spawnParticle('minecraft:basic_flame_particle',gp);
   },pos.delay+4);
  }else shoot(e,target,c.id==='purple'?'monsterplus:purple_fireball':c.id==='large_fireball'?'minecraft:fireball':'minecraft:small_fireball',.65,{x:0,y:2.5,z:0});
 }
 if(elapsed>=(['breath','barrage'].includes(c.id)?c.warmup+c.duration:c.duration)){s.cast=undefined;e.setProperty('monsterplus:casting',false);}
}
function flight(e,s,target,id,data) {
 const p=e.location;
 if(!target){
  if(!s.anchor||s.age%100===0)s.anchor=plus(p,{x:Math.random()*8-4,y:Math.random()*4-2,z:Math.random()*8-4});
  setVelocity(e,scaled(normalized(delta(p,s.anchor)),.06));return;
 }
 if(flightEyes.has(id)){
  if(s.age>=s.sweepAt){s.sweepUntil=s.age+70;s.sweepAt=s.age+160+Math.floor(Math.random()*80);}
  const sweeping=s.age<s.sweepUntil;
  const height=id==='spectral_skull'?3:id==='ancient_hero_skull'?10:25;
  const goal=sweeping?target.getHeadLocation():plus(target.location,{x:Math.cos(s.age*.025)*6,y:height,z:Math.sin(s.age*.025)*6});
  const steer=eyeSteering(p,e.getVelocity(),goal,s.heading??e.getRotation().y,s.speed??.1);s.heading=steer.yaw;s.speed=steer.speed;setVelocity(e,steer.velocity);e.setRotation({x:steer.pitch,y:steer.yaw});
  if(sweeping&&length(delta(p,target.getHeadLocation()))<1.5&&s.age-s.lastMelee>=20){damage(e,target,data.attributes.ATTACK_DAMAGE+(id==='demon_eye'&&e.getComponent('minecraft:variant')?.value===5?2:0));s.lastMelee=s.age;s.sweepUntil=0;}
  if(id==='ancient_hero_skull'&&s.age%40===0&&sees(e,target))shoot(e,target,'monsterplus:spectral_skull_projectile',.65,{x:0,y:.4,z:0});
 }else{
  // Lava squids, wisps and souls use floating ranged combat and retreat when approached.
  const v=delta(p,target.location),dist=length(v);let goal=plus(target.location,{x:Math.cos(s.age*.03)*6,y:2,z:Math.sin(s.age*.03)*6});
  if(dist<4)goal=plus(p,scaled(normalized(v),-4));
  setVelocity(e,scaled(normalized(delta(p,goal)),.1));
  if(dist<2&&s.age-s.lastMelee>=20){damage(e,target,data.attributes.ATTACK_DAMAGE);s.lastMelee=s.age;}
  const cycle=s.age%100;
  if(cycle===60||cycle===66||cycle===72){
   const type=id==='wisp'?'monsterplus:curseflame_fireball':id==='soul'?'monsterplus:soulflame_fireball':'minecraft:small_fireball';
   shoot(e,target,type,.6,{x:0,y:.5,z:0},1);
  }
  if(id==='mother_lava_squid'&&s.age%120===0){
   shoot(e,target,'minecraft:fireball',.5,{x:0,y:2,z:0});
   for(let i=0;i<12;i++)system.runTimeout(()=>{if(e.isValid&&valid(target))shoot(e,target,'minecraft:small_fireball',.65,{x:Math.cos(i*Math.PI/6)*2,y:2+Math.sin(i*Math.PI/6),z:Math.sin(i*Math.PI/6)*2},4);},i*2+1);
  }
 }
 if(id==='ender_eye'&&s.age>=s.cooldowns.teleport&&Math.random()<2/13){if(enderTeleport(e,target))s.cooldowns.teleport=s.age+120;}
}
function hero(e,s,target) {
 const health=e.getComponent('minecraft:health');if(!health)return;
 const phase=phaseForHealth(health.currentValue,health.effectiveMax);
 if(phase>s.phase){
  for(let next=s.phase+1;next<=phase;next++){
   if(next===2){summon(e,'ancient_hero_skull',1,false);if(target)for(let i=0;i<6;i++)shoot(e,target,'monsterplus:spectral_skull_projectile',.7,{x:0,y:2,z:0},2);}
   if(target)shoot(e,target,'monsterplus:spectral_skull_projectile');
  }
  s.phase=phase;e.setProperty('monsterplus:phase',phase);e.triggerEvent('monsterplus:phase_'+phase);e.dimension.playSound('random.break',e.location);
 }
 if(phase>=2&&s.ranged){s.ranged=false;e.triggerEvent('monsterplus:combat_melee');}
 if(target&&phase<2&&s.age>=s.rangedUntil){
  const distance=length(delta(e.location,target.location));
  const change=Math.floor(Math.random()*13)<=4||(Math.floor(Math.random()*13)<=7&&(s.ranged?distance<=4:distance>=6));
  if(change){s.ranged=!s.ranged;e.triggerEvent(s.ranged?'monsterplus:combat_ranged':'monsterplus:combat_melee');}
  s.rangedUntil=s.age+(s.ranged?160:240);
 }
 if(target&&s.ranged){
  const toward=normalized(delta(e.location,target.location)),distance=length(delta(e.location,target.location));
  const direction=Math.floor(s.age/40)%2===0?1:-1,radial=distance<5?-.2:distance>15?.2:0;
  const velocity=e.getVelocity();setVelocity(e,{x:toward.x*radial+toward.z*.15*direction,y:velocity.y,z:toward.z*radial-toward.x*.15*direction});
 }
 if(target&&s.age%skullInterval(phase,s.ranged)===0&&sees(e,target))shoot(e,target,'monsterplus:spectral_skull_projectile',.7,{x:0,y:1.8,z:0});
}
function tickMob(e) {
 const id=idOf(e),data=mobs[id];if(!data)return;
 const expires=e.getDynamicProperty('monsterplus:expires');if(typeof expires==='number'&&system.currentTick>=expires){e.remove();states.delete(e.id);return;}
 const s=state(e);s.age++;
 if(id==='ender_eye'&&e.isInWater)e.applyDamage(1,{cause:EntityDamageCause.drowning});
 if(id==='mother_lava_squid'&&++s.birth>=400){s.birth=0;summon(e,'lava_squid',1,false);}
 const target=targetFor(e,s,data);
 if(id==='ancient_hero')hero(e,s,target);
 if(data.flying)flight(e,s,target,id,data);
 if(!target){if(s.cast){s.cast=undefined;e.setProperty('monsterplus:casting',false);}return;}
 if(id==='crystal_zombie'&&s.age%60===0&&sees(e,target))for(let i=0;i<3;i++)spike(e,plus(target.location,{x:Math.random(),y:0,z:Math.random()}),15,3,Math.floor(Math.min(e.location.y,target.location.y))-1);
 if(['abyssologer','desert_acolyte','desert_sorceress'].includes(id)){
  if(!s.cast&&sees(e,target)){
   const spell=nextSpell(id,s.age,s.cooldowns,spell=>{
    if(spell==='breath')return length(delta(e.location,target.location))<10;
    if(spell==='darkness')return !target.getEffect('darkness');
    if(!['eyes','skeletons'].includes(spell))return true;
    const type=spell==='eyes'?'opalescent_eye':'spectral_skeleton';
    const count=e.dimension.getEntities({type:'monsterplus:'+type,location:e.location,maxDistance:16}).length;
    return 1+Math.floor(Math.random()*(spell==='eyes'?6:5))>count;
   });if(spell)castStart(e,s,spell);
  }
  if(s.cast)performSpell(e,s,target);
 }
}
// Stable API 2.0 loads on current Bedrock; use the newer pre-damage hook only when exposed.
const beforeHurt=/** @type {any} */ (world.beforeEvents).entityHurt;
beforeHurt?.subscribe(event=>{
 const victim=event.hurtEntity,source=event.damageSource.damagingEntity;
 const projectile=event.damageSource.damagingProjectile;
 if(projectile?.typeId==='monsterplus:flame')event.damage=Number(projectile.getDynamicProperty('monsterplus:damage')??1);
 if(source&&idOf(source)&&allied(source,victim)){event.cancel=true;return;}
 if(idOf(victim)==='ancient_hero'){
  const phase=Number(victim.getProperty('monsterplus:phase')??0);
  const cause=event.damageSource.cause;
  if(cause===EntityDamageCause.wither){event.cancel=true;return;}
  if([EntityDamageCause.entityAttack,EntityDamageCause.projectile,EntityDamageCause.entityExplosion,EntityDamageCause.blockExplosion].includes(cause))event.damage=javaArmorDamage(event.damage,phase===0?12:phase<3?6:0,phase===0?4:phase<3?2:0);
 }
});
world.afterEvents.entityHurt.subscribe(event=>{
 const source=event.damageSource.damagingEntity,victim=event.hurtEntity;
 if(idOf(victim)==='ender_eye')system.run(()=>{if(victim.isValid)enderTeleport(victim,undefined);});
 if(!source)return;
 if(mobs[idOf(victim)]&&valid(source)&&!allied(victim,source)){
  state(victim).target=source;
  const family=idOf(victim);
  if(['lava_squid','mother_lava_squid','wisp','soul'].includes(family))for(const ally of victim.dimension.getEntities({type:victim.typeId,location:victim.location,maxDistance:16}))state(ally).target=source;
 }
 const effect=onHitEffects[idOf(source)];
 if(effect&&valid(victim)){
  if(effect.effect==='glowing_marker')markers.set(victim.id,system.currentTick+effect.ticks);
  else victim.addEffect(effect.effect,effect.ticks,{showParticles:true});
 }
});
world.afterEvents.projectileHitEntity.subscribe(event=>{
 const hit=event.getEntityHit().entity;
 if(!valid(hit))return;
 const id=idOf(event.projectile);
 if(id==='curseflame_fireball')hit.setOnFire(5,true);
 if(id==='soulflame_fireball')hit.setOnFire(6,true);
 if(id==='purple_fireball')hit.setOnFire(4,true);
 if(id==='flame')hit.setOnFire(5,true);
});
world.afterEvents.projectileHitBlock.subscribe(event=>{if(idOf(event.projectile)==='flame'&&event.projectile.isValid)event.projectile.remove();});
world.afterEvents.entityDie.subscribe(event=>{
 const e=event.deadEntity;states.delete(e.id);markers.delete(e.id);
 if(idOf(e)==='demon_eye'){
  const variant=e.getComponent('minecraft:variant')?.value??0,p=e.location,dim=e.dimension;
  system.run(()=>{try{dim.runCommand(`loot spawn ${p.x} ${p.y} ${p.z} loot "entities/demon_eye_variant_${variant}"`);}catch(error){report('variant loot',error);}});
 }
});
world.afterEvents.entityRemove.subscribe(event=>states.delete(event.removedEntityId));
system.runInterval(()=>{
 for(const name of ['overworld','nether','the_end']){
  const dim=world.getDimension(name);
  for(const e of dim.getEntities({families:['monsterplus']})){
   try{tickMob(e);}catch(error){report(idOf(e),error);}
  }
 }
 for(const [id,f] of flames){
  if(!f.projectile.isValid){flames.delete(id);continue;}
  if(++f.age>=f.lifetime){f.projectile.remove();flames.delete(id);continue;}
  const velocity=f.projectile.getVelocity();setVelocity(f.projectile,plus(scaled(plus(velocity,scaled(normalized(velocity),.1)),.95),{x:0,y:-.0001*f.age*f.age,z:0}));
  f.projectile.dimension.spawnParticle('minecraft:basic_flame_particle',f.projectile.location);
 }
 for(const [id,h] of homing){
  if(!h.projectile.isValid||system.currentTick>=h.until){homing.delete(id);continue;}
  if(!valid(h.target))continue;
  const current=h.projectile.getVelocity(),aim=scaled(normalized(delta(h.projectile.location,h.target.getHeadLocation())),length(current));
  const steered=plus(current,scaled(delta(current,aim),.075));setVelocity(h.projectile,scaled(plus(steered,scaled(normalized(steered),.05)),.95));
 }
 if(system.currentTick%10===0)for(const [id,until] of markers){
  const e=world.getEntity(id);
  if(!e?.isValid||system.currentTick>=until){markers.delete(id);continue;}
  try{e.dimension.spawnParticle('minecraft:totem_particle',e.getHeadLocation());}catch(error){report('glowing marker',error);}
 }
},1);
console.warn('[MonsterPlus] Loaded 18 mob types. Port candidate: see VALIDATION.md for runtime verification status.');
