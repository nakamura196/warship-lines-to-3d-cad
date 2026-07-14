#!/usr/bin/env python3
"""
Full-ship model of the Amagi-class battlecruiser, WITH materials (per-component
colours via a standard OBJ + MTL). This is the established CG approach — flat
PBR materials assigned per part — not AI colourisation. Colours follow documented
IJN practice: warship grey hull, wood/linoleum deck, darker grey guns/funnels.
Exports amagi_fullship.obj (+ .mtl) in metres.
"""
import numpy as np, os
import build_hull as bh

FT=0.3048
bh.Z_DECK=52.0
full=bh.calibrate()
xs,zs,Y=bh.build_offsets(full)
Xd,Zd,Yd=bh.refine_grid(xs,zs,Y,nx=121)
Vhull,Fhull=bh.build_mesh(Xd,Zd,Yd)

V=list(map(tuple,Vhull))
FG=[(a,b,c,"hull") for (a,b,c) in Fhull]   # faces tagged with material name
def add_v(p): V.append((p[0],p[1],p[2])); return len(V)-1
def quad(a,b,c,d,m):
    if len({a,c,b})==3: FG.append((a,c,b,m))
    if len({a,d,c})==3: FG.append((a,d,c,m))

def box(cx,cy,cz,lx,ly,lz,m):
    x0,x1=cx-lx/2,cx+lx/2; y0,y1=cy-ly/2,cy+ly/2; z0,z1=cz,cz+lz
    p=[add_v((x,y,z)) for x in (x0,x1) for y in (y0,y1) for z in (z0,z1)]
    def id(xi,yi,zi): return p[(xi*2+yi)*2+zi]
    quad(id(0,0,0),id(0,1,0),id(1,1,0),id(1,0,0),m)
    quad(id(0,0,1),id(1,0,1),id(1,1,1),id(0,1,1),m)
    quad(id(0,0,0),id(1,0,0),id(1,0,1),id(0,0,1),m)
    quad(id(0,1,0),id(0,1,1),id(1,1,1),id(1,1,0),m)
    quad(id(0,0,0),id(0,0,1),id(0,1,1),id(0,1,0),m)
    quad(id(1,0,0),id(1,1,0),id(1,1,1),id(1,0,1),m)

def cyl(cx,cy,cz,r,h,m,axis='z',n=18,ry=None):
    ry=ry or r; th=np.linspace(0,2*np.pi,n,endpoint=False)
    if axis=='z':
        top=[add_v((cx+r*np.cos(t),cy+ry*np.sin(t),cz+h)) for t in th]
        bot=[add_v((cx+r*np.cos(t),cy+ry*np.sin(t),cz))   for t in th]
        ct=add_v((cx,cy,cz+h)); cb=add_v((cx,cy,cz))
    else:
        top=[add_v((cx+h,cy+r*np.cos(t),cz+ry*np.sin(t))) for t in th]
        bot=[add_v((cx,  cy+r*np.cos(t),cz+ry*np.sin(t)))  for t in th]
        ct=add_v((cx+h,cy,cz)); cb=add_v((cx,cy,cz))
    for i in range(n):
        j=(i+1)%n
        quad(bot[i],bot[j],top[j],top[i],m)
        FG.append((ct,top[i],top[j],m)); FG.append((cb,bot[j],bot[i],m))

def turret(x,zd,face,s=1.0):
    box(x,0,zd,30*s,34*s,10*s,"turret")
    cyl(x,0,zd-4,16*s,4,"turret",axis='z')
    for dy in (-6*s,6*s): cyl(x+face*10*s,dy,zd+6*s,1.7,face*52*s,"steel_dark",axis='x',n=10)

def funnel(x,zd,h,r,ry,rake=6):
    th=np.linspace(0,2*np.pi,18,endpoint=False)
    bot=[add_v((x+r*np.cos(t),ry*np.sin(t),zd)) for t in th]
    top=[add_v((x+rake+r*0.85*np.cos(t),ry*0.85*np.sin(t),zd+h)) for t in th]
    for i in range(18):
        j=(i+1)%18; quad(bot[i],bot[j],top[j],top[i],"funnel")
    ct=add_v((x+rake,0,zd+h))
    for i in range(18): FG.append((ct,top[i],top[(i+1)%18],"funnel"))

ZD=bh.Z_DECK

# --- wood deck overlay (separate material) from the top-waterline outline ---
jt=Yd.shape[1]-1
S=[add_v((Xd[i], Yd[i,jt]*0.98, Zd[jt]+0.2)) for i in range(len(Xd))]
P=[add_v((Xd[i],-Yd[i,jt]*0.98, Zd[jt]+0.2)) for i in range(len(Xd))]
C=[add_v((Xd[i],0,             Zd[jt]+0.2)) for i in range(len(Xd))]
for i in range(len(Xd)-1):
    quad(S[i],S[i+1],C[i+1],C[i],"deck")
    quad(C[i],C[i+1],P[i+1],P[i],"deck")

# --- superstructure ---
turret(700,ZD,+1); turret(640,ZD+9,+1); turret(405,ZD,+1); turret(150,ZD+9,-1); turret(210,ZD,-1)
box(590,0,ZD,26,26,14,"superstructure"); box(588,0,ZD+14,20,20,12,"superstructure"); box(586,0,ZD+26,14,16,10,"superstructure")
cyl(586,0,ZD+36,5,10,"superstructure",axis='z')
funnel(520,ZD,34,10,7); funnel(470,ZD,34,10,7)
cyl(575,0,ZD+30,2.2,80,"mast",axis='z',n=8)
cyl(360,0,ZD,2.4,95,"mast",axis='z',n=8)
box(300,0,ZD,40,24,10,"superstructure"); box(255,0,ZD,30,20,8,"superstructure")

# --- materials (documented IJN-style colours: Kd = diffuse RGB) ---
MTL={
 "hull":         (0.34,0.37,0.40),  # 軍艦色 (warship grey, slightly blue)
 "deck":         (0.55,0.44,0.30),  # wood / linoleum deck (tan-brown)
 "turret":       (0.30,0.33,0.36),
 "steel_dark":   (0.22,0.24,0.26),  # gun barrels
 "funnel":       (0.26,0.28,0.30),
 "superstructure":(0.38,0.41,0.44),
 "mast":         (0.24,0.26,0.28),
}
here=os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here,"amagi_fullship.mtl"),"w") as f:
    for name,(r,g,b) in MTL.items():
        f.write(f"newmtl {name}\nKd {r:.3f} {g:.3f} {b:.3f}\nKa 0 0 0\nKs 0.15 0.15 0.15\nNs 30\n\n")

# group faces by material for OBJ
by_mat={}
for a,b,c,m in FG: by_mat.setdefault(m,[]).append((a,b,c))
with open(os.path.join(here,"amagi_fullship.obj"),"w") as f:
    f.write("# Amagi full ship (materials per component)\nmtllib amagi_fullship.mtl\n")
    for v in V: f.write(f"v {v[0]*FT:.4f} {v[1]*FT:.4f} {v[2]*FT:.4f}\n")
    for m,tris in by_mat.items():
        f.write(f"usemtl {m}\n")
        for t in tris: f.write(f"f {t[0]+1} {t[1]+1} {t[2]+1}\n")
print(f"vertices {len(V)}  triangles {len(FG)}  materials {len(by_mat)}")
print("wrote amagi_fullship.obj + .mtl")
