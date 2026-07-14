# Blender headless turntable render of the Amagi full-ship model.
# run: Blender --background --python render_anim.py
import bpy, math

OBJ="/Users/nakamura/git/ndl/ai/amagi_cad/amagi_fullship.obj"
OUT="/Users/nakamura/git/ndl/ai/amagi_cad/amagi_turntable.mp4"
LWL_Z=9.53  # design waterline height (m) above keel

bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene

bpy.ops.wm.obj_import(filepath=OBJ)
meshes=[o for o in scene.objects if o.type=='MESH']
bpy.context.view_layer.objects.active=meshes[0]
for o in meshes: o.select_set(True)
if len(meshes)>1: bpy.ops.object.join()
ship=bpy.context.view_layer.objects.active
ship.name="Amagi"

# center horizontally, keep keel at z=0 (bake into mesh)
xs=[v.co.x for v in ship.data.vertices]; ys=[v.co.y for v in ship.data.vertices]
xc=(min(xs)+max(xs))/2; yc=(min(ys)+max(ys))/2
for v in ship.data.vertices: v.co.x-=xc; v.co.y-=yc
ship.location=(0,0,0); ship.rotation_mode='XYZ'

# keep per-component materials imported from the .mtl (do not override);
# just make them a touch rougher/metallic for a painted-steel look
for slot in ship.material_slots:
    m=slot.material
    if not m or not m.use_nodes: continue
    b=m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Roughness"].default_value=0.55
        if "Metallic" in b.inputs: b.inputs["Metallic"].default_value=0.25

# sea plane at waterline
bpy.ops.mesh.primitive_plane_add(size=1500, location=(0,0,LWL_Z))
sea=bpy.context.active_object
sm=bpy.data.materials.new("sea"); sm.use_nodes=True
sb=sm.node_tree.nodes.get("Principled BSDF")
sb.inputs["Base Color"].default_value=(0.02,0.08,0.16,1)
sb.inputs["Roughness"].default_value=0.12
if "Metallic" in sb.inputs: sb.inputs["Metallic"].default_value=0.3
sea.data.materials.append(sm)

# camera + track target
tgt=bpy.data.objects.new("tgt",None); scene.collection.objects.link(tgt); tgt.location=(0,0,12)
cd=bpy.data.cameras.new("cam"); cam=bpy.data.objects.new("cam",cd)
scene.collection.objects.link(cam); scene.camera=cam
cam.location=(300,-340,150); cd.clip_end=8000; cd.lens=60
con=cam.constraints.new("TRACK_TO"); con.target=tgt

# lights + world
sd=bpy.data.lights.new("sun",type="SUN"); sun=bpy.data.objects.new("sun",sd)
scene.collection.objects.link(sun); sun.rotation_euler=(math.radians(52),0,math.radians(35)); sd.energy=4.5
world=bpy.data.worlds.new("w"); scene.world=world; world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.06,0.09,0.13,1)

# turntable animation (ship spins on Z) — linear interpolation for constant speed
try: bpy.context.preferences.edit.keyframe_new_interpolation_type="LINEAR"
except Exception: pass
scene.frame_start=1; scene.frame_end=120
ship.rotation_euler=(0,0,0);                ship.keyframe_insert("rotation_euler",frame=1)
ship.rotation_euler=(0,0,math.radians(360));ship.keyframe_insert("rotation_euler",frame=121)

# render settings
r=scene.render
r.resolution_x=1280; r.resolution_y=720; r.fps=30
for eng in ("BLENDER_EEVEE_NEXT","BLENDER_EEVEE"):
    try: r.engine=eng; break
    except Exception: pass
r.image_settings.file_format="PNG"
r.filepath="/Users/nakamura/git/ndl/ai/amagi_cad/frames/f_"
print("ENGINE:",r.engine,"-> rendering",scene.frame_end,"frames (PNG seq)")
bpy.ops.render.render(animation=True)
print("DONE frames")
