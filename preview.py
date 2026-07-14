#!/usr/bin/env python3
"""Render the generated hull: 3D view + reconstructed lines (profile/half-breadth/body)."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for cand in ("/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
             "/System/Library/Fonts/Hiragino Sans GB.ttc",
             "/Library/Fonts/Arial Unicode.ttf"):
    try:
        fm.fontManager.addfont(cand)
        plt.rcParams["font.family"]=fm.FontProperties(fname=cand).get_name()
        break
    except Exception: pass
plt.rcParams["axes.unicode_minus"]=False
import build_hull as bh

full=bh.calibrate(); xs,zs,Y=bh.build_offsets(full)
Xd,Zd,Yd=bh.refine_grid(xs,zs,Y,nx=81)
FT=0.3048

fig=plt.figure(figsize=(15,9))

# --- 3D hull ---
ax=fig.add_subplot(2,2,(1,2),projection="3d")
Xg,Zg=np.meshgrid(Xd*FT,Zd*FT,indexing="ij")
for sgn in (+1,-1):
    ax.plot_surface(Xg, sgn*Yd*FT, Zg, rstride=2,cstride=1,
                    color="#4a7ba6",alpha=0.9,linewidth=0,antialiased=True)
ax.set_box_aspect((810,220,120))
ax.set_title("天城型 船体 3Dモデル（主要目から生成・排水量41,000tに較正）",fontsize=11)
ax.set_xlabel("length (m)");ax.set_ylabel("beam (m)");ax.set_zlabel("height (m)")
ax.view_init(elev=22,azim=-60)

# --- profile (sheer): keel + deck edge ---
ax2=fig.add_subplot(2,3,4)
ax2.plot(Xd*FT,(Yd[:,-1]*0)+Zd[-1]*FT,lw=0)  # dummy
prof_top=np.full_like(Xd,Zd[-1])
ax2.plot(Xd*FT,prof_top*FT,"k",lw=1.2,label="deck")
ax2.plot(Xd*FT,np.zeros_like(Xd),"k",lw=1.2)
ax2.axhline(bh.T*FT,color="#2c7",ls="--",lw=1,label="LWL")
ax2.set_title("側面（プロファイル）");ax2.set_aspect("equal");ax2.legend(fontsize=7)
ax2.set_xlabel("m")

# --- half-breadth (waterlines from above) ---
ax3=fig.add_subplot(2,3,5)
for j in range(0,len(Zd),2):
    ax3.plot(Xd*FT,Yd[:,j]*FT,lw=0.7,color="#36c" if Zd[j]<=bh.T else "#c73")
ax3.set_title("半幅（各喫水線）");ax3.set_aspect("equal");ax3.set_xlabel("m")

# --- body plan (sections; aft on left, fwd on right) ---
ax4=fig.add_subplot(2,3,6)
mid=len(xs)//2
for i in range(len(xs)):
    side=-1 if i<=mid else 1
    ax4.plot(side*Y[i,:]*FT,zs*FT,lw=0.7,
             color="#36c" if i>mid else "#888")
ax4.axhline(bh.T*FT,color="#2c7",ls="--",lw=1)
ax4.set_title("正面線図（Body Plan）左=後 右=前");ax4.set_aspect("equal");ax4.set_xlabel("m")

plt.tight_layout()
plt.savefig("preview.png",dpi=110,bbox_inches="tight")
print("wrote preview.png")
