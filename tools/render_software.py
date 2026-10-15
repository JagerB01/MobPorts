"""Offline texture/model inspection renderer. Not a Bedrock engine or parity test."""
import json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];RP=R/'packs/MonsterPlus_RP';OUT=R/'dist';W,H=320,320

def rotation(r):
 x,y,z=np.radians(r);cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y);cz,sz=math.cos(z),math.sin(z)
 rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
 return rz@ry@rx

def triangles(g,texture,hidden):
 bones={b['name']:b for b in g['bones']};trans={};result=[]
 def mat(name):
  if name in trans:return trans[name]
  b=bones[name];p=np.array(b.get('pivot',[0,0,0]));r=rotation(b.get('rotation',[0,0,0]));m=np.eye(4);m[:3,:3]=r;m[:3,3]=p-r@p
  if b.get('parent'):m=mat(b['parent'])@m
  trans[name]=m;return m
 def visible(name):
  return name not in hidden and (not bones[name].get('parent') or visible(bones[name]['parent']))
 for name,b in bones.items():
  if not visible(name):continue
  m=mat(name)
  for cube in b.get('cubes',[]):
   x,y,z=cube['origin'];w,h,d=cube['size'];f=cube.get('inflate',0);lo=np.array([x-f,y-f,z-f]);hi=np.array([x+w+f,y+h+f,z+d+f]);hi=np.maximum(hi,lo+.001)
   v=np.array([[lo[0],lo[1],lo[2]],[hi[0],lo[1],lo[2]],[hi[0],hi[1],lo[2]],[lo[0],hi[1],lo[2]],[lo[0],lo[1],hi[2]],[hi[0],lo[1],hi[2]],[hi[0],hi[1],hi[2]],[lo[0],hi[1],hi[2]]]);v=(m@np.column_stack((v,np.ones(8))).T).T[:,:3]
   u,t=cube['uv']
   faces=[([0,1,2,3],u+d,t+d,w,h),([5,4,7,6],u+2*d+w,t+d,w,h),([4,0,3,7],u,t+d,d,h),([1,5,6,2],u+d+w,t+d,d,h),([3,2,6,7],u+d,t,w,d),([4,5,1,0],u+d+w,t,w,d)]
   for indices,uu,vv,fw,fh in faces:
    uv=np.array([[uu,vv+fh],[uu+fw,vv+fh],[uu+fw,vv],[uu,vv]],float)
    if cube.get('mirror'):uv[:,0]=2*uu+fw-uv[:,0]
    for a in [[0,1,2],[0,2,3]]:result.append((v[np.array(indices)[a]],uv[a],texture))
 return result

def render(mob):
 id=mob['id'];d=json.loads((RP/f'entity/{id}.entity.json').read_text())['minecraft:client_entity']['description'];tris=[]
 for name in d['geometry']:
  path=RP/f'models/entity/{id+("_"+name if name!="default" else "")}.geo.json';g=json.loads(path.read_text())['minecraft:geometry'][0]
  texture=np.array(Image.open(RP/(d['textures'][name]+'.png')).convert('RGBA'))
  hidden={'left_arm','right_arm'} if id in ['abyssologer','desert_acolyte','desert_sorceress'] else set()
  tris+=triangles(g,texture,hidden)
 forward=np.array([-.8,.38,-1.6]);forward/=np.linalg.norm(forward);right=np.cross([0,1,0],forward);right/=np.linalg.norm(right);up=np.cross(forward,right);basis=np.array([right,up,forward])
 allpoints=np.concatenate([t[0] for t in tris]);projected=allpoints@basis.T;mn=projected.min(0);mx=projected.max(0);center=(mn+mx)/2;scale=min((W-44)/max(mx[0]-mn[0],1),(H-70)/max(mx[1]-mn[1],1));pixels=np.zeros((H,W,4),float);pixels[:,:,:]=[23,33,45,255];depth=np.full((H,W),-np.inf)
 ordered=sorted(tris,key=lambda t:np.mean((t[0]@basis.T)[:,2]))
 for vertices,uv,tex in ordered:
  v=(vertices@basis.T-center)*scale;v[:,0]+=W/2;v[:,1]=H/2-v[:,1]-15
  xmin=max(0,int(np.floor(v[:,0].min())));xmax=min(W-1,int(np.ceil(v[:,0].max())));ymin=max(0,int(np.floor(v[:,1].min())));ymax=min(H-1,int(np.ceil(v[:,1].max())))
  if xmin>xmax or ymin>ymax:continue
  xx,yy=np.meshgrid(np.arange(xmin,xmax+1)+.5,np.arange(ymin,ymax+1)+.5)
  a,b,c=v;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);
  if abs(den)<1e-8:continue
  wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den;wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;wc=1-wa-wb
  zz=wa*a[2]+wb*b[2]+wc*c[2];uvs=wa[...,None]*uv[0]+wb[...,None]*uv[1]+wc[...,None]*uv[2];tx=np.clip(uvs[...,0].astype(int),0,tex.shape[1]-1);ty=np.clip(uvs[...,1].astype(int),0,tex.shape[0]-1);colors=tex[ty,tx].astype(float);alpha=colors[...,3]/255
  zsub=depth[ymin:ymax+1,xmin:xmax+1];mask=(wa>=-1e-5)&(wb>=-1e-5)&(wc>=-1e-5)&(zz>=zsub-.02)&(alpha>.05)
  normal=np.cross(vertices[1]-vertices[0],vertices[2]-vertices[0]);normal/=max(np.linalg.norm(normal),1e-8);light=.65+.35*abs(np.dot(normal,np.array([.3,.8,-.5])))
  sub=pixels[ymin:ymax+1,xmin:xmax+1];mixed=colors[:,:,:3]*light*alpha[...,None]+sub[:,:,:3]*(1-alpha[...,None]);sub[mask,:3]=mixed[mask];zsub[mask]=zz[mask]
 im=Image.fromarray(pixels.astype('uint8'),'RGBA');draw=ImageDraw.Draw(im);draw.text((12,H-42),mob['name'],fill='white');draw.text((12,H-24),id,fill='#a5b3c5');return im
mobs=json.loads((R/'source/mobs.json').read_text());sheet=Image.new('RGBA',(W*6,H*3),'#0c121a')
for i,m in enumerate(mobs):sheet.paste(render(m),(i%6*W,i//6*H))
OUT.mkdir(exist_ok=True);sheet.save(OUT/'model-inspection.png');print('Rendered all 18 source-derived models to dist/model-inspection.png')
