#!/usr/bin/env python3
"""Generate baseline packaging envelopes for the flipping-cool bot."""

from __future__ import annotations

from pathlib import Path

from build123d import (
    Align,
    Box,
    BuildPart,
    Cylinder,
    Locations,
    export_step,
    export_stl,
)


# Locked packaging assumptions from docs/BOM.md.
ROBOT_SIZE_MM = (95.0, 95.0, 28.0)  # X, Y, Z
BATTERY_SIZE_MM = (65.0, 20.0, 18.0)
SERVO_SIZE_MM = (24.0, 13.0, 31.0)
WHEEL_DIAMETER_MM = 22.0
WHEEL_WIDTH_MM = 11.0
WHEEL_POD_OFFSET_MM = 34.0


def _build_chassis_envelope():
    with BuildPart() as part:
        Box(*ROBOT_SIZE_MM, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return part.part


def _build_battery_envelope():
    with BuildPart() as part:
        Box(*BATTERY_SIZE_MM, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return part.part


def _build_servo_envelopes():
    with BuildPart() as part:
        with Locations((0, 18, 0), (0, -18, 0)):
            Box(*SERVO_SIZE_MM, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return part.part


def _build_wheel_envelopes():
    corner_locations = []
    for x_sign in (-1, 1):
        for y_sign in (-1, 1):
            corner_locations.append(
                (x_sign * WHEEL_POD_OFFSET_MM, y_sign * WHEEL_POD_OFFSET_MM, 11)
            )

    with BuildPart() as part:
        with Locations(*corner_locations):
            Cylinder(
                radius=WHEEL_DIAMETER_MM / 2,
                height=WHEEL_WIDTH_MM,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            )
    return part.part


def generate(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    chassis = _build_chassis_envelope()
    battery = _build_battery_envelope()
    servos = _build_servo_envelopes()
    wheels = _build_wheel_envelopes()

    outputs = [
        output_dir / "chassis_envelope.step",
        output_dir / "battery_envelope.step",
        output_dir / "servo_envelopes.step",
        output_dir / "wheel_envelopes.step",
        output_dir / "chassis_envelope.stl",
    ]

    export_step(chassis, outputs[0])
    export_step(battery, outputs[1])
    export_step(servos, outputs[2])
    export_step(wheels, outputs[3])
    export_stl(chassis, outputs[4])
    return outputs


def main() -> None:
    default_out = Path(__file__).resolve().parents[1] / "generated"
    generated = generate(default_out)
    print("Generated CAD envelopes:")
    for path in generated:
        print(f"- {path}")


if __name__ == "__main__":
    main()
