#!/usr/bin/env python3
"""
Rev A Parametric Packaging Layout for flipping-cool.
Uses build123d to place actual components geometrically to verify fits and conflicts.
"""

from pathlib import Path
from build123d import (
    Align, Axis, Box, BuildPart, Cylinder, Location, Locations,
    export_step, export_stl, Rot, Compound, Sketch, Rectangle,
    sweep, extrude, chamfer, faces
)

# --- LOCKED PART DIMENSIONS (from BOM) ---
# Battery: 61 x 17 x 14 mm (lying flat)
BATTERY_L, BATTERY_W, BATTERY_H = 61.0, 17.0, 14.0

# Servo (Savox SH-0255MG+): 29.4 x 22.8 x 12.0 mm (lying flat)
SERVO_L, SERVO_W, SERVO_H = 29.4, 22.8, 12.0

# Motor (Pololu 75:1 N20 HPCB): 25 x 12 x 10 mm + 9mm shaft
MOTOR_L, MOTOR_W, MOTOR_H = 25.0, 12.0, 10.0
MOTOR_SHAFT_L, MOTOR_SHAFT_D = 9.0, 3.0

# Wheel (BBB 22mm): 22mm OD x 11mm wide
WHEEL_D, WHEEL_W = 22.0, 11.0

# Cross-shafts: 3mm round
SHAFT_D = 3.0

# --- ROBOT TARGET PARAMETERS ---
ROBOT_L = 95.0
ROBOT_W = 95.0
ROBOT_H = 28.0

# How much to clip the corners (chamfered-square design)
CORNER_CHAMFER = 20.0

# Wheelbase and track width (distance between wheels)
TRACK_WIDTH = 75.0
WHEELBASE = 55.0

def make_chassis_envelope() -> Compound:
    """A chamfered square bounding box for the robot."""
    with BuildPart() as bp:
        Box(ROBOT_L, ROBOT_W, ROBOT_H)
        # Chamfer the four vertical edges
        chamfer(bp.edges().filter_by(Axis.Z), length=CORNER_CHAMFER)
    # Center the chassis on origin but keep bottom at Z=0
    return bp.part.move(Location((0, 0, ROBOT_H/2)))

def make_battery() -> Compound:
    """Battery block."""
    with BuildPart() as bp:
        Box(BATTERY_L, BATTERY_W, BATTERY_H)
    return bp.part

def make_servo() -> Compound:
    """Weapon servo block."""
    with BuildPart() as bp:
        Box(SERVO_L, SERVO_W, SERVO_H)
        # Adding a simple cylinder to represent the spline/horn center
        with Locations((SERVO_L/2 - 6, 0, SERVO_H/2)):
            Cylinder(radius=2.5, height=3, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return bp.part

def make_motor_with_wheel() -> Compound:
    """Drive motor + wheel assembly."""
    with BuildPart() as bp:
        # Motor body
        Box(MOTOR_L, MOTOR_W, MOTOR_H, align=(Align.MAX, Align.CENTER, Align.CENTER))
        # Shaft
        with Locations((0, 0, 0)):
            Cylinder(radius=MOTOR_SHAFT_D/2, height=MOTOR_SHAFT_L, 
                     align=(Align.MIN, Align.CENTER, Align.CENTER))
        # Wheel (placed on the shaft)
        with Locations((MOTOR_SHAFT_L - WHEEL_W/2, 0, 0)):
            Cylinder(radius=WHEEL_D/2, height=WHEEL_W, 
                     align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return bp.part

def make_weapon_shaft(length: float) -> Compound:
    """Weapon cross-shaft."""
    with BuildPart() as bp:
        Cylinder(radius=SHAFT_D/2, height=length)
    return bp.part

def assemble_robot() -> list[Compound]:
    """Place all components into their geometric locations."""
    parts = []
    
    # 1. Chassis Envelope (rendered transparent in CAD or as a separate body)
    chassis = make_chassis_envelope()
    chassis.label = "Chassis_Envelope"
    parts.append(chassis)

    # 2. Battery
    # Center it, resting near the floor (Z = 2mm thickness of bottom plate)
    battery = make_battery().move(Location((0, 0, BATTERY_H/2 + 2)))
    battery.label = "Battery"
    parts.append(battery)

    # 3. Weapon Servos
    # Stack them or place them side by side?
    # At 12mm high each, stacking them takes 24mm. Total robot height is 28.
    # We can stack them right above the battery? No, battery is 14mm high. 14+12+12 = 38 > 28mm.
    # Therefore, they must sit beside the battery or flat on the floor next to it.
    # Battery is 17mm wide. Robot is 95mm wide. 95 - 17 = 78mm remaining.
    # Servos are 22.8mm wide. We can place one on the left and one on the right of the battery.
    servo_y_offset = BATTERY_W/2 + SERVO_W/2 + 2  # 2mm clearance
    
    # Servo 1 (e.g. driving Front/Rear flippers)
    servo1 = make_servo().move(Location((0, servo_y_offset, SERVO_H/2 + 2)))
    servo1.label = "Servo_FrontRear"
    parts.append(servo1)
    
    # Servo 2 (e.g. driving Left/Right flippers)
    servo2 = make_servo().move(Location((0, -servo_y_offset, SERVO_H/2 + 2)))
    # Rotate this one 90 degrees if it drives the other axis, or keep same orientation
    # Let's rotate 90 degrees around Z so it pushes left/right
    servo2 = servo2.move(Rot(Z=90))
    servo2.label = "Servo_LeftRight"
    parts.append(servo2)

    # 4. Drive Motors & Wheels
    # Tank drive: wheels pointing along X axis (Forward/Back)
    # 4 wheels, one in each corner
    motor_assembly = make_motor_with_wheel()
    motor_assembly = motor_assembly.move(Rot(Y=90)) # Point wheel outwards to the side? No, wheels roll forward.
    # If wheels roll forward (along X), their axis of rotation must be Y.
    # Our motor assembly has shaft along X. We need to rotate it so shaft is along Y.
    base_motor = make_motor_with_wheel().move(Rot(Z=90))
    
    # Left Front
    mf_l = make_motor_with_wheel().move(Rot(Z=90)).move(Location((WHEELBASE/2, TRACK_WIDTH/2, WHEEL_D/2)))
    mf_l.label = "Motor_FrontLeft"
    parts.append(mf_l)
    
    # Left Rear
    mr_l = make_motor_with_wheel().move(Rot(Z=90)).move(Location((-WHEELBASE/2, TRACK_WIDTH/2, WHEEL_D/2)))
    mr_l.label = "Motor_RearLeft"
    parts.append(mr_l)
    
    # Right Front (mirror the motor so wheel is on the outside)
    mf_r = make_motor_with_wheel().move(Rot(Z=-90)).move(Location((WHEELBASE/2, -TRACK_WIDTH/2, WHEEL_D/2)))
    mf_r.label = "Motor_FrontRight"
    parts.append(mf_r)
    
    # Right Rear
    mr_r = make_motor_with_wheel().move(Rot(Z=-90)).move(Location((-WHEELBASE/2, -TRACK_WIDTH/2, WHEEL_D/2)))
    mr_r.label = "Motor_RearRight"
    parts.append(mr_r)

    # 5. Weapon Cross-Shafts
    # One along X (for Left/Right flippers)
    shaft_x = make_weapon_shaft(ROBOT_L - 4).move(Rot(Y=90) * Location((0, 0, ROBOT_H - 4)))
    shaft_x.label = "CrossShaft_X"
    parts.append(shaft_x)
    
    # One along Y (for Front/Rear flippers)
    shaft_y = make_weapon_shaft(ROBOT_W - 4).move(Rot(X=90) * Location((0, 0, ROBOT_H - 8)))
    shaft_y.label = "CrossShaft_Y"
    parts.append(shaft_y)

    return parts

def generate(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    parts = assemble_robot()
    
    # Export individual parts to a single STEP assembly
    # Using Compound to bundle them
    assembly = Compound(children=parts)
    assembly_path = output_dir / "rev_a_assembly.step"
    export_step(assembly, assembly_path)
    
    # Export STL for visual check
    export_stl(assembly, output_dir / "rev_a_assembly.stl")
    return [assembly_path]

def main():
    out_dir = Path(__file__).resolve().parents[1] / "generated"
    generated = generate(out_dir)
    print("Rev A Layout Generated:")
    for p in generated:
        print(f" - {p}")

if __name__ == "__main__":
    main()
