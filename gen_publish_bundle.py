#!/usr/bin/env python3
"""
Generate, for every ship in a specs file: per-ship IIIF/model-viewer annotations
(funnels, turret groups, bridge, masts) in the glb frame (x=AP..FP metres,
y=0 centreline, z up from keel), plus a publish_manifest.json for archivebase.
Usage: python3 gen_publish_bundle.py verified_fleet.json
"""
import json, os, sys, numpy as np
import ship_gen as sg
FT=0.3048
here=os.path.dirname(os.path.abspath(__file__))
specs=json.load(open(sys.argv[1] if len(sys.argv)>1 else "verified_fleet.json"))
outdir=os.path.join(here,"variants"); os.makedirs(outdir,exist_ok=True)

def annotations(sp):
    L=float(sp["L_wl_ft"]); ZD=float(sp["draught_ft"])+float(sp.get("freeboard_ft",20.75))
    def P(xft,zft): return [round(xft*FT,2),0.0,round(zft*FT,2)]
    A=[]
    T=sg.parse_turrets(sp.get("turret_layout","2-1-2"),L,60)
    fwd=[t for t in T if t[1]>0 and t[0]>0.5*L]; mid=[t for t in T if 0.35*L<t[0]<0.6*L and t[1]>0]
    aft=[t for t in T if t[1]<0]
    g=int(sp.get("guns_per_turret",2)); gg="連装" if g==2 else ("三連装" if g==3 else f"{g}門")
    if fwd: A.append(dict(position=P(np.mean([t[0] for t in fwd]),ZD+9),title=f"前部主砲（{len(fwd)}基・{gg}）",title_en="Forward main turrets",lead=f"{sp.get('main_gun','')} {gg}砲塔 {len(fwd)}基",lead_en="Forward main battery"))
    if mid: A.append(dict(position=P(np.mean([t[0] for t in mid]),ZD+6),title=f"中央主砲（{len(mid)}基）",title_en="Amidships main turret(s)",lead="中央部の主砲",lead_en="Amidships main battery"))
    if aft: A.append(dict(position=P(np.mean([t[0] for t in aft]),ZD+9),title=f"後部主砲（{len(aft)}基・{gg}）",title_en="Aft main turrets",lead=f"{sp.get('main_gun','')} {gg}砲塔 {len(aft)}基",lead_en="Aft main battery"))
    nf=int(sp.get("n_funnels",0) or 0)
    if nf: A.append(dict(position=P(0.64*L,ZD+30),title=f"煙突（{nf}本）",title_en=f"Funnels ({nf})",lead=f"煙突{nf}本。設計案により本数が変化。",lead_en=f"{nf} funnel(s)"))
    A.append(dict(position=P(0.73*L,ZD+20),title="艦橋",title_en="Bridge",lead="艦橋構造",lead_en="Bridge structure"))
    A.append(dict(position=P(0.71*L,ZD+55),title="前檣",title_en="Foremast",lead="前部マスト",lead_en="Foremast"))
    A.append(dict(position=P(0.44*L,ZD+50),title="主檣",title_en="Mainmast",lead="後部マスト",lead_en="Mainmast"))
    for a in A: a["normal"]=[0,0,1]
    return A

manifest=[]
for sp in specs:
    nm=sp["name"]
    ann=annotations(sp)
    af=os.path.join(outdir,f"{nm}_annotations.json")
    json.dump(ann,open(af,"w"),ensure_ascii=False,indent=1)
    manifest.append({
        "id":nm.replace("/","_"),"name":nm,
        "glb":f"variants/{nm}.glb","annotations":f"variants/{nm}_annotations.json",
        "verified":bool(sp.get("verified",True)),
        "metadata":{
            "L_wl_m":round(sp["L_wl_ft"]*FT,1),"beam_m":round(sp["beam_ft"]*FT,1),
            "draught_m":round(sp["draught_ft"]*FT,2),"displacement_t":sp.get("displacement_t"),
            "speed_kt":sp.get("speed_kt"),"funnels":sp.get("n_funnels"),
            "turret_layout":sp.get("turret_layout"),"main_gun":sp.get("main_gun"),
            "date":sp.get("date"),"provenance":"平賀譲デジタルアーカイブ（東京大学）",
            "method":"線図・主要目からのパラメトリック復元（複数エージェントで図面照合）"}})
json.dump(manifest,open(os.path.join(here,"publish_manifest.json"),"w"),ensure_ascii=False,indent=1)
print(f"wrote {len(manifest)} annotation files + publish_manifest.json")
for m in manifest: print(f"  {m['name']:16} {len(json.load(open(os.path.join(here,m['annotations']))))} annotations  verified={m['verified']}")
