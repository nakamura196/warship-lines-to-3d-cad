#!/usr/bin/env python3
"""Generate clean blog figures for the Zenn article."""
import numpy as np, matplotlib, os
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image, ImageOps, ImageEnhance
FONT="/System/Library/Fonts/Hiragino Sans GB.ttc"
fm.fontManager.addfont(FONT); plt.rcParams["font.family"]=fm.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"]=False
import build_hull as bh

OUT="/Users/nakamura/git/zenn/web/public/images/articles"
SLUG="warship-lines-plan-3d-cad"
os.makedirs(OUT,exist_ok=True)
FT=0.3048
full=bh.calibrate(); xs,zs,Y=bh.build_offsets(full)
Xd,Zd,Yd=bh.refine_grid(xs,zs,Y,nx=101)

# --- fig1: 3D hull ---
fig=plt.figure(figsize=(11,4.6))
ax=fig.add_subplot(111,projection="3d")
Xg,Zg=np.meshgrid(Xd*FT,Zd*FT,indexing="ij")
for sgn in (+1,-1):
    ax.plot_surface(Xg,sgn*Yd*FT,Zg,rstride=2,cstride=1,color="#4a7ba6",
                    alpha=0.95,linewidth=0.15,edgecolor="#2c4a63",antialiased=True)
ax.set_box_aspect((810,220,150))
ax.set_xlabel("船長 (m)");ax.set_ylabel("船幅 (m)");ax.set_zlabel("高さ (m)")
ax.set_title("主要目のみから生成した天城型 船体（排水量41,000tに較正）")
ax.view_init(elev=20,azim=-63)
plt.tight_layout();plt.savefig(f"{OUT}/{SLUG}-hull3d.png",dpi=120,bbox_inches="tight");plt.close()

# --- fig2: reconstructed lines ---
fig,axs=plt.subplots(1,3,figsize=(13,3.4))
axs[0].axhline(bh.T*FT,color="#2a2",ls="--",lw=1,label="LWL")
axs[0].plot(Xd*FT,np.full_like(Xd,Zd[-1])*FT,"k",lw=1.3)
axs[0].plot(Xd*FT,np.zeros_like(Xd),"k",lw=1.3)
axs[0].set_title("側面（プロファイル）");axs[0].set_aspect("equal");axs[0].legend(fontsize=8);axs[0].set_xlabel("m")
for j in range(0,len(Zd),2):
    axs[1].plot(Xd*FT,Yd[:,j]*FT,lw=0.8,color="#36c" if Zd[j]<=bh.T else "#c73")
axs[1].set_title("半幅（各喫水線を上から）");axs[1].set_aspect("equal");axs[1].set_xlabel("m")
mid=len(xs)//2
for i in range(len(xs)):
    side=-1 if i<=mid else 1
    axs[2].plot(side*Y[i,:]*FT,zs*FT,lw=0.8,color="#36c" if i>mid else "#888")
axs[2].axhline(bh.T*FT,color="#2a2",ls="--",lw=1)
axs[2].set_title("正面線図 Body Plan（左=船尾 右=船首）");axs[2].set_aspect("equal");axs[2].set_xlabel("m")
plt.tight_layout();plt.savefig(f"{OUT}/{SLUG}-lines.png",dpi=120,bbox_inches="tight");plt.close()

# --- fig3: source body plan crop (invert negative -> black-on-white) ---
src="/Users/nakamura/git/ndl/ai/amagi_cad/crop/dims_b.jpg"
im=Image.open(src).convert("L")
im=ImageOps.invert(im); im=ImageOps.autocontrast(im,cutoff=1)
im=ImageEnhance.Contrast(im).enhance(1.25)
im.convert("RGB").save(f"{OUT}/{SLUG}-source.png",quality=88)
print("wrote 3 figures to",OUT)
