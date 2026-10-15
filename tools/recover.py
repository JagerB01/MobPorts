"""Recover numeric model definitions and attributes from CFR output, fail on unknown constructs."""
import re,json,math,sys,zipfile,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--java-dir',type=Path,required=True);parser.add_argument('--jar',type=Path,required=True);args=parser.parse_args();JAVA=args.java_dir;JAR=args.jar
def nums(s):
 s=re.sub(r'\((?:float|int|double)\)','',s)
 return [float(v.strip().rstrip('fFdD')) for v in s.split(',') if v.strip()]
def splitargs(s):
 out=[];depth=0;start=0
 for i,c in enumerate(s):
  depth+=(c=='(')-(c==')')
  if c==',' and depth==0: out.append(s[start:i].strip()); start=i+1
 out.append(s[start:].strip());return out
def cubes(s):
 uv=[0,0];mirror=False;out=[]
 for m in re.finditer(r'\.(texOffs|mirror|addBox)\(',s):
  i=m.end();depth=1;j=i
  while depth: depth+=(s[j]=='(')-(s[j]==')');j+=1
  a=s[i:j-1];op=m[1]
  if op=='texOffs': uv=nums(a)
  elif op=='mirror':mirror=a!='false'
  else:
   a=splitargs(a);v=nums(','.join(a[:6]));inflate=0
   if len(a)>6:
    assert a[6].startswith('new CubeDeformation('),a
    inflate=nums(a[6][20:-1])[0]
   if all(x==0 for x in v[3:]):continue
   out.append(dict(origin=v[:3],size=v[3:],uv=uv.copy(),inflate=inflate,mirror=mirror))
 return out
def bone(name,pivot,c, parent=None,rotation=None):
 d=dict(name=name,pivot=pivot,cubes=c)
 if parent:d['parent']=parent
 if rotation:d['rotation']=rotation
 return d
def cube(x,y,z,w,h,d,u,v,inflate=0,mirror=False):return dict(origin=[x,y,z],size=[w,h,d],uv=[u,v],inflate=inflate,mirror=mirror)
def humanoid(skeleton=False,illager=False):
 arm=2 if skeleton else 4
 bones=[bone('head',[0,0,0],[cube(-4,-8,-4,8,8,8,0,0)]),bone('hat',[0,0,0],[cube(-4,-8,-4,8,8,8,32,0,.5)]),bone('body',[0,0,0],[cube(-4,0,-2,8,12,4,16,16)])]
 for side,x in [('right',-1),('left',1)]:
  bones += [bone(side+'_arm',[5*x,2,0],[cube(-1 if skeleton else (-3 if x<0 else -1),-2,-arm/2,arm,12,arm,40,16,mirror=x>0)]),bone(side+'_leg',[2*x,12,0],[cube(-arm/2,0,-arm/2,arm,12,arm,0,16,mirror=x>0)])]
 if illager:
  bones[0]['cubes']=[cube(-4,-10,-4,8,10,8,0,0)];bones[1]['cubes']=[cube(-4,-10,-4,8,12,8,32,0,.45)]
  bones[2]['cubes']=[cube(-4,0,-2,8,12,4,16,20),cube(-4,0,-2,8,18,4,0,38,.5)]
  bones.append(bone('nose',[0,-2,0],[cube(-1,-1,-6,2,4,2,24,0)],'head'))
  bones.append(bone('arms',[0,3,0],[cube(-8,-2,-2,4,8,4,44,22),cube(4,-2,-2,4,8,4,44,22,mirror=True),cube(-4,2,-2,8,4,4,40,38)],rotation=[-.75,0,0]))
 return dict(texture_size=[64,64 if illager else 32],bones=bones)
def parse_model(name):
 p=next(JAVA.rglob(name+'.java'));s=p.read_text().replace(', cubedeformation1)',', new CubeDeformation(-0.48f))').replace(', cubedeformation2)',', new CubeDeformation(0.0f))')
 start=re.search(r'public static LayerDefinition \w+\([^\n]*\) \{',s)
 if not start:return None
 s=s[start.end():];s=s[:s.index('return LayerDefinition.create')+150]
 bones={};variables={'partdefinition':None};texture=[int(x) for x in re.search(r'LayerDefinition.create\([^\n]+?\(int\)(\d+), \(int\)(\d+)\)',s).groups()]
 for line in s.splitlines():
  if '.addOrReplaceChild("' not in line:continue
  m=re.search(r'(?:(\w+) = )?(\w+)\.addOrReplaceChild\("([^"]+)", (.*)\);',line)
  assert m,line
  var,par,n,args=m.groups();a=splitargs(args);assert len(a)==2,(n,a)
  pose=a[1];v=[0,0,0];rot=[0,0,0]
  if pose!='PartPose.ZERO':
   v=nums(pose[pose.index('(')+1:-1]);rot=v[3:] or rot;v=v[:3]
  b=bone(n,v,cubes(a[0]),variables[par],rot)
  bones[n]=b
  if var:variables[var]=n
 # The Wisp and Mother Lava Squid generate tentacles in a loop.
 if name in ['WispModel','MotherLavaSquidModel']:
  mother=name.startswith('Mother');y=31 if mother else 15;length=18 if mother else 12
  for k in range(8):
   a=k*math.pi/4;b=bone('tentacle'+str(k),[math.cos(a)*5,y,math.sin(a)*5],[cube(-1,0,-1,2,length,2,48,0)],rotation=[0,-a+math.pi/2,0]);bones[b['name']]=b
 return dict(texture_size=texture,bones=list(bones.values()))
models={}
for name in ['SkullProjectileModel','CrystalSpikesModel','AncientHeroModel','AncientHeroSkullModel','CrystalZombieModel','DemonEyeModel','FlyingSkullModel','GlowSkeletonModel','MotherLavaSquidModel','OvergrownSkeletonModel','DesertAcolyteModel','DesertSorceressModel','WispModel','EyeModel']:
 models[name]=parse_model(name)
models['SwampZombieModel']=humanoid();models['SpectralSkeletonModel']=humanoid(True);models['AbyssologerModel']=humanoid(illager=True)
models['LavaSquidModel']=dict(texture_size=[64,32],bones=[bone('body',[0,8,0],[cube(-6,-8,-6,12,16,12,0,0)])]+[bone('tentacle'+str(k),[math.cos(k*math.pi/4)*5,15,math.sin(k*math.pi/4)*5],[cube(-1,0,-1,2,18,2,48,0)],rotation=[0,-k*math.pi/4+math.pi/2,0]) for k in range(8)])
# setupAnim overwrites the exported jaw offsets every frame.
for name in ['AncientHeroModel','AncientHeroSkullModel','FlyingSkullModel','SkullProjectileModel']:
 for b in models[name]['bones']:
  if b['name']=='mouth':b['pivot'][1]=1 if name=='AncientHeroModel' else 3
# Java roots float at their entity origin; retain an intentional half-block center for airborne heads.
for name in ['AncientHeroSkullModel','FlyingSkullModel','SkullProjectileModel']:
 for b in models[name]['bones']:
  if b['name']=='head':b['pivot'][1]=24
# Runtime copyFrom overrides these exported poses every rendered frame.
for b in models['DemonEyeModel']['bones']:
 if b['name']=='tendrils':b['pivot']=[0,20,0]
for b in models['AncientHeroModel']['bones']:
 if b['name']=='cape':b['pivot']=[0,0,0]
attrs={}
for p in (JAVA/'common/entity').rglob('*.java'):
 s=p.read_text();a={k:float(v) for k,v in re.findall(r'\.add\(Attributes\.(\w+), ([\d.]+)\)',s)}
 if a:attrs[p.stem]=a
entity=(JAVA/'core/init/EntityInit.java').read_text();mobs=[]
with zipfile.ZipFile(JAR) as z:
 lang=json.loads(z.read('assets/monsterplus/lang/en_us.json'))
 (ROOT/'source/lang.json').write_text(json.dumps(lang,indent=2)+'\n')
 for n in z.namelist():
  if n.startswith('assets/monsterplus/models/item/') and n.endswith('.json'):
   dest=ROOT/'source/item_models'/n.split('/')[-1];dest.parent.mkdir(exist_ok=True);dest.write_bytes(z.read(n))
 for id,cls,w,h in re.findall(r'ENTITIES.register\("([^"]+)", \(\) -> EntityType.Builder.of\((\w+)::new[^\n]+?\.sized\(([\d.]+)f, ([\d.]+)f\)',entity):
  if cls not in attrs:continue
  model={'Eye':'EyeModel','EnderEye':'DemonEyeModel','Soul':'WispModel','SpectralSkeleton':'SpectralSkeletonModel'}.get(cls,cls+'Model')
  mobs.append(dict(id=id,java_class=cls,model=model,name=lang.get('entity.monsterplus.'+id,id),width=float(w),height=float(h),attributes=attrs[cls]))
 for n in z.namelist():
  if n.startswith('assets/monsterplus/') and not n.endswith('/'):
   rel=n[len('assets/monsterplus/'):]
   if rel.startswith(('textures/','sounds/')) or rel=='sounds.json':
    dest=ROOT/'source/assets'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(n))
 for n in z.namelist():
  if n.startswith('data/monsterplus/') and n.endswith('.json'):
   dest=ROOT/'source/java_data'/n[len('data/monsterplus/'):];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(n))
(ROOT/'source/models.json').write_text(json.dumps(models,indent=2)+'\n')
(ROOT/'source/mobs.json').write_text(json.dumps(mobs,indent=2)+'\n')
(ROOT/'source/provenance.json').write_text(json.dumps(dict(file=JAR.name,sha256=hashlib.sha256(JAR.read_bytes()).hexdigest(),embedded_version='1.1.9.0',filename_version='1.2.0.0',author='Nitespring',license='All rights reserved',recovery='CFR 0.152; numeric model and attribute recovery; vanilla inherited models explicitly reconstructed'),indent=2)+'\n')
print('Recovered',len(mobs),'mobs;',len(models),'models;',sum(len(b['cubes']) for m in models.values() for b in m['bones']),'cubes')
