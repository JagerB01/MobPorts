import {mobs} from '../packs/MonsterPlus_BP/scripts/data.js';
class Signal{handlers=[];subscribe(h){this.handlers.push(h);}emit(e){for(const h of this.handlers)h(e);}}
let counter=0;const entities=new Map(),dimensions=new Map(),timeouts=[];let interval;
export const GameMode={Creative:'creative',Spectator:'spectator',Survival:'survival'};
export const EntityDamageCause={magic:'magic',entityAttack:'entityAttack',projectile:'projectile',wither:'wither',entityExplosion:'entityExplosion',blockExplosion:'blockExplosion'};
export class MockEntity{
 constructor(type,dimension,p){this.typeId=type;this.dimension=dimension;this.location={...p};this.id='entity'+ ++counter;this.isValid=true;this.properties={};this.dynamic={};this.velocity={x:0,y:0,z:0};this.health={currentValue:mobs[type.slice(12)]?.attributes.MAX_HEALTH??20,effectiveMax:mobs[type.slice(12)]?.attributes.MAX_HEALTH??20};this.health.setCurrentValue=v=>this.health.currentValue=v;entities.set(this.id,this);}
 getComponent(id){
  if(id==='minecraft:health')return this.health;
  if(id==='minecraft:variant')return {value:0};
  if(id==='minecraft:projectile')return this.projectile??= {owner:undefined,shoot:v=>{this.velocity=v;this.shot=true;}};
 }
 getProperty(k){return this.properties[k]??0;}setProperty(k,v){this.properties[k]=v;}
 getDynamicProperty(k){return this.dynamic[k];}setDynamicProperty(k,v){this.dynamic[k]=v;}
 getRotation(){return this.rotation??{x:0,y:0};}setRotation(r){this.rotation=r;}getVelocity(){return this.velocity;}applyImpulse(v){for(const k of ['x','y','z'])this.velocity[k]+=v[k];}
 getHeadLocation(){return {...this.location,y:this.location.y+1};}
 getGameMode(){return GameMode.Survival;}getEffect(name){return this.effects?.[name];}
 addEffect(name,ticks){this.effects??={};this.effects[name]={ticks};}
 setOnFire(seconds){this.fire=seconds;}
 applyDamage(amount,options){this.health.currentValue-=amount;}
 remove(){this.isValid=false;entities.delete(this.id);}
 tryTeleport(p){this.location={...p};return true;}
 triggerEvent(name){this.events??=[];this.events.push(name);}
}
class Dimension{
 constructor(id){this.id=id;this.heightRange={min:-64,max:320};this.commands=[];this.sounds=[];}
 spawnEntity(type,p){return new MockEntity(type,this,p);}
 getEntities(q={}){return [...entities.values()].filter(e=>e.dimension===this&&e.isValid&&(!q.type||e.typeId===q.type)&&(!q.families||e.typeId.startsWith('monsterplus:')&&!!mobs[e.typeId.slice(12)])&&(!q.excludeTypes||!q.excludeTypes.includes(e.typeId))&&(!q.location||Math.hypot(e.location.x-q.location.x,e.location.y-q.location.y,e.location.z-q.location.z)<=(q.maxDistance??Infinity)));}
 getBlockFromRay(){return undefined;}getBlock(p){return {isSolid:p.y<0};}
 spawnParticle(){}playSound(s){this.sounds.push(s);}runCommand(s){this.commands.push(s);}
}
export const world={gameRules:{mobGriefing:true},afterEvents:{entityHurt:new Signal(),projectileHitEntity:new Signal(),projectileHitBlock:new Signal(),entityDie:new Signal(),entityRemove:new Signal()},beforeEvents:{entityHurt:new Signal()},getEntity:id=>entities.get(id),getDimension:id=>{if(!dimensions.has(id))dimensions.set(id,new Dimension(id));return dimensions.get(id);}};
export const system={afterEvents:{scriptEventReceive:new Signal()},currentTick:0,runInterval:f=>interval=f,runTimeout:(f,t)=>timeouts.push({f,at:system.currentTick+t}),run:f=>timeouts.push({f,at:system.currentTick+1})};
export function ticks(count){for(let i=0;i<count;i++){system.currentTick++;interval();for(const t of timeouts.filter(t=>t.at<=system.currentTick)){timeouts.splice(timeouts.indexOf(t),1);t.f();}}}
export {entities};

if(process.env.MOBPORTS_API_20_ONLY==='1')delete world.beforeEvents.entityHurt;
