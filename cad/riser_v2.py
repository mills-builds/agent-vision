"""Bench camera arm riser v2 -- support-free redesign.
Every part prints in its exported orientation with no supports: overhangs replaced by
tapers steeper than 45 deg (rise = TAPER_K * run), joint/arm bolts go into M5 heat-set inserts
in solid tapered tops (no nut access needed under an overhang).
Run: .venv/bin/python bench_arm_v2.py -> stl/*.stl
"""
import os, cadquery as cq

CL = 0.25
TAPER_K = 1.2           # rise/run for every taper -> 39.8 deg from vertical (< 45)
BASE_HOLES = [(-31.75, 34.82), (31.75, 34.82), (-27.78, -34.96), (27.78, -34.96)]  # [M] SO-101 base
TOP_PLATE = (117.0, 93.0)
JOIN = (110.0, 90.0); JOIN_HOLES = [(sx*45, sy*32) for sx in (-1, 1) for sy in (-1, 1)]
M5_CLR = 5.5
NUT_AF, NUT_H = 8.4, 4.4   # M5 hex nut 8 AF x 4 + clearance; captive pocket + side slot to the outside
NUT_TOP = 11.0             # joint/arm face -> top of nut pocket (8 flange + 3 solid ceiling)
TAIL = 12.0                # 5.5 hole continues this far below the pocket for bolt tail
FL_T = 8.0; COL = (70.0, 50.0); WALL = 4.0
KEY_H, KEY_O, KEY_I = 8.0, (60.0, 40.0), (46.0, 26.0)
SOCK = (KEY_O[0]+0.5, KEY_O[1]+0.5)  # 60.5 x 40.5
FOOT = (220.0, 140.0, 8.0); PAD_L = 45.0
A_BODY = 150.0           # foot bottom -> joint face
B_BODY = 292.0 - A_BODY  # joint face -> arm face = 142
BORE_A = (COL[0]-2*WALL, COL[1]-2*WALL)   # 62 x 42

def box(x, y, h, z0=0, cx=0, cy=0):
    return cq.Workplane("XY").center(cx, cy).rect(x, y).extrude(h).translate((0, 0, z0))

def loft(b, t, z0, h):
    return (cq.Workplane("XY").workplane(offset=z0).rect(*b)
            .workplane(offset=h).rect(*t).loft(combine=True))

def taper_h(b, t):
    return TAPER_K*max(abs(t[0]-b[0]), abs(t[1]-b[1]))/2

def holes(s, pts, d, h, z0):
    for x, y in pts:
        s = s.cut(cq.Workplane("XY").center(x, y).circle(d/2).extrude(h).translate((0, 0, z0)))
    return s

def column(h, z0):
    c = box(*COL, h)
    for x in (-20, 20):
        for sy in (-1, 1):
            c = c.union(box(4, 6, h, cx=x, cy=sy*(COL[1]/2+3)))
    for sx in (-1, 1):
        c = c.union(box(10, 4, h, cx=sx*(COL[0]/2+5)))
    return c.translate((0, 0, z0))   # solid; bores are cut at the end

# ---------------- Section A: printed upright, foot on bed ----------------
fx, fy, ft = FOOT
foot = cq.Workplane("XY").rect(fx, fy).extrude(ft).edges("|Z").fillet(8)
for y in (-COL[1]/2+2, COL[1]/2-2, -52, 52):
    foot = foot.union(box(fx-2*PAD_L, 4, 20, ft, cy=y))
for x in (-COL[0]/2-2, COL[0]/2+2):
    foot = foot.union(box(4, fy-10, 20, ft, cx=x))
thA = taper_h(COL, JOIN)                       # 24 mm
zt0 = A_BODY - FL_T - thA
A = (foot.union(column(zt0 - ft + 1, ft))
     .union(loft(COL, JOIN, zt0, thA))
     .union(box(*JOIN, FL_T, A_BODY - FL_T))
     .union(box(*KEY_O, KEY_H, A_BODY)))       # spigot up (gender swapped vs v1)
# bore: 62x42 straight, then 45-deg-safe taper in to 46x26 below the joint face, open through spigot
ib_h = taper_h(BORE_A, KEY_I)                   # 9.6
zi0 = A_BODY - 4 - ib_h
A = A.cut(box(*BORE_A, zi0)).cut(loft(BORE_A, KEY_I, zi0, ib_h)).cut(box(*KEY_I, 50, zi0 + ib_h - 0.01))

def nut_traps(s, pts, face_z, axis):
    """5.5 thru hole from face_z down, hex pocket NUT_TOP below face, slot out along +-axis."""
    zt = face_z - NUT_TOP; zb = zt - NUT_H
    for x, y in pts:
        s = s.cut(cq.Workplane("XY").center(x, y).circle(M5_CLR/2).extrude(NUT_TOP + NUT_H + TAIL).translate((0, 0, zb - TAIL)))
        rot = 0 if axis == "x" else 90          # polygon vertex on +x -> flats face +-y (x-slot)
        hexp = cq.Workplane("XY").polygon(6, NUT_AF/0.8660254).extrude(NUT_H).rotate((0,0,0),(0,0,1),rot).translate((x, y, zb))
        L = 40.0
        if axis == "x":
            sl = box(L, NUT_AF, NUT_H, zb, cx=x + (L/2 if x > 0 else -L/2), cy=y)
        else:
            sl = box(NUT_AF, L, NUT_H, zb, cx=x, cy=y + (L/2 if y > 0 else -L/2))
        s = s.cut(hexp.union(sl))
    return s
A = nut_traps(A, JOIN_HOLES, A_BODY, "x")

# ---------------- Section B: printed upright, joint flange on bed ----------------
thB = taper_h(COL, TOP_PLATE)                   # 28.2
zb0 = B_BODY - FL_T - thB
B = (box(*JOIN, FL_T)
     .union(column(zb0 - FL_T + 1, FL_T))
     .union(loft(COL, TOP_PLATE, zb0, thB))
     .union(box(*TOP_PLATE, FL_T, B_BODY - FL_T)))
# gussets on the bed flange (upward-narrowing triangles -> no overhang), clear of bolt heads
def gus(axis, sgn, start, end, h, pos):
    pts = [(start, FL_T), (end, FL_T), (start, FL_T + h)]
    if axis == "y":
        return cq.Workplane("YZ").polyline([(sgn*a, z) for a, z in pts]).close().extrude(2, both=True).translate((pos, 0, 0))
    return cq.Workplane("XZ").polyline([(sgn*a, z) for a, z in pts]).close().extrude(2, both=True).translate((0, pos, 0))
for x in (-20, 20):
    for s in (-1, 1):
        B = B.union(gus("y", s, COL[1]/2 + 5.5, JOIN[1]/2, 22, x))
for s in (-1, 1):
    B = B.union(gus("x", s, COL[0]/2 + 9.5, JOIN[0]/2, 22, 0))
B = B.cut(box(*SOCK, B_BODY + 1, -0.5))         # straight bore = socket for A's spigot, cable path
B = holes(B, JOIN_HOLES, M5_CLR, FL_T, 0)
B = nut_traps(B, BASE_HOLES, B_BODY, "y")

os.makedirs("stl", exist_ok=True)
for n, p in {"riser_A_foot_v2": A, "riser_B_top_v2": B}.items():
    cq.exporters.export(p, f"stl/{n}.stl", tolerance=0.05, angularTolerance=0.1)
    bb = p.val().BoundingBox()
    print(f"{n:16s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:6.1f}  z {bb.zmin:.1f}..{bb.zmax:.1f} vol {p.val().Volume()/1000:6.1f} cm3")
print("stack: A joint face", A_BODY, "+ B", B_BODY, "=", A_BODY + B_BODY)

# quick test coupon: top 40 mm of A (taper + flange + insert holes + spigot), printed alone first
T = A.intersect(box(300, 300, 40, 118)).translate((0, 0, -118))
cq.exporters.export(T, "stl/test_A_top_taper.stl", tolerance=0.05, angularTolerance=0.1)
print("test coupon vol", round(T.val().Volume()/1000, 1), "cm3")
