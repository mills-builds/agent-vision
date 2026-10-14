# Agent Vision

An AI-controlled camera arm built on the open SO-101.

Agent Vision is a five-servo SO-101 arm with the gripper swapped for a small camera plate, mounted on a printed riser at the back of a workbench. An AI assistant drives it from a computer over USB, so it can move the camera above a spot on the bench and then aim it precisely.

This is my first public repo, and I'm new to robotics, so the docs are written for beginners.

**Goal of this repo: tools, not numbers.** Every bench, riser and cable run is different, so you discover your own joint limits and teach your own camera presets. Nothing here ships one person's positions for you to reuse.

## What's in here

| Path | What it is |
|---|---|
| `agent_vision/` | Python package: `hx_bus` servo driver plus the `av_*` command line tools. |
| `tests/` | Unit tests for packet building/parsing, checksums and clamping (no hardware needed). |
| `examples/` | Placeholder `limits`, `poses` and `av_config` files showing the file format only. |
| `cad/riser_A_foot.stl` | Bottom riser section (150 mm, print upright as is). Clamps to the bench edge. |
| `cad/riser_B_top.stl` | Top riser section (150 mm). Modelled upside down for printing; flip it so the spigot points down into the foot. Stacked height is 292 mm. |
| `cad/camera_plate.stl` | 42 x 42 mm plate that bolts to the wrist-roll servo horn in place of the gripper. Holds a UC-A55 camera board on M2 standoffs (28 x 28 mm pattern). |
| `cad/arm_adapter_v2.py` | CadQuery source for the SO-101 base to riser adapter (strap clamps, no drilling). Needs a base outline traced from Hiwonder's base part, which is not included. |
| `cad/buslinker_mount.py` | CadQuery source for the clip-on BusLinker V3 mount for the riser column. |
| `models/so101-camera-arm.glb` | The assembled arm, riser and camera plate as one 3D model. |
| `docs/index.html` | "How Agent Vision works", an interactive 3D explainer (also served on GitHub Pages). |
| `docs/buslinker.html` | How the BusLinker board connects the computer, the 12 V supply and a chain of bus servos. |

## Parts list

- Hiwonder SO-ARM101 kit (follower arm): 5 HX bus servos used, BusLinker V3.0 board, 12 V supply, bus cables and kit hardware. The gripper servo and jaws are not used.
- UC-A55 / Arducam USB camera board for the wrist.
- **4-pin camera-to-USB cable.** The camera board may ship without one that reaches from the wrist to your computer; you may need to buy it separately. Leave slack through every joint.
- USB cable from the BusLinker to your computer.
- Printed parts: riser foot, riser top, camera plate, arm adapter, BusLinker mount. These use only SO-101 kit hardware, plus the bench fasteners for the riser (M5 bolts and washers into the riser's captive nuts, and a clamp to the bench edge).

## Assembly

1. Get the Hiwonder SO-ARM101 kit and print its follower-arm parts (skip the gripper jaws).
2. Give each servo its own ID, one servo on the BusLinker at a time: 1 base, 2 shoulder, 3 elbow, 4 wrist, 5 wrist roll.
3. Assemble the arm from the base up. Toothed "main" horns clamp onto the splined servo shafts with the center screw; smooth "assistant" horns go on the back pivots.
4. Print the two riser sections and the camera plate, stack the riser, fit the arm adapter and bolt it into the riser top, then clamp the foot to the bench. Always clamp it; weight alone won't stop a swinging arm from tipping.

![SO-101 adapter on the riser](docs/so101_adapter_riser_assembly.png)

5. Clip the BusLinker mount onto the riser column and fit the board.

![BusLinker mount on the riser](docs/buslinker_mount_assembly.png)

6. Fit the camera plate to the wrist-roll horn and the camera board to the plate.

## Wiring

```
computer --USB-- BusLinker V3 --bus--> 1 base --> 2 shoulder --> 3 elbow --> 4 wrist --> 5 roll
                     ^
                   12 V
computer --USB (4-pin cable)-- wrist camera
```

Daisy-chain the bus cables from the BusLinker to the base, then each servo up to the wrist roll, leaving slack at each joint. The servos talk at 1,000,000 baud. See `docs/buslinker.html` for a picture of the board.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
# macOS camera snaps need ffmpeg: brew install ffmpeg   (Linux: apt install ffmpeg)
```

Find your serial port (macOS: `ls /dev/cu.usb*`, Linux: `ls /dev/ttyUSB* /dev/ttyACM*`) and tell the tools about it, in any of these ways (first one wins):

- `--port /dev/cu.usbmodemXXXX` on each command
- `export AV_PORT=/dev/cu.usbmodemXXXX`
- `cp examples/av_config.example.json av_config.json` and edit `port`

Check the bus:

```bash
av_read     # position (0-1000), temperature and voltage for joints 1-5
```

## Discover your ranges

Your safe range depends on your riser, bench, cable runs and what is nearby. Capture it once, by hand:

1. Clear the space around the arm. Support the arm with one hand.
2. Run `av_capture_range` (add `--margin 40` for a bigger safety margin; the default is 25). Torque goes off.
3. Slowly move **each** joint to both ends of its travel. Stop at resistance, a cable tug, or anything the arm or camera could touch.
4. Press Ctrl-C. The tool trims the margin off each end and writes `limits.json`.
5. Leave the arm resting folded; torque is still off.

`av_goto` refuses to move without `limits.json` and clamps every target to it. Re-run the capture whenever you change the mount, cables or surroundings.

## Teaching presets

```bash
av_teach overhead --snap     # torque off, place the arm, press Enter, it locks and saves
av_relax                     # torque off again (support the arm first)
av_goto overhead             # slow move back to the saved pose
av_snap                      # grab a frame into frames/
```

`av_teach` reads all five positions, re-locks the joints in place, optionally saves a camera frame to `frames/NAME.jpg`, and stores the pose in `poses.json`. A suggested starter set:

| Name | What it's for |
|---|---|
| `home` | Folded rest pose; the safest place to relax torque. |
| `overhead` | Camera straight down over the middle of the work area. |
| `front45` | Looking at the work area from the front at about 45 degrees. |
| `side_low` | Low side view for checking heights and edges. |
| `detail` | Close-up on a small spot. |
| `face_user` | Camera facing you, for a call or a quick check-in. |

`av_goto` options: `--max-temp 55` (abort and hold if any servo goes hotter, in C), `--step 20` and `--step-ms 100` (smaller step or longer time = slower).

## Safety

- **Support the arm before torque off.** `av_relax`, `av_capture_range` and `av_teach` make the arm go limp; it will drop under its own weight.
- **Gravity sag.** With torque on, the shoulder and elbow sag a little under load, more at full reach. Leave clearance, and don't teach poses that touch anything.
- **Stay in your limits.** Only move with `av_goto`, which clamps to `limits.json`. Re-capture limits after any change.
- Watch temperatures with `av_read`. Let hot servos cool and don't hold the arm stretched out for long.
- Keep hands, cables and faces clear when it moves, and keep the riser clamped.

## Known gaps (please check before you print)

- The riser's base bolt holes were matched against TheRobotStudio's base mesh, not Hiwonder's printed base. The base holes measure about 5.0 x 6.1 mm against the plate's 5.5 mm, so check your bolt size.
- The camera plate assumes a 6 mm servo horn, which leaves a 1.3 mm gap to the wrist bracket. Check your horn's real thickness or add a spacer.
- `cad/arm_adapter_v2.py` and `cad/buslinker_mount.py` are sources only; printable STLs aren't in the repo yet.

## Credits

This project stands on other people's open work. Thank you.

- **[TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100)** designed the SO-101 arm (Apache License 2.0). The 3D explainer uses their arm meshes and URDF joint data, converted and restyled. See [NOTICE](NOTICE) for exactly what was changed.
- **Hiwonder** makes the SO-ARM101 kit I built from: the HX-30HM bus servos, the BusLinker V3.0 board, and the print files for their servo pockets. Their print files are **not** copied here; get them from Hiwonder with the kit. <!-- TODO(mills-builds): add the Hiwonder product/download link -->
- **[LeRobot](https://github.com/huggingface/lerobot)** by Hugging Face is the open robot-learning project the SO-101 was designed for.
- **[Anatomy](https://github.com/wheresryan22/anatomy)** set the conventions for the explainer pages.
- **[ISO-GLOW](https://isoglow.dev)** by April Zhu (MIT) provides the 3D page shell, built on **[iso-figure](https://github.com/MrBongoC/ai-iso-skill)** by Tolga Cohce (MIT).
- **[three.js](https://threejs.org)** (MIT) renders the 3D view.

## License

Apache License 2.0, the same license as the SO-101. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
