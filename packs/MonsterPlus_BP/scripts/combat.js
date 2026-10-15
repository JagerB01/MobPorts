/** Pure combat rules shared by the runtime and deterministic regression tests. */
export const TAU = Math.PI * 2;
export function delta(a,b) { return {x:b.x-a.x,y:b.y-a.y,z:b.z-a.z}; }
export function length(v) {return Math.hypot(v.x,v.y,v.z);}
export function normalized(v) {const d=length(v)||1;return {x:v.x/d,y:v.y/d,z:v.z/d};}
export function scaled(v,s) {return {x:v.x*s,y:v.y*s,z:v.z*s};}
export function plus(a,b) {return {x:a.x+b.x,y:a.y+b.y,z:a.z+b.z};}
export function phaseForHealth(hp,max) {return hp<=max*.25?3:hp<=max*.5?2:hp<=max*.75?1:0;}
export function skullInterval(phase,ranged) {return ranged?16:[48,32,24,16][phase];}
export function ring(center,count,radius,offset=0,delay=0) {
 return Array.from({length:count},(_,i)=>({x:center.x+Math.cos(offset+i*TAU/count)*radius,y:center.y,z:center.z+Math.sin(offset+i*TAU/count)*radius,delay}));
}
/** Exact Java spike counts, distances, offsets, and stagger ticks. */
export function spikePattern(origin,target,pattern,random=Math.random) {
 const angle=Math.atan2(target.z-origin.z,target.x-origin.x);
 const dist=length(delta(origin,target));
 if(dist<4)return [...ring(origin,5,1.5,angle,1),...ring(origin,10,3,angle+1.2566371,2),...ring(origin,15,4.5,angle+2.256637,3)];
 if(pattern===1)return Array.from({length:16},(_,i)=>({x:origin.x+Math.cos(angle)*1.25*(i+1)+random()-.5,y:target.y,z:origin.z+Math.sin(angle)*1.25*(i+1)+random()-.5,delay:i}));
 if(pattern===2)return [{...target,delay:0},...ring(target,5,1,angle,1),...ring(target,8,1.5,angle+1.2566371,2),...ring(target,25,5,angle+2.566371,3)];
 if(pattern===3)return [{...target,delay:0},...ring(target,4,.75,angle,1),...ring(target,20,4,angle+2.566371,3)];
 return [{...target,delay:0},...ring(target,4,.75,angle,1),...ring(target,7,1.25,angle+1.2566371,2)];
}
export const spells = {
 abyssologer:[{id:'eyes',duration:60,cooldown:720,warmup:20},{id:'skeletons',duration:60,cooldown:560,warmup:20},{id:'darkness',duration:35,cooldown:720,warmup:20},{id:'spikes',duration:40,cooldown:60,warmup:20},{id:'purple',duration:20,cooldown:25,warmup:20}],
 desert_acolyte:[{id:'breath',duration:35,cooldown:160,warmup:20},{id:'small_fireball',duration:50,cooldown:200,warmup:20}],
 desert_sorceress:[{id:'breath',duration:35,cooldown:160,warmup:20},{id:'large_fireball',duration:50,cooldown:200,warmup:20},{id:'fire_wall',duration:40,cooldown:80,warmup:20},{id:'barrage',duration:20,cooldown:180,warmup:25}]
};
/** Per-spell timers prevent a short fireball cooldown from replacing summon spells. */
export function nextSpell(id,tick,cooldowns,eligible=(_id)=>true) {
 return spells[id]?.find(s=>(cooldowns[s.id]??0)<=tick&&eligible(s.id));
}
/** A thrown projectile must be attributed to its owner, never to another nearby mob. */
export const onHitEffects = {
 swamp_zombie:{effect:'poison',ticks:500},overgrown_skeleton:{effect:'poison',ticks:200},
 // Bedrock has no Java Glowing effect: handled as a documented particle marker in main.js.
 glow_skeleton:{effect:'glowing_marker',ticks:600}
};

export function javaArmorDamage(damage,armor,toughness=0) {const reduction=Math.min(20,Math.max(armor*.2,armor-damage/(2+toughness/4)));return damage*(1-reduction/25);}

export function eyeSize(random=Math.random) {
 const r=Math.floor(random()*13);
 if(r===1||r===2)return {scale:.5+.25*random(),tier:'small'};
 if(r>=3&&r<=7)return {scale:.75+.5*random(),tier:'normal'};
 if(r===8||r===9)return {scale:1.25+.25*random(),tier:'large'};
 if(r===10)return {scale:1.5+.5*random(),tier:'giant'};
 return {scale:1,tier:'normal'};
}
export function fireWallPattern(origin,target,pattern,random=Math.random) {
 const angle=Math.atan2(target.z-origin.z,target.x-origin.x),dist=length(delta(origin,target));
 if(dist*dist<32||(dist*dist<64&&random()<.5))return [...ring(origin,8,2.5,angle,1),...ring(origin,32,6.5,angle,1)];
 if(pattern===1)return spikePattern(origin,target,1,random);
 return ring(target,16,4.5,angle,1);
}

function wrapDegrees(a) {return ((a+180)%360+360)%360-180;}
/** Java EyeMoveControl's four-degree turn and 0.2 velocity interpolation. */
export function eyeSteering(position,velocity,goal,yaw,speed) {
 const d=delta(position,goal),distance=length(d);
 if(distance<1e-6)return {velocity:{x:0,y:0,z:0},yaw,pitch:0,speed};
 const desired=Math.atan2(d.z,d.x)*180/Math.PI;
 const old=wrapDegrees(yaw+90),diff=wrapDegrees(desired-old);
 const newYaw=old+Math.max(-4,Math.min(4,diff))-90;
 const turn=Math.abs(wrapDegrees(yaw-newYaw));
 const targetSpeed=turn<3?1.8:.2,step=turn<3?.005*(1.8/Math.max(speed,.01)):.025;
 const newSpeed=speed+Math.max(-step,Math.min(step,targetSpeed-speed));
 const pitch=Math.atan2(d.y,Math.hypot(d.x,d.z))*180/Math.PI,angle=(newYaw+90)*Math.PI/180;
 const wanted={x:newSpeed*Math.cos(angle)*Math.abs(d.x/distance),y:newSpeed*Math.sin(pitch*Math.PI/180)*Math.abs(d.y/distance),z:newSpeed*Math.sin(angle)*Math.abs(d.z/distance)};
 return {velocity:plus(velocity,scaled(delta(velocity,wanted),.2)),yaw:newYaw,pitch,speed:newSpeed};
}
