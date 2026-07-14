# warship-lines-to-3d-cad

旧日本海軍艦の線図（平賀譲デジタルアーカイブ・東京大学）から、**主要目と実測オフセット
だけ**を入力に 3D 船体を生成し、水密メッシュ・厳密CAD(STEP)・回転アニメまで出力する
パラメトリック・パイプライン。

対象艦は順次追加していきます（第1弾：**天城型巡洋戦艦**）。手法は艦に依存せず、線図から
主要目と中央断面を読み替えれば他艦にも適用できます。

解説記事（Zenn）:
- 幾何編：<https://zenn.dev/nakamura196/articles/warship-lines-plan-3d-cad>
- 塗装編：<https://zenn.dev/nakamura196/articles/warship-3d-model-color-texture>

## 入力と導出

- **入力**：主要目（水線長 810ft / 幅 100ft / 喫水 31.25ft / 排水量 ~41,000t）＋格子間隔＋
  正面線図から実測した中央断面オフセット。
- **導出**：オフセット表 → 排水量較正（prismatic を二分法） → ロフト → 水密メッシュ／
  NURBS曲面(STEP) → Blender 回転アニメ。

## スクリプト

| ファイル | 役割 |
|---|---|
| `build_hull.py` | オフセット表生成・排水量較正・水密メッシュ書き出し（OBJ/STL） |
| `build_fullship.py` | 全体船体＋上部構造＋マテリアル（OBJ+MTL） |
| `export_step.py` | NURBS 曲面ロフトで STEP（厳密CAD）出力（要 `gmsh`） |
| `render_anim.py` | Blender ヘッドレスで回転アニメ（PNG連番→ffmpegでmp4） |
| `preview.py` / `blog_figures.py` | 検証・記事用の図版生成 |

## 出力データ

`amagi_hull.obj` / `.stl` / `.step`（船殻）、`amagi_fullship.obj` / `.mtl` / `.glb`（全体船体）、
`offsets_generated.csv`（オフセット表）、`amagi_turntable*.mp4`（回転アニメ）。

## 使い方

```bash
pip install numpy scipy matplotlib pillow gmsh
python3 build_hull.py        # 船殻メッシュ + オフセット表
python3 export_step.py       # 厳密CAD (STEP)
python3 build_fullship.py    # 全体船体 (+材質)
# Blender 5.x:
/Applications/Blender.app/Contents/MacOS/Blender --background --python render_anim.py
ffmpeg -framerate 30 -i frames/f_%04d.png -c:v libx264 -pix_fmt yuv420p amagi_turntable.mp4
```

## 他艦への応用

`build_hull.py` 冒頭の主要目定数と、`_MZ/_MV`（中央断面テンプレート）を対象艦の
線図から読み替えれば、同じパイプラインで別艦の船体を生成できます。

## 出典・権利

図面は平賀譲デジタルアーカイブ（東京大学, IIIF 配信）に由来します。本リポジトリには
アーカイブ画像そのものは含めず（`crop/`, `src/`, `frames/` は非追跡）、生成した
コードと 3D データのみを収録しています。原資料の利用条件は同アーカイブに従ってください。
