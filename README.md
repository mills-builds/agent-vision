# Agent Vision

An AI-controlled camera arm built on the open SO-101.

Agent Vision is a five-servo SO-101 arm with the gripper swapped for a small camera plate, mounted on a printed riser at the back of a workbench. An AI assistant drives it from a computer over USB, so it can move the camera above a spot on the bench and then aim it precisely.

This is my first public repo, and I'm new to robotics, so the docs are written for beginners.

## Credits

This project stands on other people's open work. Thank you.

- **[TheRobotStudio](https://github.com/TheRobotStudio/SO-ARM100)** designed the SO-101 arm (Apache License 2.0). The 3D explainer uses their arm meshes and URDF joint data, converted and restyled. See [NOTICE](NOTICE) for exactly what was changed.
- **Hiwonder** makes the SO-ARM101 kit I built from: the HX-30HM bus servos, the BusLinker V3.0 board, and the print files for their servo pockets. Their print files are **not** copied here; get them from Hiwonder with the kit. <!-- TODO(Josh): add the Hiwonder product/download link -->
- **[Anatomy](https://github.com/wheresryan22/anatomy)** set the conventions for the explainer pages.
- **[ISO-GLOW](https://isoglow.dev)** by April Zhu (MIT) provides the 3D page shell, built on **[iso-figure](https://github.com/MrBongoC/ai-iso-skill)** by Tolga Cohce (MIT).
- **[three.js](https://threejs.org)** (MIT) renders the 3D view.

## What's in here

| Path | What it is |
|---|---|
| `cad/riser_A_foot.stl` | Bottom riser section (150 mm, print upright as is). Clamps to the bench edge. |
| `cad/riser_B_top.stl` | Top riser section (150 mm). Modelled upside down for printing; flip it so the spigot points down into the foot. Stacked height is 292 mm. |
| `cad/camera_plate.stl` | 42 x 42 mm plate that bolts to the wrist-roll servo horn in place of the gripper. Holds a UC-A55 camera board on M2 standoffs (28 x 28 mm pattern). |
| `models/so101-camera-arm.glb` | The assembled arm, riser and camera plate as one 3D model. |
| `docs/index.html` | "How Agent Vision works", an interactive 3D explainer (also served on GitHub Pages). |
| `docs/buslinker.html` | How the BusLinker board connects the computer, the 12 V supply and a chain of bus servos. |

## Build overview

1. Get the Hiwonder SO-ARM101 kit and print its follower-arm parts (skip the gripper jaws).
2. Give each servo its own ID, one servo on the BusLinker at a time: 1 base, 2 shoulder, 3 elbow, 4 wrist tilt, 5 wrist spin.
3. Assemble the arm from the base up. Toothed "main" horns clamp onto the splined servo shafts with the center screw; smooth "assistant" horns go on the back pivots.
4. Daisy-chain the bus cables: BusLinker, then servo 1, 2, 3, 4, 5, leaving slack at each joint.
5. Print the two riser sections and the camera plate, stack the riser, bolt the arm base to the top plate, and clamp the foot to the bench. Always clamp it; weight alone won't stop a swinging arm from tipping.

## Known gaps (please check before you print)

- The riser's base bolt holes were matched against TheRobotStudio's base mesh, not Hiwonder's printed base. The base holes measure about 5.0 x 6.1 mm against the plate's 5.5 mm, so check your bolt size.
- The camera plate assumes a 6 mm servo horn, which leaves a 1.3 mm gap to the wrist bracket. Check your horn's real thickness or add a spacer.
- Servo setup and control scripts are coming next.

## License

Apache License 2.0, the same license as the SO-101. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
