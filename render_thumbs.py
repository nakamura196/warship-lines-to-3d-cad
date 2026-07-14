# Blender: render a 3/4 thumbnail per verified-fleet ship, reusing the PROVEN
# turntable framing (render_anim.py): ship centred at origin, camera (300,-340,150)
# scaled by L/247. run: Blender -b --python render_thumbs.py
import bpy, math, json, os, mathutils
BASE="/Users/nakamura/git/ndl/ai/amagi_cad"
manifest=json.load(open(f"{BASE}/publish_manifest.json"))
SLUG={"B-C_Amagi":"amagi","B62":"b62","B63a":"b63a","B64":"b64","G":"g",
 "A123":"a123","A124":"a124","A126":"a126","A127_加賀型":"a127-kaga","球磨型":"kuma",
 "古鷹型":"furutaka","扶桑型":"fuso","金剛型":"kongo","長門型_陸奥":"nagato-mutsu"}
OUT=f"{BASE}/variants/thumbs"; os.makedirs(OUT,exist_ok=True)

for ship in manifest:
    slug=SLUG.get(ship["id"]); glb=f"{BASE}/{ship['glb']}"
    if not slug or not os.path.exists(glb): continue
    bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=glb)
    ms=[o for o in sc.objects if o.type=='MESH']
    bpy.context.view_layer.objects.active=ms[0]
    for o in ms: o.select_set(True)
    if len(ms)>1: bpy.ops.object.join()
    obj=bpy.context.view_layer.objects.active
    # world bbox, then centre horizontally (bake), keel stays at its z
    lo=[1e9]*3; hi=[-1e9]*3
    for c in obj.bound_box:
        w=obj.matrix_world @ mathutils.Vector(c)
        for i in range(3): lo[i]=min(lo[i],w[i]); hi[i]=max(hi[i],w[i])
    L=hi[0]-lo[0]; xc=(lo[0]+hi[0])/2; yc=(lo[1]+hi[1])/2
    for v in obj.data.vertices: v.co.x-=xc; v.co.y-=yc
    wl=float(ship["metadata"].get("draught_m") or (hi[2]-lo[2])*0.4)
    topz=hi[2]-wl
    # material: painted steel
    for slot in obj.material_slots:
        m=slot.material
        if m and m.use_nodes:
            b=m.node_tree.nodes.get("Principled BSDF")
            if b:
                b.inputs["Roughness"].default_value=0.55
                if "Metallic" in b.inputs: b.inputs["Metallic"].default_value=0.25
    # sea
    bpy.ops.mesh.primitive_plane_add(size=L*5, location=(0,0,wl))
    sea=bpy.context.active_object; sm=bpy.data.materials.new("sea"); sm.use_nodes=True
    sb=sm.node_tree.nodes.get("Principled BSDF")
    sb.inputs["Base Color"].default_value=(0.05,0.12,0.20,1); sb.inputs["Roughness"].default_value=0.22
    sea.data.materials.append(sm)
    # camera: proven turntable ratios scaled by L/247, target just above waterline
    r=L/247.0
    tgt=bpy.data.objects.new("t",None); sc.collection.objects.link(tgt); tgt.location=(0,0,wl+topz*0.30)
    cd=bpy.data.cameras.new("c"); cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
    cam.location=(300*r, -340*r, (wl+150*r)); cd.clip_end=40000; cd.lens=62
    con=cam.constraints.new("TRACK_TO"); con.target=tgt
    # lights + world
    sd=bpy.data.lights.new("s",type="SUN"); s=bpy.data.objects.new("s",sd); sc.collection.objects.link(s)
    s.rotation_euler=(math.radians(52),0,math.radians(35)); sd.energy=4.5
    w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True
    w.node_tree.nodes["Background"].inputs["Color"].default_value=(0.09,0.14,0.20,1)
    rn=sc.render; rn.resolution_x=800; rn.resolution_y=500
    for e in("BLENDER_EEVEE_NEXT","BLENDER_EEVEE"):
        try: rn.engine=e; break
        except: pass
    rn.image_settings.file_format="PNG"; rn.filepath=f"{OUT}/{slug}.png"
    bpy.ops.render.render(write_still=True); print("THUMB",slug)
print("done")
