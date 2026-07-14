#!/usr/bin/env python3
"""
Build a model-viewer comparison page for the generated design variants.
Usage: python3 build_compare.py specs.json   -> variants/compare.html
Each spec needs a matching variants/{name}.glb (from ship_gen + batch_glb).
"""
import json, os, sys
FT=0.3048
here=os.path.dirname(os.path.abspath(__file__))
specs=json.load(open(sys.argv[1] if len(sys.argv)>1 else os.path.join(here,"specs.json")))
outdir=os.path.join(here,"variants")

def m(v,f=1):
    try: return round(float(v)*f,1)
    except: return None

cards=""
rows=""
for s in specs:
    nm=s["name"]; glb=f"{nm}.glb"
    if not os.path.exists(os.path.join(outdir,glb)):
        cards+=f'<div class="card missing">{nm}<br><small>glb未生成</small></div>'; continue
    Lm=m(s.get("L_wl_ft"),FT); Bm=m(s.get("beam_ft"),FT); Tm=m(s.get("draught_ft"),FT)
    nf=s.get("n_funnels","?"); tl=s.get("turret_layout","?"); disp=s.get("displacement_t","?"); spd=s.get("speed_kt","?")
    cards+=f'''<div class="card">
      <model-viewer src="{glb}" camera-controls auto-rotate rotation-per-second="18deg"
        camera-orbit="55deg 78deg 340m" shadow-intensity="0.6" exposure="1.1"
        interaction-prompt="none" style="width:100%;height:230px;background:#20303c"></model-viewer>
      <div class="cap"><b>{nm}</b>　煙突<span class="hl">{nf}</span>本 / 主砲{tl}</div>
      <div class="sub">{Lm}m × {Bm}m × 喫水{Tm}m / {disp}t / {spd}kt</div>
    </div>'''
    rows+=f'<tr><td>{nm}</td><td>{Lm}</td><td>{Bm}</td><td>{Tm}</td><td>{disp}</td><td>{spd}</td><td class="hl">{nf}</td><td>{tl}</td></tr>'

html=f'''<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>八八艦隊 設計案 3D比較</title>
<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
<style>
body{{font-family:"Hiragino Kaku Gothic ProN",sans-serif;margin:0;background:#eef1f4;color:#1a2530}}
header{{background:#20303c;color:#fff;padding:14px 20px}} header h1{{margin:0;font-size:17px}}
header p{{margin:4px 0 0;color:#b7c4cf;font-size:12px}}
.wrap{{max-width:1300px;margin:0 auto;padding:16px 20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}}
.card{{background:#fff;border:1px solid #d7dde3;border-radius:10px;overflow:hidden}}
.card.missing{{display:flex;align-items:center;justify-content:center;height:280px;color:#a33}}
.cap{{padding:8px 12px 2px;font-size:13px}} .sub{{padding:0 12px 10px;color:#667;font-size:11px}}
.hl{{color:#c0392b;font-weight:700;font-size:15px}}
table{{border-collapse:collapse;width:100%;margin:18px 0;font-size:12px;background:#fff}}
th,td{{border:1px solid #dde;padding:6px 9px;text-align:center}} th{{background:#20303c;color:#fff}}
td:first-child{{text-align:left;font-weight:600}}
.note{{font-size:12px;color:#556;background:#fff;border-left:4px solid #20303c;padding:8px 12px;border-radius:4px}}
</style></head><body>
<header><h1>八八艦隊 設計案 3D比較（線図・要目からの復元）</h1>
<p>平賀譲デジタルアーカイブの要目・一般配置図から、各設計案の船体・煙突数・主砲配置をパラメトリックに再現。ドラッグで回転できます。</p></header>
<div class="wrap">
<div class="grid">{cards}</div>
<table><tr><th>設計案</th><th>水線長(m)</th><th>幅(m)</th><th>喫水(m)</th><th>排水量(t)</th><th>速力(kt)</th><th>煙突</th><th>主砲配置</th></tr>{rows}</table>
<div class="note">形状は主要目＋中央断面テンプレートからのパラメトリック復元。煙突数・主砲配置は各案の一般配置図に基づく。寸法・配置は図面由来、断面の細部は近似。出典：平賀譲デジタルアーカイブ（東京大学）。</div>
</div></body></html>'''
stem=os.path.splitext(os.path.basename(sys.argv[1] if len(sys.argv)>1 else "compare"))[0]
name="compare.html" if stem in ("specs","compare") else f"compare_{stem}.html"
open(os.path.join(outdir,name),"w").write(html)
print(f"wrote variants/{name} for",len(specs),"designs")
