# Flipping Cool Rev B PCB

This KiCad project is now the active Rev B integration target for
`flipping-cool`. Rev A remains the historical receiver-driven baseline in the
older schematic sheets and docs; Rev B is the aggressive single-board control
and power architecture.

## Rev B Intent

Rev B integrates the electronics that make sense to put on the robot PCB:

- ESP32-S3-WROOM-1 module for firmware, BLE alternate control, telemetry, ADC
  rail sensing, status LEDs, I2C, and CRSF experiments.
- Board-generated `SERVO_6V` rail with a 5.5 A minimum target for receiver and
  weapon servo loads.
- Board-generated `AUX_3V3` rail for MCU, sensors, status, and debug logic.
- Hardware authority selection using the mandatory user-facing
  `SAFE / RX_DIRECT / MCU_CONTROL` switch.
- Receiver-priority PWM routing through hardware mux footprints so
  `RX_DIRECT` can bypass an unpowered or failed MCU.
- Matek receiver interface, optional CRSF UART, WEKA-native ESC power/PWM
  interface, motor/servo harness connectors, ADC dividers, debug headers, I2C,
  and status LEDs.

These remain off-board by design: motors, weapon servos, battery pack, WEKA
ESC, and Matek receiver.

## Active Artifacts

- `build_rev_b_pcb.py`: reproducible Rev B PCB/fab generator.
- `flipping-cool.kicad_pcb`: generated Rev B active board target, about
  `120 x 100 mm`, 4 copper layers.
- `fab_rev_b/`: generated Gerbers, drill, position CSV, STEP, renders, ZIP,
  and DRC report.
- `../docs/rev_b_architecture.md`: Rev B architecture and bench validation
  contract.

Run the generator from the repo root:

```bash
python3 bots/flipping-cool/pcb/build_rev_b_pcb.py
```

Run PCB DRC:

```bash
kicad-cli pcb drc bots/flipping-cool/pcb/flipping-cool.kicad_pcb \
  --output bots/flipping-cool/pcb/fab_rev_b/flipping-cool-rev-b-drc.rpt \
  --format report
```

## Current Validation Status

Rev B is **not yet print-ready**. The generated board/fab package exists, but
KiCad DRC is still failing in `fab_rev_b/flipping-cool-rev-b-drc.rpt`.

Current blocker class:

- Generated routing still needs hand/interactive cleanup around the ESP32-S3,
  switch/mux cluster, headers, and high-current rails.
- The schematic intent and board architecture are present, but PCB DRC must be
  driven to zero errors before ordering.

Acceptance remains:

- ERC: zero errors.
- PCB DRC: zero errors and zero required unconnected items.
- Rev B footprints present for MCU, regulators, mode switch, muxes, receiver,
  CRSF, WEKA interfaces, servo outputs, sensing, debug, I2C, and status.
- Fab ZIP regenerated only after DRC is clean.

Do not fabricate Rev B until DRC passes.
