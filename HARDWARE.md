# Hardware and bill of materials

What one Agent Vision build uses. Sizes come from the CAD sources in `cad/` and the design notes.
Anything marked **verify** hasn't been confirmed on a real build. Check it before you buy or print.

## Electronics

| Qty | Part | Notes |
|---|---|---|
| 1 | Hiwonder SO-ARM101 kit (follower arm) | Supplies the servos, board, PSU, bus cables and arm hardware below. |
| 5 | Hiwonder HX-30HM bus servo | IDs 1 base, 2 shoulder, 3 elbow, 4 wrist, 5 wrist roll. The kit's 6th (gripper) servo isn't used. |
| 1 | Hiwonder BusLinker V3.0 | USB to servo bus, 1,000,000 baud. Board 42 x 33 mm, holes 36 x 28 mm (vendor spec). |
| 1 | 12 V 5 A power supply (kit) | Check that the plug fits the BusLinker jack (**verify**: 5.5 x 2.5 vs 4.0 x 1.7). |
| 1 set | Servo bus cables (kit) | Daisy chain: BusLinker, then servos 1 to 5. Kit cables are 200 mm max; a longer lead to the base may be needed (**verify**). |
| 1 | USB hub | Connects the BusLinker and the camera to the computer. Model and whether it's powered: **verify**. |
| 1 | Arducam UC-A55 USB camera board | 95° H x 76° V FOV (vendor spec). The v3 plate fits a 38 x 38 board with holes on 28 x 28 (photo-measured, **verify** with calipers). |
| 1 | 4-pin 1.25 mm pitch (Molex PicoBlade) to USB cable for the camera | **May need buying separately.** Long enough to run from the wrist to the hub with slack at every joint (length **verify**). |
| 1 | USB cable, BusLinker to hub | |

## Printed parts (`cad/stl/`)

| Qty | File | Print orientation |
|---|---|---|
| 1 | `riser_A_foot_v2.stl` | Upright, foot on the bed. 220 x 140 x 158 mm (includes the 8 mm spigot). |
| 1 | `riser_B_top_v2.stl` | Upright, joint flange on the bed. 117 x 93 x 142 mm. Stack height 292 mm. |
| 1 | `arm_adapter_plate_v2_print-facedown.stl` | As exported: top face down. |
| 1 | `arm_adapter_clamp_v2_left_print-facedown.stl` | As exported: top face down. |
| 1 | `arm_adapter_clamp_v2_right_print-facedown.stl` | As exported: top face down. |
| 1 | `buslinker_mount.stl` | As exported (plate face on the bed). |
| 1 | `camera_plate_v3.stl` | As exported: horn boss on the bed, camera side up. |

All parts are designed to print without supports. The SO-101 arm parts themselves come from Hiwonder's print files (`White LeRobot.3mf` / `Black LeRobot.3mf`), which aren't redistributed here.

### Known print settings

- **Filament:** white PLA for every part (confirmed).
- **Adapter plate and both clamps** (from their slicer file): Bambu Lab X1 Carbon, 0.4 mm nozzle, 0.2 mm layers, 4 walls, 5 top / 3 bottom layers, 15% grid infill, nozzle 220 °C, bed 55 °C, textured PEI plate, no supports, no brim.
- **Riser, BusLinker mount and camera plate:** slicer settings not recorded (**verify**). The design notes plan for 4 walls and 20 to 25% infill.

## Fasteners by part

### Riser A to riser B joint
Tab and socket: riser A's 60 x 40 mm spigot drops into riser B's socket, then 4 bolts pull the flanges together.
M5 bolts, nuts and washers come from any hardware store.

| Qty | Part | Notes |
|---|---|---|
| 4 | M5 x 30 hex bolt | Down through B's 8 mm flange into captive nuts in A. In the CAD the nut sits 11 mm below A's joint face and the hole runs 12 mm deeper, so anything from 25 to 35 mm fits; 30 mm is the middle. |
| 4 | M5 hex nut | Slide into the side-slot nut traps in A. |
| 4 | M5 flat washer | Under the bolt heads. Recommended; the CAD doesn't model one. |

### Arm adapter plate to riser B (`arm_adapter_v2.py`)
| Qty | Part | Notes |
|---|---|---|
| 4 | M5 x 30 hex bolt | Through the plate's 14 mm holes into riser B's captive nuts. |
| 4 | M5 hex nut | In riser B's nut traps. |
| 4 | M8 x 24 mm fender washer | Bottom of each counterbore. Lets the bolt sit up to about 4 mm off-centre. |
| 4 | M5 x 15 mm fender washer | On top of the M8 fender, under the bolt head. |

### Arm base clamps (`arm_adapter_v2.py`)
No holes are drilled in the arm base. Two printed strap clamps grip the base's side wings.

| Qty | Part | Notes |
|---|---|---|
| 4 | M5 x 30 hex bolt | Two per clamp, through 8.5 x 13.5 mm slots. |
| 4 | M5 hex nut | Pressed into hex pockets (8.1 mm across flats) under the plate. |
| 4 | M5 x 15 mm fender washer | Under each clamp bolt head. |

All M5 bolts, nuts and washers (fender washers included) are standard parts from any hardware store.

### BusLinker mount (`buslinker_mount.py`)
| Qty | Part | Notes |
|---|---|---|
| 4 | M2.5 nylon F-F hex standoff, about 10 mm | Kit. 8 to 12 mm works. |
| 4 | M2.5 x 4 screw, rear (plate to standoff) | Heads sit in 1 mm counterbores. If yours are x6, delete the counterbore in the source. |
| 4 | M2.5 x 4 screw, front (board to standoff) | Use x5 at most with 8 mm standoffs. |
| 1 | M3 x 6 self-tapping screw | Jack screw in the centre boss. Tightening it pre-loads the clip on the riser column. Use x8 only with standoffs of 10 mm or more. |

Kit screw lengths are **verify**.

### Camera plate (`camera_plate_v3.py`)
| Qty | Part | Notes |
|---|---|---|
| 4 | M3 x 6 pan head (kit) | Through counterbores into the wrist-roll horn. Fit these before the camera. |
| 4 | M2 x 6 self-tapping (kit) | Camera board onto printed posts (1.7 mm pilots). |

### Bench mounting
| Qty | Part | Notes |
|---|---|---|
| 2 | G-clamp or C-clamp | Clamp riser A's foot to the bench edge (kit G-clamps or your own). Always clamp it. |

### Not used
- No heat-set inserts. The riser source comments mention inserts, but the v2 geometry uses captive M5 nuts.
- No bearings in the printed parts.
