#!/usr/bin/env python3
"""
Amagi-class battlecruiser hull generator.

Builds a lofted, watertight hull mesh from the PRINCIPAL DIMENSIONS read off the
Hiraga Digital Archive body plan (B-C 正面線図, item 21340101-027):

    Length on LWL      810.0 ft
    Length overall     818.0 ft
    Breadth on LWL     100.0 ft   (half = 50.0)
    Breadth max (uwl)  102.9 ft   (half = 51.45)
    Draught mean keel   31.25 ft
    Water lines apart    6.25 ft
    Stations apart      40.5 ft  (20 spaces)
    Displacement       ~41,000 long tons

Method: parametric offset table (station x waterline half-breadths) whose midship
fullness is calibrated so the integrated underwater volume reproduces ~41,000 t
(salt water, 35 ft^3/long ton). Ends taper to the centre-plane so the surface
closes; deck is capped -> watertight solid. Exports OBJ + STL and an offset CSV.

If you later trace real per-station offsets, drop them into offsets.csv with the
same grid and re-run with --offsets to loft the authentic hull instead.
"""
import numpy as np, csv, os, sys

# ---- read dimensions (feet) ----
L_LWL   = 810.0
L_OA    = 818.0
BMAX_H  = 102.9/2.0     # max half-breadth (under LWL)
BLWL_H  = 100.0/2.0     # half-breadth at LWL
T       = 31.25         # design draught
WL_DZ   = 6.25          # waterline spacing
ST_DX   = 40.5          # station spacing
DISP_T  = 41000.0       # target displacement, long tons
FT3_PER_TON = 35.0      # salt water

Z_DECK  = 46.0          # model hull top (freeboard above LWL) for a usable solid
N_ST    = 20            # station spaces (0..20 -> 21 stations)
N_GIRTH = 26            # girth samples keel->deck per station

# ---- longitudinal beam factor at LWL (0..1), station 0=AP .. 20=FP ----
# finer bow (FP) than stern (AP): classic fast-capital-ship waterplane.
_stn = np.arange(N_ST+1)
_beam_lwl = np.array([
 0.14,0.42,0.66,0.82,0.92,0.975,0.997,1.0,1.0,1.0,1.0,   # AP..mid (0..10)
 1.0,0.998,0.985,0.955,0.90,0.815,0.69,0.52,0.30,0.05    # mid..FP (11..20)
])

# "V-ness" of sections: 0 = wall-sided/flat (midship), 1 = deep-V (ends).
_vness = np.clip(np.abs(_stn-10.5)/10.5, 0, 1)**1.6

# Bow-form control: 0 = convex bow waterline (older/fuller entrance),
# 1 = strongly hollow, streamlined entrance (the post-Nagato "smoother" bow).
BOW_HOLLOW = 0.0
def _apply_bow(bl):
    """Pull in the mid-entrance of the forward waterplane so the bow waterline
    becomes hollow (S-shaped) rather than a plain convex taper."""
    if BOW_HOLLOW <= 0: return bl
    bl = bl.copy(); i0 = 13; n = len(bl)
    for i in range(i0, n-1):
        t = (i-i0)/(n-1-i0)                    # 0 at entrance start, 1 near stem
        bl[i] *= (1.0 - 0.40*BOW_HOLLOW*np.sin(np.pi*t))
    return bl

# Midship vertical section template, fitted to the body-plan measurements
# (station 10, normalised to max half-beam BMAX_H=51.45 ft):
#   z/T : 0    0.2   0.4   0.6   0.8   1.0(LWL)
#   frac: 0   .777  .933  .981  1.000 .972   -> max beam BELOW LWL, wall-sided
_MZ = np.array([0.0, 0.20, 0.40, 0.60, 0.80, 1.00])
_MV = np.array([0.0, 0.777, 0.933, 0.981, 1.000, 0.972])
def mid_profile(zn):
    return np.interp(zn, _MZ, _MV)

def _beamlwl_fat(beam_lwl, p):
    """Adjust end fineness (Cp). p>0 fattens ends, p<0 fines them.
    Midship peak (=1.0) preserved, so max beam stays 102.9 ft."""
    return np.clip(beam_lwl, 1e-6, 1.0)**(1.0/(1.0+1.3*p))

def section_halfbreadth(beam_lwl, vness, z, p):
    """Half-breadth (ft). Midship uses the drawing-fitted full, wall-sided,
    hard-bilge template with max beam below LWL; ends blend to a fine V.
    Displacement is tuned by end fineness p, keeping the midship shape fixed."""
    ymax = BMAX_H * _beamlwl_fat(beam_lwl, p)
    zt = T
    if z <= zt:
        zn = z/zt
        m  = mid_profile(zn)          # drawing-fitted full section
        vt = zn**1.7                  # fine deep-V for the ends
        v  = (1.0-vness)*m + vness*vt
    else:
        za  = (z - zt)/(Z_DECK - zt)
        vl  = (1.0-vness)*mid_profile(1.0) + vness*1.0
        v   = vl*(1.0 - 0.06*za)      # slight tumblehome above LWL
    return ymax * v

def build_offsets(fullness):
    xs = _stn*ST_DX
    zs = np.arange(0, Z_DECK+1e-6, WL_DZ)
    if zs[-1] < Z_DECK: zs = np.append(zs, Z_DECK)
    Y = np.zeros((len(xs), len(zs)))
    beam = _apply_bow(_beam_lwl)          # apply bow-form (hollow entrance)
    for i in range(len(xs)):
        for j,z in enumerate(zs):
            Y[i,j] = section_halfbreadth(beam[i], _vness[i], z, fullness)
    return xs, zs, Y

def displacement_tons(xs, zs, Y):
    """Underwater volume up to z=T via double integration of half-breadth."""
    juw = zs <= T + 1e-6
    zt = zs[juw]
    area = np.zeros(len(xs))            # section area up to LWL
    for i in range(len(xs)):
        area[i] = 2.0*np.trapz(Y[i,juw], zt)   # both sides
    vol = np.trapz(area, xs)
    return vol/FT3_PER_TON, vol

# ---- calibrate fullness to hit target displacement ----
def calibrate():
    lo,hi = -0.7,4.0
    for _ in range(40):
        mid=(lo+hi)/2
        xs,zs,Y=build_offsets(mid)
        d,_=displacement_tons(xs,zs,Y)
        if d<DISP_T: lo=mid
        else: hi=mid
    return (lo+hi)/2

def refine_grid(xs, zs, Y, nx=81, nz=None):
    """Spline-smooth to a denser grid for a clean lofted surface."""
    from scipy.interpolate import RectBivariateSpline
    ky = min(3,len(xs)-1); kz=min(3,len(zs)-1)
    spl=RectBivariateSpline(xs,zs,Y,kx=ky,ky=kz,s=0)
    Xd=np.linspace(xs[0],xs[-1],nx)
    Zd=zs if nz is None else np.linspace(zs[0],zs[-1],nz)
    Yd=spl(Xd,Zd)
    Yd=np.clip(Yd,0,None)
    Yd[0,:]=0; Yd[-1,:]=0            # close stem & stern at centre-plane
    return Xd,Zd,Yd

def write_offsets_csv(path,xs,zs,Y):
    with open(path,"w",newline="") as f:
        w=csv.writer(f); w.writerow(["z\\x_ft"]+[f"{x:.1f}" for x in xs])
        for j,z in enumerate(zs):
            w.writerow([f"{z:.2f}"]+[f"{Y[i,j]:.2f}" for i in range(len(xs))])

def build_mesh(Xd,Zd,Yd):
    """Watertight solid: starboard grid + mirrored port + deck cap."""
    nx,nz=Yd.shape
    V=[]; idx={}
    def add(p):
        key=(round(p[0],4),round(p[1],4),round(p[2],4))
        if key not in idx:
            idx[key]=len(V); V.append(p)
        return idx[key]
    # winding chosen so normals point OUTWARD; degenerate tris are dropped.
    # grids of vertex indices
    S=np.zeros((nx,nz),dtype=int); P=np.zeros((nx,nz),dtype=int)
    for i in range(nx):
        for j in range(nz):
            S[i,j]=add((Xd[i], Yd[i,j], Zd[j]))
            P[i,j]=add((Xd[i],-Yd[i,j], Zd[j]))
    F=[]
    def quad(a,b,c,d):
        # reversed winding -> outward normals; skip degenerate (collapsed) tris
        if len({a,c,b})==3: F.append((a,c,b))
        if len({a,d,c})==3: F.append((a,d,c))
    for i in range(nx-1):
        for j in range(nz-1):
            quad(S[i,j],S[i+1,j],S[i+1,j+1],S[i,j+1])       # starboard
            quad(P[i,j],P[i,j+1],P[i+1,j+1],P[i+1,j])       # port (rev)
    # deck cap (top waterline ring) as a strip between starboard & port edges
    jt=nz-1
    for i in range(nx-1):
        quad(S[i,jt],S[i+1,jt],P[i+1,jt],P[i,jt])
    # drop exact duplicate faces (coincident tris at the pinched stem/stern tips)
    seen=set(); Fu=[]
    for t in F:
        k=frozenset(t)
        if k in seen: continue
        seen.add(k); Fu.append(t)
    return np.array(V), Fu

def write_obj(path,V,F):
    with open(path,"w") as f:
        f.write("# Amagi-class hull (parametric, calibrated to Hiraga body plan dims)\n")
        for v in V: f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
        for t in F: f.write(f"f {t[0]+1} {t[1]+1} {t[2]+1}\n")

def write_stl(path,V,F):
    tris=V[np.array(F)]
    with open(path,"wb") as f:
        f.write(b'\0'*80); f.write(np.uint32(len(F)).tobytes())
        for tri in tris:
            n=np.cross(tri[1]-tri[0],tri[2]-tri[0]); nn=np.linalg.norm(n)
            n=n/nn if nn>0 else n
            f.write(n.astype('<f4').tobytes())
            for p in tri: f.write(p.astype('<f4').tobytes())
            f.write(b'\0\0')

if __name__=="__main__":
    here=os.path.dirname(os.path.abspath(__file__))
    full=calibrate()
    xs,zs,Y=build_offsets(full)
    d,vol=displacement_tons(xs,zs,Y)
    Xd,Zd,Yd=refine_grid(xs,zs,Y,nx=81)
    write_offsets_csv(os.path.join(here,"offsets_generated.csv"),xs,zs,Y)
    V,F=build_mesh(Xd,Zd,Yd)
    write_obj(os.path.join(here,"amagi_hull.obj"),V,F)
    write_stl(os.path.join(here,"amagi_hull.stl"),V,F)
    # metrics
    FT=0.3048
    print(f"fullness      = {full:.4f}")
    print(f"displacement  = {d:,.0f} long tons  (target {DISP_T:,.0f})")
    print(f"underwater V  = {vol:,.0f} ft^3  = {vol*FT**3:,.0f} m^3")
    print(f"L_LWL {L_LWL:.0f} ft = {L_LWL*FT:.1f} m | Bmax {BMAX_H*2:.1f} ft = {BMAX_H*2*FT:.2f} m | T {T:.2f} ft = {T*FT:.2f} m")
    Cb=vol/(L_LWL*BLWL_H*2*T); print(f"Cb (block coef) = {Cb:.3f}")
    print(f"vertices {len(V)}  triangles {len(F)}")
    print("wrote: amagi_hull.obj, amagi_hull.stl, offsets_generated.csv")
