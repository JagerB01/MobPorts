// This exercises real main.js with a minimal API double; it does not emulate Bedrock AI/rendering.
import assert from 'node:assert/strict';
import {world,ticks,entities} from './minecraft-stub.mjs';
import {mobs} from '../packs/MonsterPlus_BP/scripts/data.js';
const warnings=[];const oldWarn=console.warn;console.warn=(...args)=>{if(!args.join(' ').includes('Loaded 18 mob types'))warnings.push(args.join(' '));};
await import('../packs/MonsterPlus_BP/scripts/main.js');
const dim=world.getDimension('overworld'),spawned={};
let i=0;
for(const id of Object.keys(mobs)){
 const p={x:i++*120,y:0,z:0},mob=dim.spawnEntity('monsterplus:'+id,p),player=dim.spawnEntity('minecraft:player',{...p,z:8});spawned[id]=mob;player.health.currentValue=100000; // Durable target keeps long spell cycles observable.
 world.afterEvents.entityHurt.emit({hurtEntity:mob,damageSource:{damagingEntity:player},damage:1});
}
ticks(450);
assert.deepEqual(warnings,[],'Runtime scripts must not swallow an API failure');
assert.ok([...entities.values()].some(e=>e.typeId==='monsterplus:purple_fireball'&&e.shot));
assert.ok([...entities.values()].some(e=>e.typeId==='monsterplus:crystal_spikes'));
const mother=spawned.mother_lava_squid;
assert.ok([...entities.values()].some(e=>e.typeId==='monsterplus:lava_squid'&&e.dynamic['monsterplus:owner']===mother.id),'mother births a lava squid after 400 ticks');
const hero=spawned.ancient_hero;
hero.health.currentValue=20;ticks(1);
assert.equal(hero.properties['monsterplus:phase'],3,'a large hit traverses all hero phases');
assert.equal([...entities.values()].filter(e=>e.typeId==='monsterplus:ancient_hero_skull'&&e.dynamic['monsterplus:owner']===hero.id).length,1,'phase two summons exactly one owned skull');
const friendly={hurtEntity:hero,damageSource:{damagingEntity:hero},damage:8,cancel:false};if(world.beforeEvents.entityHurt){world.beforeEvents.entityHurt.emit(friendly);assert.equal(friendly.cancel,true);}
const player=dim.spawnEntity('minecraft:player',{x:0,y:0,z:0});
world.afterEvents.entityHurt.emit({hurtEntity:player,damageSource:{damagingEntity:spawned.swamp_zombie},damage:2});assert.equal(player.effects.poison.ticks,500);
world.afterEvents.entityHurt.emit({hurtEntity:player,damageSource:{damagingEntity:spawned.overgrown_skeleton},damage:1});assert.equal(player.effects.poison.ticks,200);
const eye=spawned.demon_eye;world.afterEvents.entityDie.emit({deadEntity:eye});ticks(1);assert.ok(dim.commands.some(c=>c.includes('demon_eye_variant_0')));
assert.deepEqual(warnings,[]);
console.warn=oldWarn;console.log('PASS: simulated API smoke — all 18 mob controllers, attacks, ownership, hero phases, birth, poison, variant loot');
