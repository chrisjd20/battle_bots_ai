# Rev A Packaging Layout

This document summarizes the current packaging layout and dimensions based on the `cad/src/rev_a_layout.py` script.

## Frozen Dimensions (Rev A)
- **Robot Envelope**: 95.0 x 95.0 x 28.0 mm
- **Corner Chamfer**: 20.0 mm
- **Wheelbase**: 55.0 mm (distance between front and rear axles)
- **Track Width**: 75.0 mm (distance between left and right wheel centerlines)
- **Weapon Servo Positions**: Center-mounted beside the battery, offset by `~22mm` from center Y-axis. One faces front/rear flippers, one faces left/right flippers.
- **Weapon Cross-Shafts**: Lengths of `91.0 mm` on X and Y axes, clearing the chassis walls by 2mm per side. Height Z offset: 24mm (X-axis) and 20mm (Y-axis) to avoid crossing interference.

## Check Results
1. **Drive Pods**: The four Pololu N20 motors fit cleanly at the chamfered corners with standard 22mm wheels.
2. **Central Bay**: The GNB 450mAh 2S battery and two Savox servos physically fit inside the 95mm chassis without height violations.
3. **Weapon Linkages**: The cross-shafts are currently stacked at two different heights (Z=20mm and Z=24mm) so they do not intersect in the dead center. This forces the flipper bellcranks to have two different radii/geometries.

## Open Risks & Next Steps
- The weapon cross shafts cross in the center, so they must be stacked at different heights (currently Z=20 and Z=24). This requires designing two different linkage bellcranks.
- Need to finalize precise ESC and BEC placement in the remaining open space near the battery.
- Need to confirm mass of the 3D-printed chassis around these parts.

*See `cad/generated/rev_a_assembly.step` for the 3D export.*
