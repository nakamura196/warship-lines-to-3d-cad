#!/usr/bin/env python3
"""
Export the hull as a genuine NURBS/B-rep STEP file (strict CAD), lofting the
SAME offset table used for the mesh. This is the "厳密CAD化" path: instead of
flat triangles, each station section becomes a smooth B-spline and the hull is
a B-spline surface -> STEP (AP214), openable/editable in Fusion360/Rhino/FreeCAD.

Swap in a traced offset table (real drawing offsets) and re-run to get a strict
CAD of the authentic hull form. Units: metres.
"""
import numpy as np, gmsh, os
import build_hull as bh

FT=0.3048
full=bh.calibrate()
xs,zs,Y=bh.build_offsets(full)
Xd,Zd,Yd=bh.refine_grid(xs,zs,Y,nx=41)   # 41 stations x len(Zd) waterlines
nx,nz=Yd.shape

gmsh.initialize()
gmsh.model.add("amagi_hull")
occ=gmsh.model.occ

def bspline_surface(sign):
    """One shell side (sign=+1 starboard, -1 port) as a B-spline surface."""
    pts=[]
    for i in range(nx):
        for j in range(nz):
            pts.append(occ.addPoint(Xd[i]*FT, sign*Yd[i,j]*FT, Zd[j]*FT))
    # pointTags ordered U(=station i) major, V(=waterline j) minor
    return occ.addBSplineSurface(pts, nx, degreeU=3, degreeV=3)

s_stbd=bspline_surface(+1)
s_port=bspline_surface(-1)
occ.synchronize()

here=os.path.dirname(os.path.abspath(__file__))
step=os.path.join(here,"amagi_hull.step")
gmsh.write(step)
gmsh.finalize()

# validate by re-importing
gmsh.initialize()
gmsh.model.add("check")
gmsh.model.occ.importShapes(step)
gmsh.model.occ.synchronize()
bb=gmsh.model.getBoundingBox(-1,-1)
gmsh.finalize()
print(f"STEP written: {step} ({os.path.getsize(step)//1024} KB)")
print(f"reimport bbox (m): x[{bb[0]:.1f},{bb[3]:.1f}] y[{bb[1]:.1f},{bb[4]:.1f}] z[{bb[2]:.1f},{bb[5]:.1f}]")
print(f"-> LOA {bb[3]-bb[0]:.1f} m, beam {bb[4]-bb[1]:.1f} m, depth {bb[5]-bb[2]:.1f} m")
