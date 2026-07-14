#!/usr/bin/env python3
"""
Bow-form comparison: overlay the LWL waterline (top-down) of several ships /
bow settings to visualise how the bow entrance became "smoother" (hollow).
Usage: python3 build_bow_compare.py [specs.json]  (each spec may set bow_hollow)
"""
import numpy as np, matplotlib, os, sys, json
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
F="/System/Library/Fonts/Hiragino Sans GB.ttc"
fm.fontManager.addfont(F); plt.rcParams["font.family"]=fm.FontProperties(fname=F).get_name()
plt.rcParams["axes.unicode_minus"]=False
import build_hull as bh, ship_gen as sg
FT=0.3048

def lwl_curve(spec):
    V,Fc,Xd,Zd,Yd=sg.gen_hull(spec)
    j=int(np.argmin(np.abs(Zd-bh.T)))
    return Xd*FT, Yd[:,j]*FT, bh.L_LWL*FT

if len(sys.argv)>1:
    cases=json.load(open(sys.argv[1]))
else:
    base=dict(L_wl_ft=700,beam_ft=100,draught_ft=30,displacement_t=37000)
    cases=[dict(name="長門以前タイプ（凸な船首・仮定）",bow_hollow=0.0,**base),
           dict(name="改正後タイプ（なめらか船首・仮定）",bow_hollow=0.9,**base)]

fig,axs=plt.subplots(1,2,figsize=(13,5))
colors=["#c0392b","#2c7fb8","#27ae60","#8e44ad","#e67e22"]
for k,sp in enumerate(cases):
    x,y,L=lwl_curve(sp); c=colors[k%len(colors)]
    # full waterplane (both sides), bow at right
    axs[0].plot(x, y,color=c,lw=1.6,label=sp.get("name",sp.get("name")))
    axs[0].plot(x,-y,color=c,lw=1.6)
    # bow close-up: forward 32% of length
    m=x>=0.68*L
    axs[1].plot(x[m], y[m],color=c,lw=2,label=sp.get("name"))
    axs[1].plot(x[m],-y[m],color=c,lw=2)
axs[0].set_title("水線面（上から）全体　右=船首");axs[0].set_aspect("equal");axs[0].legend(fontsize=9);axs[0].set_xlabel("m")
axs[1].set_title("船首クローズアップ（水線の入り方＝滑らかさ）");axs[1].set_aspect("equal");axs[1].legend(fontsize=9);axs[1].set_xlabel("m")
plt.tight_layout()
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"bow_compare.png")
plt.savefig(out,dpi=120,bbox_inches="tight"); print("wrote",out)
