import {world,system,ItemStack,ItemTypes,BlockPermutation} from '@minecraft/server';
const IDS = __MOB_IDS__;
let active,spawned=new Set(),running=false;
world.afterEvents.entitySpawn.subscribe(({entity})=>{
 if(running&&active&&entity.typeId==='monsterplus:'+active&&entity.location.z>25){spawned.add(active);}
});
system.afterEvents.scriptEventReceive.subscribe(event=>{
 if(event.id!=='mobports:eggs'||running)return;
 running=true;
 const dim=world.getDimension('overworld');
 const results=[];
 const fail=error=>{running=false;console.error('MP_EGG_TEST_FAILURE '+String(error));};
 try{
  dim.runCommand('gamerule doMobSpawning false');
  dim.runCommand('time set midnight');
  dim.runCommand('tickingarea add circle 40 5 32 4 mp_egg_native');
  system.runTimeout(()=>{
   try{
    dim.runCommand('fill -8 4 26 96 4 44 stone');
    let index=0;
    function next(){
     if(index===IDS.length){
      running=false;console.warn('MP_EGG_TEST_RESULT '+JSON.stringify({engine:'1.26.52.3',passed:results.length,total:IDS.length,results}));return;
     }
     active=IDS[index];const x=index*5;
     const itemId='monsterplus:'+active+'_spawn_egg';
     if(!ItemTypes.get(itemId))throw Error('Item not registered: '+itemId);
     const block=dim.getBlock({x,y:5,z:32});
     block.setPermutation(BlockPermutation.resolve('minecraft:dispenser',{facing_direction:2}));
     block.getComponent('minecraft:inventory').container.setItem(0,new ItemStack(itemId,1));
     dim.getBlock({x:x+1,y:5,z:32}).setType('minecraft:redstone_block');
     const expected=active;
     system.runTimeout(()=>{
      try{
       if(!spawned.has(expected))throw Error('Dispenser egg did not create '+expected);
       const slot=block.getComponent('minecraft:inventory').container.getItem(0);
       if(slot)throw Error('Egg not consumed for '+expected);
       results.push({id:expected,itemRegistered:true,eggConsumed:true,mobSpawned:true});
       console.warn('MP_EGG_PASS '+expected);
       index++;next();
      }catch(error){fail(error);}
     },12);
    }
    next();
   }catch(error){fail(error);}
  },40);
 }catch(error){fail(error);}
});
