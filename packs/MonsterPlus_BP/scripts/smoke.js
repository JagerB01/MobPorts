import {world,system} from '@minecraft/server';
import {mobs} from './data.js';
// Explicit in-engine registration smoke. Run /scriptevent monsterplus:smoke in a test world.
system.afterEvents.scriptEventReceive.subscribe(event=>{
 if(event.id!=='monsterplus:smoke')return;
 const player=event.sourceEntity;if(player?.typeId!=='minecraft:player')return;
 const p=/** @type {import('@minecraft/server').Player} */(player),created=[];let passed=0;
 try{
  for(const [id,data] of Object.entries(mobs)){
   const e=p.dimension.spawnEntity('monsterplus:'+id,{x:p.location.x+48,y:p.location.y+8,z:p.location.z});created.push(e);
   const hp=e.getComponent('minecraft:health');
   if(!hp||hp.currentValue!==data.attributes.MAX_HEALTH)throw Error(id+': source health mismatch');
   if(e.getProperty('monsterplus:phase')!==0)throw Error(id+': phase property missing');
   passed++;
  }
  p.sendMessage(`[MonsterPlus] PASS: ${passed}/18 mob registrations, health components and phase properties. Visuals and combat still require observation.`);
 }catch(error){p.sendMessage(`[MonsterPlus] FAIL after ${passed}/18: ${error}`);}
 finally{for(const e of created)if(e.isValid)e.remove();}
});
