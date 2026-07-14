#!/usr/bin/env python3
"""Design-year timeline: year x waterline-length, bubble = displacement,
colour = ship type, edge = verified vs provisional."""
import matplotlib, os
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
F="/System/Library/Fonts/Hiragino Sans GB.ttc"; fm.fontManager.addfont(F)
plt.rcParams["font.family"]=fm.FontProperties(fname=F).get_name(); plt.rcParams["axes.unicode_minus"]=False

# (name, design_year, year_read, L_m, disp_t, type, verified)
S=[
 ("扶桑型",1913,False,195.1,30600,"戦艦",False),
 ("金剛型",1913,False,201.2,27642,"戦艦",False),
 ("長門型(陸奥)",1920,True,213.6,33029,"戦艦",False),
 ("A123",1917,True,227.0,36600,"戦艦",True),
 ("A124",1917,True,227.1,37200,"戦艦",True),
 ("A126",1918,False,227.1,39300,"戦艦",True),
 ("A127/加賀型",1919,False,228.6,39900,"戦艦",True),
 ("B63a",1917,False,243.8,41000,"巡洋戦艦",True),
 ("B-C 天城",1919,False,246.9,41000,"巡洋戦艦",True),
 ("B64",1917,False,246.9,41000,"巡洋戦艦",True),
 ("B62",1917,False,251.5,39900,"巡洋戦艦",True),
 ("G",1918,False,286.5,43500,"巡洋戦艦",True),
 ("球磨型",1920,True,158.5,5506,"巡洋艦",True),
 ("古鷹型",1922,True,177.0,7100,"巡洋艦",True),
]
COL={"巡洋戦艦":"#c0392b","戦艦":"#2c7fb8","巡洋艦":"#27 ae60".replace(" ","")}
fig,ax=plt.subplots(figsize=(13,7))
seen=set()
for name,yr,yrd,L,disp,typ,ver in S:
    c=COL[typ]
    ax.scatter(yr,L,s=disp/45,c=c,alpha=0.55,
               edgecolors=("black" if ver else "#888"),linewidths=(1.6 if ver else 1.0),
               marker=("o" if ver else "s"),
               label=(typ if typ not in seen else None),zorder=3)
    seen.add(typ)
    ax.annotate(name,(yr,L),xytext=(4,4),textcoords="offset points",fontsize=8.5)
ax.set_xlabel("設計年（概算・読取は年月を記載）"); ax.set_ylabel("水線長 (m)")
ax.set_title("平賀譲設計 主要艦の設計年 × 大きさ（円=排水量／●=図面検証済 ■=暫定）",fontsize=12)
ax.grid(alpha=0.25); ax.legend(title="艦種",loc="upper left")
ax.text(0.99,0.02,"排水量が円の大きさ。八八艦隊系(1916-20)で41,000t級巡戦へ大型化。",
        transform=ax.transAxes,ha="right",fontsize=8,color="#555")
plt.tight_layout()
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"timeline.png")
plt.savefig(out,dpi=120,bbox_inches="tight"); print("wrote",out)
