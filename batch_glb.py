# Blender: convert every variants/*.obj -> variants/*.glb.  Run: Blender -b --python batch_glb.py
import bpy, glob, os
d="/Users/nakamura/git/ndl/ai/amagi_cad/variants"
for obj in sorted(glob.glob(os.path.join(d,"*.obj"))):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=obj)
    out=obj[:-4]+".glb"
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False)
    print("GLB", os.path.basename(out))
