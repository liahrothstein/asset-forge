# blender_process.py — ФАЗА 3: оптимизация меша под игру
# Запуск: blender --background --python blender_process.py -- in.obj out.glb 20000 1024 [log] [ref.png]
import bpy, bmesh, sys, math
from pathlib import Path

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, DST = argv[0], argv[1]
TARGET_TRIS, BAKE_RES = int(argv[2]), int(argv[3])
LOG_PATH  = argv[4] if len(argv) > 4 else None   # зарезервировано, лог ведёт батник
REF_PATH  = argv[5] if len(argv) > 5 else None   # референс для проекции (Hunyuan)
# Маркер фазы 2: что делало меши ("hunyuan" = без текстур, всегда проекция)
_mode_file = Path(SRC).parent.parent / "mode.txt"
PIPELINE_MODE = _mode_file.read_text(encoding="utf-8").strip() if _mode_file.exists() else ""
print(f"[diag] SRC={SRC!r}")
print(f"[diag] маркер: файл={_mode_file} есть={_mode_file.exists()} значение={PIPELINE_MODE!r}")

bpy.ops.wm.read_homefile(use_empty=True)

# --- 1. Импорт исходного OBJ
bpy.ops.wm.obj_import(filepath=SRC)

# --- 2. Склеиваем все части в один меш
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1:
    bpy.ops.object.join()
high = bpy.context.active_object
high.name = "High"

# --- 3. Счётчик треугольников
def count_tris(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    n = sum(len(f.edges) - 2 for f in bm.faces)
    bm.free()
    return n

n_tris = count_tris(high)
print(f"Исходный меш: {n_tris} полигонов")

# --- 4. Копия + Decimate до целевого числа полигонов
bpy.ops.object.select_all(action='DESELECT')
high.select_set(True)
bpy.context.view_layer.objects.active = high
bpy.ops.object.duplicate()
low = bpy.context.active_object
low.name = "Low"
ratio = max(0.001, min(1.0, TARGET_TRIS / max(n_tris, 1)))
mod = low.modifiers.new("Decimate", 'DECIMATE')
mod.ratio = ratio
bpy.context.view_layer.objects.active = low
bpy.ops.object.modifier_apply(modifier="Decimate")
print(f"После decimate: {count_tris(low)} полигонов (цель {TARGET_TRIS})")

# --- 4b. Сглаживание: убирает ступеньки marching cubes
sm = low.modifiers.new("Smooth", 'SMOOTH')
sm.factor = 0.5
sm.iterations = 3
bpy.context.view_layer.objects.active = low
bpy.ops.object.modifier_apply(modifier="Smooth")

# --- Определяем: есть ли у исходника текстура?
def high_has_texture(obj):
    for m in obj.data.materials:
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image:
                    px = list(n.image.pixels[:4])  # первые пиксели
                    # Пустая текстура = все пиксели чёрные/прозрачные/белые
                    if any(abs(c) > 0.02 for c in px[:3]) and not all(abs(c - 1.0) < 0.02 for c in px[:3]):
                        return True
    return False

if PIPELINE_MODE == "hunyuan":
    USE_PROJECTION = bool(REF_PATH)
else:
    USE_PROJECTION = (not high_has_texture(high)) and bool(REF_PATH)
print("Режим:", "проекция референса (Hunyuan)" if USE_PROJECTION else "запекание с high (TripoSR)")

# --- 4c. ПРОЕКЦИЯ: натягиваем референс-картинку на меш фронтально
if USE_PROJECTION:
    # Ориентация мешей Hunyuan: up=+Y, front=+Z.
    # Если текстура легла не тем боком — меняйте знаки/оси:
    FRONT_AXIS, FRONT_SIGN = 2, 1   # фронт смотрит в +Z
    UP_AXIS,    UP_SIGN    = 1, 1   # вверх это +Y
    import numpy as np
    me = low.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uvl = me.uv_layers.active.data
    co = np.array([v.co[:] for v in me.vertices])
    horiz = ({0, 1, 2} - {FRONT_AXIS, UP_AXIS}).pop()
    hmin, hmax = co[:, horiz].min(), co[:, horiz].max()
    vmin, vmax = co[:, UP_AXIS].min(), co[:, UP_AXIS].max()
    for poly in me.polygons:
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            u = (c[horiz] - hmin) / (hmax - hmin + 1e-9)
            if FRONT_SIGN < 0:
                u = 1.0 - u
            v = (c[UP_AXIS] - vmin) / (vmax - vmin + 1e-9)
            uvl[li].uv = (u, v)
    img = bpy.data.images.load(str(Path(REF_PATH).resolve()))
    mat = bpy.data.materials.new("ref_proj")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], outn.inputs["Surface"])
    low.data.materials.clear()
    low.data.materials.append(mat)
else:
    # --- 5. (TripoSR) Свежая UV-развертка для low-poly
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')

    # --- 6. (TripoSR) Материал с чистой текстурой под запекание
    img = bpy.data.images.new("baked", BAKE_RES, BAKE_RES)
    mat = bpy.data.materials.new("asset_mat")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out_node = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])
    low.data.materials.clear()
    low.data.materials.append(mat)
    nt.nodes.active = tex

    # --- 7. (TripoSR) Запекание цвета с high-poly на low-poly
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = 'GPU'
        print("Запекание на GPU (OPTIX)")
    except Exception as e:
        print("GPU не настроился, печём на CPU:", e)
    scene.cycles.samples = 16
    scene.cycles.max_bounces = 2

    bpy.ops.object.select_all(action='DESELECT')
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.bake(type='DIFFUSE',
                        pass_filter={'COLOR'},
                        use_selected_to_active=True,
                        margin=8)
    img.pack()

# --- 8. Экспорт только low-poly
bpy.ops.object.select_all(action='DESELECT')
low.select_set(True)
bpy.context.view_layer.objects.active = low
bpy.ops.export_scene.gltf(filepath=DST, export_format='GLB',
                          use_selection=True, export_apply=True)
print(f"OK: {DST} | {count_tris(low)} полигонов | "
      + ("проекция референса" if USE_PROJECTION else f"запечённая текстура {BAKE_RES}px"))