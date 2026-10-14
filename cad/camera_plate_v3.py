"""Camera plate v3 (rev c) - kit-hardware only. Print = install orientation: boss (z=0) on bed, camera side up, no supports.
Horn: 4x kit M3x6 pan heads in deep counterbores from the deck (fit before the camera).
Camera: UC-A55 (38x38, holes 28x28 dia ~2.8, photo-measured) on 4 printed posts, 4x kit M2x6 self-tapping into 1.7 pilots.
-y edge: notch under the 4-pin JST connector + cable exit."""
import cadquery as cq
HORN_SQ=9.90; HORN_HOLE=3.4; BORE=6.1
BOSS_D=22.0; BOSS_H=4.0; CB_D=6.2; UNDER=2.0
BASE=14.0; TOP=36.0; S=BOSS_H+(TOP-BASE)/2       # solid 45-deg frustum to a 36x36 deck at z=15
CAM_P=28.0; POST_D=5.0; POST_H=4.5; PILOT=1.7; PILOT_D=POST_H+3.0
NX0, NX1, NY, ND = -11.2, 1.0, -11.0, 4.0        # connector notch x range, inner y, depth (JST at x~-6.6, 7.8 wide)
part=cq.Workplane("XY").circle(BOSS_D/2).extrude(BOSS_H)
part=part.union(cq.Workplane("XY").workplane(offset=BOSS_H).rect(BASE,BASE).workplane(offset=S-BOSS_H).rect(TOP,TOP).loft())
cp=[(sx*CAM_P/2,sy*CAM_P/2) for sx in(-1,1) for sy in(-1,1)]
for x,y in cp:
    part=part.union(cq.Workplane("XY").center(x,y).circle(POST_D/2).extrude(POST_H).translate((0,0,S)))
part=part.cut(cq.Workplane("XY").center((NX0+NX1)/2,(NY-TOP/2-1)/2).rect(NX1-NX0,-NY+TOP/2+1).extrude(ND+0.01).translate((0,0,S-ND)))
for x,y in cp:
    part=part.cut(cq.Workplane("XY").center(x,y).circle(PILOT/2).extrude(PILOT_D).translate((0,0,S+POST_H-PILOT_D)))
for x,y in [(sx*HORN_SQ/2,sy*HORN_SQ/2) for sx in(-1,1) for sy in(-1,1)]:
    part=part.cut(cq.Workplane("XY").center(x,y).circle(HORN_HOLE/2).extrude(S))
    part=part.cut(cq.Workplane("XY").center(x,y).circle(CB_D/2).extrude(S).translate((0,0,UNDER)))
part=part.cut(cq.Workplane("XY").circle(BORE/2).extrude(S))
cq.exporters.export(part,"stl/camera_plate_v3.stl")
print(f"deck z={S}, board underside z={S+POST_H}, total w/ board {S+POST_H+1.6}; clearance under board {POST_H}, at connector {POST_H+ND}; M2x6 into post {6-1.6}")
