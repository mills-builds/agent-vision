"""SO-101 base -> riser B adapter, v2 (no drilling, hole patterns treated as unverified).
Riser side : plate drops over riser B's 117x93 top plate (skirt, 0.4 clearance/side) -> located by the outline.
             4x M5x30 hex + M5x15 fender on top of an M8x24 fender washer through 14 mm holes (+-4.25 mm any direction)
             into riser B's existing captive nuts. Heads flush in 26 mm counterbores.
Arm side   : no base holes used. Two printed strap clamps grip the base's flat 12.4 mm side wings
             (x=+-55.5, flat out to the edge) and hook its rear corners and the start of the front slant.
             Each clamp (strap clamp: lip preloaded 0.375 mm, outer heel on the plate): 2x M5x30 hex + M5x15 fender washer through 8.5x13.5 slots (+-4 in x, +-1.5 in y)
             into M5 nuts held in hex pockets in the plate underside (outside the riser).
Frames: riser frame, z=0 riser top face; plate top z=12; base frame (bbox centre, z=0 rib bottom) maps to
(x, y+18, z+12) so the pan axis (base (0,-18)) is over the riser centre.
Print: plate TOP FACE DOWN; clamps TOP FACE DOWN. No supports.
"""
import os, numpy as np, cadquery as cq
from shapely.geometry import Polygon

RISER = (117.0, 93.0); SK_CLR, SK_WALL, SK_H = 0.4, 2.5, 6.0
RISER_HOLES = [(-31.75, 34.82), (31.75, 34.82), (-27.78, -34.96), (27.78, -34.96)]   # nominal; +-4 tolerated
T = 12.0; BASE_DY = 18.0; BASE_H = 12.4
RB_HOLE, RB_CB, RB_CB_D = 14.0, 30.0, 7.0      # riser bolt: hole / cbore dia (lets the 24 mm M8 fender follow the bolt +-4.25) / depth (M8 fender 1.6 + M5x15 fender 1.6 + head 3.5)
LIP_T = 4.0; NOTCH_H = 12.0; RELIEF = 0.8; HEEL_X = 72.0   # strap clamp: lip 0.375 below wing top (preload), only the outer heel x>=72 touches the plate
CL_BOLT_X = 66.5; CL_BOLT_Y = [22.0, 54.0]      # clamp bolt positions (riser frame), outside riser + skirt
SLOT_W, SLOT_L = 8.5, 13.5
NUT_AF, NUT_H = 8.1, 4.4   # 8.1 AF = light press fit for an 8 mm M5 nut

OUT = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../hiwonder/base_outline_dz6.npy'))
base_poly = Polygon(OUT + [0, BASE_DY]).buffer(0)
base_clr = base_poly.buffer(0.4, join_style=2)

xo = RISER[0]/2 + SK_CLR + SK_WALL                # 61.4 skirt outer
X_MAX = CL_BOLT_X + SLOT_L/2 + 5                   # plate half-width
y_min = -RISER[1]/2 - SK_CLR - SK_WALL - 3.0
y_max = max(base_poly.bounds[3] + 6, CL_BOLT_Y[1] + 10) + 4

def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1-x0, y1-y0, z1-z0, centered=False).translate((x0, y0, z0))
def cyl(x, y, d, z0, z1):
    return cq.Workplane("XY").center(x, y).circle(d/2).extrude(z1-z0).translate((0, 0, z0))
def prism(poly, z0, z1):
    pts = list(poly.exterior.coords)[:-1]
    return cq.Workplane("XY").polyline(pts).close().extrude(z1-z0).translate((0, 0, z0))
def slot(x, y, w, l, z0, z1):   # long axis along x
    return cq.Workplane("XY").center(x, y).slot2D(l, w, 0).extrude(z1-z0).translate((0, 0, z0))

# ---------------- plate ----------------
plate = box(-X_MAX, X_MAX, y_min, y_max, 0, T).edges("|Z").fillet(6)
xi, yi = RISER[0]/2 + SK_CLR, RISER[1]/2 + SK_CLR
plate = plate.union(box(-xo, xo, -yi - SK_WALL, yi + SK_WALL, -SK_H, 0.01).cut(box(-xi, xi, -yi, yi, -SK_H - 1, 0.02)))
for x, y in RISER_HOLES:
    plate = plate.cut(cyl(x, y, RB_HOLE, -1, T + 1)).cut(cyl(x, y, RB_CB, T - RB_CB_D, T + 1))
    zc = T - RB_CB_D   # sacrificial bridge steps (prints face-down)
    plate = plate.cut(box(x - RB_HOLE/2, x + RB_HOLE/2, y - RB_CB/2, y + RB_CB/2, zc - 0.3, zc + 0.01))
    plate = plate.cut(box(x - RB_HOLE/2, x + RB_HOLE/2, y - RB_HOLE/2, y + RB_HOLE/2, zc - 0.6, zc + 0.01))
for sx in (-1, 1):
    for y in CL_BOLT_Y:
        x = sx*CL_BOLT_X
        plate = plate.cut(cyl(x, y, 5.5, -1, T + 1))
        plate = plate.cut(cq.Workplane("XY").center(x, y).polygon(6, NUT_AF/0.8660254).extrude(NUT_H).translate((0, 0, -0.01)))

arrow = cq.Workplane("XY").polyline([(-1.5, -32), (1.5, -32), (1.5, -41), (4, -41), (0, -47), (-4, -41), (-1.5, -41)]).close().extrude(0.7).translate((0, 0, T - 0.6))
plate = plate.cut(arrow)   # engraved arrow = arm FRONT (servo end of the base)
# ---------------- clamp (+x side; mirror for -x) ----------------
Z0 = T; ZT = T + BASE_H + LIP_T
cy0 = -14.0 + BASE_DY; cy1 = y_max - 5.0   # engages ~11 mm of the base's front slant
cx0 = 49.5; cx1 = CL_BOLT_X + SLOT_L/2 + 3.5
clamp = box(cx0, cx1, cy0, cy1, Z0, ZT)
clamp = clamp.cut(prism(base_clr, Z0 - 1, Z0 + NOTCH_H))                        # base body (wing) notch
clamp = clamp.cut(box(cx0 - 1, HEEL_X, cy0 - 1, cy1 + 1, Z0 - 1, Z0 + RELIEF))  # relieve all but the outer heel
for y in CL_BOLT_Y:
    clamp = clamp.cut(cq.Workplane("XY").center(CL_BOLT_X, y).rect(SLOT_L - SLOT_W, SLOT_W).extrude(ZT - Z0 + 2).translate((0, 0, Z0 - 1))
                      .union(cyl(CL_BOLT_X - (SLOT_L - SLOT_W)/2, y, SLOT_W, Z0 - 1, ZT + 1))
                      .union(cyl(CL_BOLT_X + (SLOT_L - SLOT_W)/2, y, SLOT_W, Z0 - 1, ZT + 1)))

clamp_L = clamp.mirror("YZ")

if __name__ == "__main__":
    os.makedirs("stl", exist_ok=True)
    cq.exporters.export(plate, "stl/arm_adapter_plate_v2.stl", tolerance=0.05, angularTolerance=0.1)
    cq.exporters.export(clamp, "stl/arm_adapter_clamp_v2_R.stl", tolerance=0.05, angularTolerance=0.1)
    cq.exporters.export(clamp_L, "stl/arm_adapter_clamp_v2_L.stl", tolerance=0.05, angularTolerance=0.1)
    for n, p in (("plate", plate), ("clamp", clamp)):
        bb = p.val().BoundingBox(); print(n, f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} z {bb.zmin:.1f}..{bb.zmax:.1f} vol {p.val().Volume()/1000:.1f} cm3")
    print("plate y", round(y_min, 1), round(y_max, 1), "x +-", X_MAX, "base outline", np.round(base_poly.bounds, 1))
