import {test} from 'node:test';
import assert from 'node:assert/strict';
import {phaseForHealth,skullInterval,spikePattern,nextSpell,normalized,length,onHitEffects,javaArmorDamage,eyeSize,fireWallPattern,eyeSteering} from '../packs/MonsterPlus_BP/scripts/combat.js';
test('Ancient Hero phase thresholds match the source, including large hits',()=>{
 assert.deepEqual([100,76,75,51,50,26,25,1].map(h=>phaseForHealth(h,100)),[0,0,1,1,2,2,3,3]);
});
test('skull attack accelerates through all phases',()=>{
 assert.deepEqual([0,1,2,3].map(p=>skullInterval(p,false)),[48,32,24,16]);
 assert.equal(skullInterval(0,true),16);
});
test('close crystal attack contains the three source rings and stagger times',()=>{
 const p=spikePattern({x:0,y:0,z:0},{x:2,y:0,z:0},1);
 assert.equal(p.length,30);
 assert.deepEqual([1,2,3].map(t=>p.filter(x=>x.delay===t).length),[5,10,15]);
 for(const v of p)assert.ok(Math.abs(Math.hypot(v.x,v.z)-v.delay*1.5)<1e-6);
});
test('line crystal attack follows target direction for 20 blocks',()=>{
 const p=spikePattern({x:0,y:0,z:0},{x:0,y:0,z:20},1,()=>.5);
 assert.equal(p.length,16);assert.equal(p.at(-1).z,20);assert.equal(p.at(-1).delay,15);
 assert.ok(Math.abs(p.at(-1).x)<1e-6);
});
test('targeted ring patterns preserve distinct source counts',()=>{
 const p={x:0,y:0,z:0},t={x:20,y:0,z:0};assert.equal(spikePattern(p,t,2).length,39);assert.equal(spikePattern(p,t,3).length,25);
});
test('summon cooldowns do not starve shorter spells',()=>{
 const cd={};let spell=nextSpell('abyssologer',0,cd);assert.equal(spell.id,'eyes');cd.eyes=720;
 spell=nextSpell('abyssologer',60,cd);assert.equal(spell.id,'skeletons');cd.skeletons=620;
 spell=nextSpell('abyssologer',120,cd);assert.equal(spell.id,'darkness');cd.darkness=840;
 spell=nextSpell('abyssologer',155,cd);assert.equal(spell.id,'spikes');cd.spikes=215;
 assert.equal(nextSpell('abyssologer',195,cd).id,'purple');assert.equal(nextSpell('abyssologer',720,cd).id,'eyes');
});
test('ineligible summons allow other attacks',()=>{
 assert.equal(nextSpell('abyssologer',0,{},id=>!['eyes','skeletons'].includes(id)).id,'darkness');
});
test('projectile vector math remains finite for coincident targets',()=>{
 assert.deepEqual(normalized({x:0,y:0,z:0}),{x:0,y:0,z:0});assert.ok(Math.abs(length(normalized({x:3,y:4,z:0}))-1)<1e-9);
});
test('poison duration is mob-specific, and glow has an explicit substitution',()=>{
 assert.equal(onHitEffects.swamp_zombie.ticks,500);assert.equal(onHitEffects.overgrown_skeleton.ticks,200);assert.equal(onHitEffects.glow_skeleton.effect,'glowing_marker');
});

test('hero armor uses the source reduction formula at each phase',()=>{assert.equal(javaArmorDamage(10,0,0),10);assert.ok(javaArmorDamage(10,12,4)<javaArmorDamage(10,6,2));assert.equal(spikePattern({x:0,y:0,z:0},{x:20,y:0,z:0},4).length,12);});

test('Demon Eye size probabilities retain all thirteen source outcomes',()=>{
 const tiers=Array.from({length:13},(_,r)=>eyeSize((()=>{let i=0;return ()=>i++===0?(r+.1)/13:.5;})()).tier);
 assert.equal(tiers.filter(t=>t==='small').length,2);assert.equal(tiers.filter(t=>t==='large').length,2);assert.equal(tiers.filter(t=>t==='giant').length,1);assert.equal(tiers.filter(t=>t==='normal').length,8);
});
test('Sorceress fire wall uses source ring counts and ranges',()=>{
 const o={x:0,y:0,z:0},t={x:20,y:0,z:0};
 assert.equal(fireWallPattern(o,{x:2,y:0,z:0},1).length,40);assert.equal(fireWallPattern(o,t,1).length,16);assert.equal(fireWallPattern(o,t,2).length,16);
 for(const p of fireWallPattern(o,t,2))assert.ok(Math.abs(Math.hypot(p.x-t.x,p.z-t.z)-4.5)<1e-8);
});
test('eye steering turns at most four degrees and smooths speed',()=>{
 const s=eyeSteering({x:0,y:0,z:0},{x:0,y:0,z:0},{x:10,y:3,z:0},0,.1);
 assert.equal(s.yaw,-4);assert.ok(length(s.velocity)<.1);assert.ok(Number.isFinite(s.pitch));
});
