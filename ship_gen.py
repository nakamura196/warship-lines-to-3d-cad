#!/usr/bin/env python3
"""
Parametric multi-ship generator. Turns a design SPEC (principal dimensions +
funnel count + turret layout) into a full-ship OBJ/MTL, reusing the calibrated,
drawing-fitted hull shape from build_hull.py. Built for the 8-8 fleet design
variant comparison (B62/B63a/B64/G battlecruisers, A124/A127 battleships...).

spec = {
  "name": "B64", "L_wl_ft": 810, "beam_ft": 100, "draught_ft": 31.25,
  "displacement_t": 41000, "n_funnels": 2, "turret_layout": "2-1-2",
  "main_gun": "41cm", "freeboard_ft": 20.75  # optional
}
"""
import numpy as np, os, re, importlib
import build_hull as bh

FT=0.3048

def gen_hull(spec):
    bh.L_LWL   = float(spec["L_wl_ft"])
    bh.BLWL_H  = float(spec["beam_ft"])/2.0
    bh.BMAX_H  = float(spec.get("beam_max_ft", spec["beam_ft"]*1.029))/2.0
    bh.T       = float(spec["draught_ft"])
    bh.ST_DX   = bh.L_LWL/bh.N_ST
    bh.DISP_T  = float(spec["displacement_t"])
    bh.Z_DECK  = bh.T + float(spec.get("freeboard_ft", 20.75))
    bh.BOW_HOLLOW = float(spec.get("bow_hollow", 0.0))
    # per-ship midship section: use this ship's measured half-breadths if given
    # (waterlines at z/T = 0,0.2,...,1.0), else keep the default template.
    mh=spec.get("midship_halfbreadths_ft")
    if mh:
        order=["keel","5WL","4WL","3WL","2WL","LWL"]
        vals=[mh.get(k) for k in order]
        if all(v is not None for v in vals):
            vals=np.array(vals,dtype=float); mx=vals.max()
            bh._MZ=np.array([0.0,0.2,0.4,0.6,0.8,1.0])
            bh._MV=vals/mx
            bh.BMAX_H=mx                 # measured max half-beam governs
    p=bh.calibrate()
    xs,zs,Y=bh.build_offsets(p)
    Xd,Zd,Yd=bh.refine_grid(xs,zs,Y,nx=121)
    V,F=bh.build_mesh(Xd,Zd,Yd)
    return V,F,Xd,Zd,Yd

def parse_turrets(layout, L, super_dx):
    """'2-1-2' (fwd-mid-aft) or '2-2' (fwd-aft) -> turret specs (x_ft, face, raised)."""
    parts=[int(n) for n in re.findall(r'\d+', str(layout))][:3]
    if len(parts)==3: fwd,mid,aft=parts
    elif len(parts)==2: fwd,mid,aft=parts[0],0,parts[1]
    else: fwd,mid,aft=2,1,2
    T=[]
    # forward group near bow (face +1), super-firing raised on the inner one
    fx=[0.86,0.80,0.74][:fwd]
    for k,fr in enumerate(fx): T.append((fr*L,+1, k%2==1))
    # midships
    if mid>=1: T.append((0.50*L,+1,False))
    if mid>=2: T.append((0.44*L,+1,False))
    # aft group (face -1)
    ax=[0.14,0.20,0.26][:aft]
    for k,fr in enumerate(ax): T.append((fr*L,-1, k%2==1))
    return T

def build_ship(spec, outdir):
    L=float(spec["L_wl_ft"]); Vh,Fh,Xd,Zd,Yd=gen_hull(spec)
    V=list(map(tuple,Vh)); FG=[(a,b,c,"hull") for (a,b,c) in Fh]
    def add(p): V.append((p[0],p[1],p[2])); return len(V)-1
    def quad(a,b,c,d,m):
        if len({a,c,b})==3: FG.append((a,c,b,m))
        if len({a,d,c})==3: FG.append((a,d,c,m))
    def box(cx,cy,cz,lx,ly,lz,m):
        x0,x1=cx-lx/2,cx+lx/2;y0,y1=cy-ly/2,cy+ly/2;z0,z1=cz,cz+lz
        p=[add((x,y,z)) for x in(x0,x1) for y in(y0,y1) for z in(z0,z1)]
        i=lambda a,b,c:p[(a*2+b)*2+c]
        quad(i(0,0,0),i(0,1,0),i(1,1,0),i(1,0,0),m);quad(i(0,0,1),i(1,0,1),i(1,1,1),i(0,1,1),m)
        quad(i(0,0,0),i(1,0,0),i(1,0,1),i(0,0,1),m);quad(i(0,1,0),i(0,1,1),i(1,1,1),i(1,1,0),m)
        quad(i(0,0,0),i(0,0,1),i(0,1,1),i(0,1,0),m);quad(i(1,0,0),i(1,1,0),i(1,1,1),i(1,0,1),m)
    def cyl(cx,cy,cz,r,h,m,axis='z',n=16,ry=None):
        ry=ry or r; th=np.linspace(0,2*np.pi,n,endpoint=False)
        if axis=='z':
            top=[add((cx+r*np.cos(t),cy+ry*np.sin(t),cz+h)) for t in th]
            bot=[add((cx+r*np.cos(t),cy+ry*np.sin(t),cz)) for t in th]; ct=add((cx,cy,cz+h));cb=add((cx,cy,cz))
        else:
            top=[add((cx+h,cy+r*np.cos(t),cz+ry*np.sin(t))) for t in th]
            bot=[add((cx,cy+r*np.cos(t),cz+ry*np.sin(t))) for t in th]; ct=add((cx+h,cy,cz));cb=add((cx,cy,cz))
        for k in range(n):
            j=(k+1)%n; quad(bot[k],bot[j],top[j],top[k],m)
            FG.append((ct,top[k],top[j],m)); FG.append((cb,bot[j],bot[k],m))
    def funnel(x,zd,h,r,ry,rake=6):
        th=np.linspace(0,2*np.pi,16,endpoint=False)
        bot=[add((x+r*np.cos(t),ry*np.sin(t),zd)) for t in th]
        top=[add((x+rake+r*0.85*np.cos(t),ry*0.85*np.sin(t),zd+h)) for t in th]
        for k in range(16): j=(k+1)%16; quad(bot[k],bot[j],top[j],top[k],"funnel")
        ct=add((x+rake,0,zd+h))
        for k in range(16): FG.append((ct,top[k],top[(k+1)%16],"funnel"))
    ZD=bh.Z_DECK; s=L/810.0   # scale superstructure sizes with ship length
    # wood deck overlay
    jt=Yd.shape[1]-1
    S=[add((Xd[i],Yd[i,jt]*0.98,Zd[jt]+0.2)) for i in range(len(Xd))]
    P=[add((Xd[i],-Yd[i,jt]*0.98,Zd[jt]+0.2)) for i in range(len(Xd))]
    C=[add((Xd[i],0,Zd[jt]+0.2)) for i in range(len(Xd))]
    for i in range(len(Xd)-1):
        quad(S[i],S[i+1],C[i+1],C[i],"deck"); quad(C[i],C[i+1],P[i+1],P[i],"deck")
    # turrets (guns_per_turret barrels each: 2=twin, 3=triple ...)
    guns=int(spec.get("guns_per_turret",2) or 2)
    turrets=parse_turrets(spec.get("turret_layout","2-1-2"), L, 60*s)
    gw=(18+guns*8)*s   # gunhouse width scales with barrel count
    for (x,face,raised) in turrets:
        dz=9 if raised else 0
        box(x,0,ZD+dz,30*s,gw,10*s,"turret")
        cyl(x,0,ZD-4+dz,16*s,4,"turret")
        dys=[0.0] if guns==1 else [(-(guns-1)/2+k)*6.4*s for k in range(guns)]
        for dy in dys: cyl(x+face*10*s,dy,ZD+6*s+dz,1.7,face*52*s,"steel_dark",axis='x',n=8)
    # funnels: n placed evenly in amidships band [0.52L..0.68L]
    nf=int(spec.get("n_funnels",2) or 2)
    if nf>0:
        xs_f=np.linspace(0.60*L,0.68*L,nf) if nf>1 else [0.63*L]
        for xf in xs_f: funnel(xf,ZD,34*s,10*s,7*s)
    # bridge + masts
    box(0.73*L,0,ZD,26*s,26*s,14*s,"superstructure"); box(0.72*L,0,ZD+14*s,18*s,18*s,11*s,"superstructure")
    cyl(0.71*L,0,ZD+25*s,4.5*s,9*s,"superstructure")
    cyl(0.71*L,0,ZD+30*s,2.2,80*s,"mast",n=8); cyl(0.44*L,0,ZD,2.4,95*s,"mast",n=8)

    MTL={"hull":(0.34,0.37,0.40),"deck":(0.55,0.44,0.30),"turret":(0.30,0.33,0.36),
         "steel_dark":(0.22,0.24,0.26),"funnel":(0.26,0.28,0.30),
         "superstructure":(0.38,0.41,0.44),"mast":(0.24,0.26,0.28)}
    os.makedirs(outdir,exist_ok=True)
    name=spec["name"]
    with open(os.path.join(outdir,f"{name}.mtl"),"w") as f:
        for nm,(r,g,b) in MTL.items(): f.write(f"newmtl {nm}\nKd {r} {g} {b}\nKs 0.15 0.15 0.15\nNs 30\n\n")
    by={}
    for a,b,c,m in FG: by.setdefault(m,[]).append((a,b,c))
    with open(os.path.join(outdir,f"{name}.obj"),"w") as f:
        f.write(f"# {name}\nmtllib {name}.mtl\n")
        for v in V: f.write(f"v {v[0]*FT:.4f} {v[1]*FT:.4f} {v[2]*FT:.4f}\n")
        for m,tris in by.items():
            f.write(f"usemtl {m}\n")
            for t in tris: f.write(f"f {t[0]+1} {t[1]+1} {t[2]+1}\n")
    return {"name":name,"L_m":round(L*FT,1),"beam_m":round(spec['beam_ft']*FT,1),
            "draught_m":round(spec['draught_ft']*FT,2),"disp_t":spec['displacement_t'],
            "funnels":nf,"turrets":spec.get("turret_layout","2-1-2"),
            "verts":len(V),"tris":len(FG)}

if __name__=="__main__":
    import json,sys
    here=os.path.dirname(os.path.abspath(__file__))
    specs=json.load(open(sys.argv[1])) if len(sys.argv)>1 else [
        {"name":"B-C_Amagi","L_wl_ft":810,"beam_ft":100,"draught_ft":31.25,"displacement_t":41000,"n_funnels":2,"turret_layout":"2-1-2","main_gun":"41cm"}]
    out=os.path.join(here,"variants")
    for sp in specs:
        print(build_ship(sp,out))
