"""Rebuild models/so101-camera-arm.glb with the current (v2) printed parts.

Keeps the SO-101 link and servo meshes from the existing GLB and replaces / adds:
  riser_A_foot, riser_B_top           riser v2, in the riser frame (A z 0..158, B modelled z 0..142)
  arm_adapter_plate, clamp_L, clamp_R adapter v2, riser-top frame (z=0 = riser B top face)
  buslinker_mount, buslinker_board, buslinker_standoffs   riser-B frame (B joint face z=0)
  camera_plate                         v3 rev c, z=0 = horn boss face, camera side +z
Positions are stored in metres in each part's own frame; docs/index.html places them.
The adapter / clamp / BusLinker meshes are the "in place" exports from the CAD scripts
(same geometry as cad/stl, before rotating to print orientation).

Usage: python3 tools/build_explainer_glb.py [CAD_V2_DIR]   (default /workspace/bench-arm/cad-v2)
Then re-embed: python3 tools/build_explainer_glb.py --embed
"""
import base64, json, os, re, struct, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLB = os.path.join(ROOT, "models/so101-camera-arm.glb")
HTML = os.path.join(ROOT, "docs/index.html")


def read_stl(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("x", "<u2")]))
    v = a["v"].reshape(-1, 3).astype(np.float64)
    key = np.round(v, 4)
    uniq, idx = np.unique(key, axis=0, return_inverse=True)
    return (uniq / 1000.0).astype(np.float32), idx.reshape(-1).astype(np.uint32)


def load_glb(path):
    b = open(path, "rb").read()
    jl = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + jl])
    bin_off = 20 + jl + 8
    return j, b[bin_off:bin_off + j["buffers"][0]["byteLength"]]


def main(src):
    j, binb = load_glb(GLB)
    parts = {
        "riser_A_foot": "stl/riser_A_foot_v2.stl",
        "riser_B_top": "stl/riser_B_top_v2.stl",
        "arm_adapter_plate": "stl/arm_adapter_plate_v2.stl",
        "clamp_L": "stl/arm_adapter_clamp_v2_L.stl",
        "clamp_R": "stl/arm_adapter_clamp_v2_R.stl",
        "buslinker_mount": "stl/_bl_clip_inplace.stl",
        "buslinker_board": "stl/_bl_board.stl",
        "buslinker_standoffs": "stl/_bl_standoffs.stl",
        "camera_plate": "stl/camera_plate_v3.stl",
    }
    # keep the arm meshes (everything not being replaced), copying their buffer data
    out = bytearray(); views = []; accs = []; meshes = []; nodes = []
    def add_view(data, target):
        while len(out) % 4: out.append(0)
        views.append({"buffer": 0, "byteOffset": len(out), "byteLength": len(data), "target": target}); out.extend(data)
        return len(views) - 1
    def add_mesh(name, pos, idx):
        pv = add_view(pos.tobytes(), 34962)
        accs.append({"bufferView": pv, "componentType": 5126, "count": len(pos), "type": "VEC3",
                     "min": pos.min(0).tolist(), "max": pos.max(0).tolist()})
        if len(pos) < 65536: idx, ct = idx.astype(np.uint16), 5123
        else: ct = 5125
        iv = add_view(idx.tobytes(), 34963)
        accs.append({"bufferView": iv, "componentType": ct, "count": len(idx), "type": "SCALAR"})
        meshes.append({"name": name, "primitives": [{"attributes": {"POSITION": len(accs) - 2}, "indices": len(accs) - 1}]})
        return len(meshes) - 1
    def copy_acc(i):
        a = dict(j["accessors"][i]); bv = j["bufferViews"][a["bufferView"]]
        data = binb[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]
        a["bufferView"] = add_view(data, bv.get("target", 34962)); accs.append(a); return len(accs) - 1
    mesh_map = {}
    for n in j["nodes"]:
        if n["name"] in parts: continue
        mi = n["mesh"]
        if mi not in mesh_map:
            m = j["meshes"][mi]; prims = []
            for p in m["primitives"]:
                prims.append({"attributes": {k: copy_acc(v) for k, v in p["attributes"].items()}, "indices": copy_acc(p["indices"])})
            meshes.append({"name": m["name"], "primitives": prims}); mesh_map[mi] = len(meshes) - 1
        nodes.append({"name": n["name"], "mesh": mesh_map[mi]})
    for name, rel in parts.items():
        pos, idx = read_stl(os.path.join(src, rel))
        nodes.append({"name": name, "mesh": add_mesh(name, pos, idx)})
    while len(out) % 4: out.append(0)
    gj = {"asset": dict(j["asset"], generator="agent-vision tools/build_explainer_glb.py"),
          "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}], "nodes": nodes, "meshes": meshes,
          "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(out)}]}
    js = json.dumps(gj, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    glb = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(out))
    glb += struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(out), 0x004E4942) + bytes(out)
    open(GLB, "wb").write(glb)
    print("wrote", GLB, len(glb), "bytes,", len(nodes), "nodes")


def embed():
    h = open(HTML).read()
    b64 = base64.b64encode(open(GLB, "rb").read()).decode()
    h2, n = re.subn(r'(<script type="application/octet-stream" id="glb">)[^<]*(</script>)', lambda m: m.group(1) + b64 + m.group(2), h)
    assert n == 1
    open(HTML, "w").write(h2); print("embedded into", HTML)


if __name__ == "__main__":
    if "--embed" in sys.argv: embed()
    else: main(sys.argv[1] if len(sys.argv) > 1 else "/workspace/bench-arm/cad-v2")
