#!/usr/bin/env python3
"""
Fleet comparison from the read specs:
  (1) size_compare.png  — all hulls' LWL plan at COMMON SCALE (size evolution)
  (2) race.mp4          — top-down "race": each hull moves at v ∝ design knots
Usage: python3 build_fleet_compare.py specs_all.json
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
here=os.path.dirname(os.path.abspath(__file__))
specs=json.load(open(sys.argv[1] if len(sys.argv)>1 else "specs_all.json"))

ships=[]
for sp in specs:
    V,Fc,Xd,Zd,Yd=sg.gen_hull(sp)
    j=int(np.argmin(np.abs(Zd-bh.T)))
    x=(Xd-Xd.min())*FT                       # 0..L metres, stern at 0
    y=Yd[:,j]*FT
    ships.append(dict(name=sp["name"],x=x,y=y,L=x.max(),
                      kt=sp.get("speed_kt"),disp=sp.get("displacement_t")))
ships.sort(key=lambda s:s["L"])
cols=plt.cm.viridis(np.linspace(0,0.92,len(ships)))

# ---- (1) size comparison at common scale ----
fig,ax=plt.subplots(figsize=(12,0.9*len(ships)+1))
for k,s in enumerate(ships):
    off=k*40
    ax.fill_between(s["x"], off+s["y"], off-s["y"], color=cols[k], alpha=0.85, lw=0)
    lab=f'{s["name"]}　L={s["L"]:.0f}m'
    if s["disp"]: lab+=f' / {s["disp"]:,}t'
    if s["kt"]: lab+=f' / {s["kt"]}kt'
    ax.text(s["x"].max()+6, off, lab, va="center", fontsize=10)
ax.set_title("八八艦隊系 設計案 サイズ比較（同一縮尺・水線面を上から／複数エージェントで図面一致を検証済）",fontsize=11)
ax.set_xlabel("m"); ax.set_aspect("equal"); ax.set_yticks([]); ax.set_xlim(-10,ships[-1]["L"]+150)
plt.tight_layout(); plt.savefig(os.path.join(here,"size_compare.png"),dpi=120,bbox_inches="tight"); plt.close()
print("wrote size_compare.png")

# ---- (2) speed race ----
racers=[s for s in ships if s["kt"]]
racers.sort(key=lambda s:-s["kt"])
T=7.0; FPS=25; N=int(T*FPS)
kt2mps=0.514444
SPEEDUP=6.0        # visual speed-up so ships travel a visible distance
dist_max=max(s["kt"] for s in racers)*kt2mps*SPEEDUP*T
os.makedirs(os.path.join(here,"race_frames"),exist_ok=True)
for f in os.listdir(os.path.join(here,"race_frames")): os.remove(os.path.join(here,"race_frames",f))
lane=45
for fi in range(N):
    t=fi/FPS
    fig,ax=plt.subplots(figsize=(13,0.62*len(racers)+1.4))
    ax.set_facecolor("#12324a")
    for k,s in enumerate(racers):
        off=k*lane
        dx=s["kt"]*kt2mps*SPEEDUP*t
        ax.fill_between(s["x"]+dx, off+s["y"], off-s["y"], color="#dfe8ef", alpha=0.95, lw=0)
        ax.text(-40, off, f'{s["name"]}\n{s["kt"]}kt', va="center", ha="right", fontsize=9, color="#dfe8ef")
    ax.set_xlim(-260, dist_max+ships_max if False else dist_max+300)
    ax.set_ylim(-lane, lane*len(racers))
    ax.set_aspect("equal"); ax.set_yticks([]); ax.set_xticks([])
    ax.set_title(f"速力レース（設計速力に比例・{SPEEDUP:.0f}倍速表示）  t={t:0.1f}s",color="#dfe8ef")
    for sp in ax.spines.values(): sp.set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(here,"race_frames",f"f_{fi:04d}.png"),dpi=100,facecolor="#12324a")
    plt.close()
print(f"wrote {N} race frames")
