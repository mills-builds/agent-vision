"""BusLinker V3.0 mount - clips onto riser B's column (+x OR -x end) right under the top taper. B is NOT modified.
Attach: U-clip; plate sits outboard of B's end rib (x 35..45), two 2.5 mm arms run back along the long faces
outside the side ribs (x 18..22, y 25..31) and 45-deg lead-in hooks snap behind those ribs (contact face x=18).
1x kit M3x6 self-taps into a 2.6 pilot in the plate centre boss and bears on the end-rib face -> tensions arms
against hooks = friction clamp. Taper above stops it rising; clamp holds it from sliding down.
Board: 42x33 [V Hiwonder spec], holes 36x28 [V spec] on 4 kit M2.5x10 nylon standoffs; plate has BOTH 36x28 and
28x36 patterns (2.7 clearance) so the board can go landscape or portrait; M2.5 screws from behind into the F-F standoffs (heads in 1 mm
counterbores, sit in the 10 mm gap between plate and column face beside the 4 mm end rib), M2.5x4 from the front into the standoffs.
Modelled in riser-B frame (B joint face z=0, assembled z = +150). Printed upside down (plate top on bed), no supports.
ASSEMBLY ORDER: 1) 4 rear M2.5 through plate, spin standoffs on; 2) back M3 out, snap clip on; 3) snug M3;
4) board on with 4 front M2.5 (remove board to re-tighten M3). Cable-tie the 12 V lead to the column.
Run: .venv/bin/python buslinker_mount.py"""
import cadquery as cq, os
TAPER0 = 142 - 8 - 1.2*(117-70)/2          # 105.8: B column -> taper start (B frame)
RIB_IN, RIB_OUT, RIB_Y = 18.0, 45.0, 31.0  # side-rib inner face x, end-rib outer face x, side-rib outer y
GAP = 0.6                                  # plate inner face standoff from end rib (taken up by M3 tip)
T_PL, T_ARM, HOOK = 3.0, 2.5, 2.7
X0 = RIB_OUT + GAP; X1 = X0 + T_PL         # plate 45.6..48.6 (FDM snap slack)
Y_IN = RIB_Y + 0.2; Y_OUT = Y_IN + T_ARM   # arms 31.2..33.7
ZT = TAPER0 + 4.0                          # top (clears taper: plate ok to +12.7, hooks to +4.85; ~1 mm vertical play, lips take the load)
H = 46.0; ZB = ZT - H
ZC = ZT - H/2

import math
def tear(r, x0, y, z, L=10):
    """horizontal hole along +x, teardrop apex toward model -z (= up when printed upside down)"""
    # build in (Y,Z) plane: circle arc from -45..225 deg on the +z side, then apex at -z*r*sqrt2
    arc=[(r*math.cos(math.radians(d)), r*math.sin(math.radians(d))) for d in range(-45, 226, 15)]
    prof=arc+[(0, -r*math.sqrt(2))]
    return cq.Workplane("YZ").polyline(prof).close().extrude(L).translate((x0, y, z))
def prism(pts, z0, h):
    return cq.Workplane("XY").polyline(pts).close().extrude(h).translate((0, 0, z0))

prof = [(X1, -Y_OUT), (X1, Y_OUT), (RIB_IN - 4.2, Y_OUT),
        (RIB_IN - 4.2 + 0.0, Y_IN),        # 45-deg lead-in starts here
        (RIB_IN - 1.7, Y_IN - HOOK), (RIB_IN, Y_IN - HOOK), (RIB_IN, Y_IN), (X0, Y_IN),
        (X0, -Y_IN), (RIB_IN, -Y_IN), (RIB_IN, -Y_IN + HOOK), (RIB_IN - 1.7, -Y_IN + HOOK),
        (RIB_IN - 4.2, -Y_IN), (RIB_IN - 4.2, -Y_OUT)]
ARM_H = 22.0
clip = prism(prof, ZT - ARM_H, ARM_H)                         # arms + hooks + top of plate
clip = clip.union(cq.Workplane("XY").box(T_PL, 2*Y_OUT, H, centered=(False, True, False)).translate((X0, 0, ZB)))
# lower corners of plate trimmed to board size (save filament)
for s in (-1, 1):
    clip = clip.cut(cq.Workplane("XY").box(10, Y_OUT - 25, H - ARM_H, centered=(True, False, False))
                    .translate((X0 + 1.5, 25 if s > 0 else -Y_OUT, ZB)) )
# [review fix] positive down-stop: lips resting on the tops of B's side ribs (z=TAPER0+1) and end rib
RIB_TOP = TAPER0 + 1.0
for sy in (-1, 1):
    clip = clip.union(cq.Workplane("XY").box(22.0 - (RIB_IN - 4.2), Y_IN - (Y_IN - HOOK), ZT - RIB_TOP - 0.2, centered=False)
                      .translate((RIB_IN - 4.2, (Y_IN - HOOK) if sy > 0 else -Y_IN, RIB_TOP + 0.2)))
clip = clip.union(cq.Workplane("XY").box(X0 - 40.0, 4.0, ZT - RIB_TOP - 0.2, centered=(False, True, False)).translate((40.0, 0, RIB_TOP + 0.2)))
# [review fix] 1.5 mm corner gussets arm/plate (inner corner, tension side of snap)
for sy in (-1, 1):
    clip = clip.union(prism([(X0, sy*Y_IN), (X0 - 1.5, sy*Y_IN), (X0, sy*(Y_IN - 1.5))], ZT - ARM_H, ARM_H))
# M3 boss + pilot at centre, bears on end rib
clip = clip.union(cq.Workplane("YZ").rect(5.6, 5.6).extrude(1.0).rotate((0,0,0),(1,0,0),45).translate((X1, 0, ZC)))
clip = clip.cut(tear(1.3, X0 - 1, 0, ZC))
# lightening windows between hole rows (not through the boss)
for s in (-1, 1):
    clip = clip.cut(cq.Workplane("YZ").rect(7, 22).extrude(10).translate((X0 - 1, s*9.5, ZC)))
HOLES = sorted({(sy*a/2, sz*b/2) for a, b in ((36, 28), (28, 36)) for sy in (-1, 1) for sz in (-1, 1)})
for y, z in HOLES:
    clip = clip.cut(tear(1.45, X0 - 1, y, ZC + z))
    clip = clip.cut(tear(2.8, X0 - 1, y, ZC + z, L=2.0))   # 5.6 x 1.0 deep (delete if kit screws >= M2.5x6) counterbore -> ~2 mm thread in standoff

# --- board + standoffs (render only), landscape: 42 along y, 33 along z, servo JST edge up
SO = 10.0; BX = X1 + SO
board = cq.Workplane("XY").box(1.6, 42, 33).translate((BX + 0.8, 0, ZC))
for y in (-8, 0, 8):
    board = board.union(cq.Workplane("XY").box(6, 6, 5).translate((BX + 1.6 + 3, y, ZC + 16.5 - 2.5)))   # JST
# real layout: DC jack + terminal block + USB-C all on the LOWER long edge (cables exit downward, clear of clip),
# 3 servo ports on the UPPER long edge (cables up to base servo), header/jumper on a short edge (+y)
EB = ZC - 16.5
board = board.union(cq.Workplane("XY").box(11, 9, 6.5, centered=(False, True, False)).translate((BX + 1.6, -13, EB - 1.5)))   # DC jack, opening down
board = board.union(cq.Workplane("XY").box(8, 10, 7, centered=(False, True, False)).translate((BX + 1.6, 0, EB + 0.5)))     # terminal block
board = board.union(cq.Workplane("XY").box(3.3, 9, 7, centered=(False, True, False)).translate((BX + 1.6, 13, EB - 0.8)))   # USB-C, opening down
board = board.union(cq.Workplane("XY").box(2.5, 2.5, 10).translate((BX + 1.6 + 4.5, 19.5, ZC)))                            # header/jumper, short edge
stand = None
for y, z in [(sy*18, sz*14) for sy in (-1, 1) for sz in (-1, 1)]:
    s = cq.Workplane("YZ").polygon(6, 5.0).extrude(SO).translate((X1, y, ZC + z))
    stand = s if stand is None else stand.union(s)

os.makedirs("stl", exist_ok=True)
pr = clip.rotate((0, 0, 0), (1, 0, 0), 180)                   # upside down: top face on bed
bb = pr.val().BoundingBox(); pr = pr.translate((0, 0, -bb.zmin))
cq.exporters.export(pr, "stl/buslinker_mount.stl", tolerance=0.02, angularTolerance=0.1)
cq.exporters.export(clip, "stl/_bl_clip_inplace.stl"); cq.exporters.export(board, "stl/_bl_board.stl"); cq.exporters.export(stand, "stl/_bl_standoffs.stl")
b = clip.val().BoundingBox(); v = clip.val().Volume()
print(f"clip {b.xlen:.1f} x {b.ylen:.1f} x {b.zlen:.1f}  B-frame z {b.zmin:.1f}..{b.zmax:.1f} (assembled {b.zmin+150:.1f}..{b.zmax+150:.1f})")
print(f"vol {v/1000:.2f} cm3 -> solid PLA {v/1000*1.24:.1f} g; ~{v/1000*1.24*0.85:.1f} g at 4 walls/20% infill (thin part ~mostly perimeters)")
print("board top edge assembled z", ZC + 16.5 + 150, " board outer x", BX + 1.6)
