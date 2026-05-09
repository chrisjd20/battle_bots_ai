# Flipping Cool Rev A PCB Schematic

This KiCad 9 project is a schematic-first power and interconnect design for the `flipping-cool` robot. It intentionally uses off-board proven modules for drive, BEC, receiver, and servos.

## Rails

- `VBAT_RAW`: 2S LiHV battery positive before the removable link.
- `VBAT_SW`: switched battery positive after the mechanical disconnect.
- `SERVO_6V`: Pololu D36V50F6 external BEC output for weapon servos and spares.
- `RX_6V`: filtered branch of `SERVO_6V` for the ELRS receiver.
- `AUX_3V3`: optional future 3.3 V logic/sensor rail from the D24V5F3 module footprint.
- `GND_PWR`: common return for battery, ESC, BEC, receiver, and servos.

## Locked Off-Board Modules

- Battery: GNB4502S80AHV 2S LiHV XT30 pack.
- Drive motors: 4x Pololu 3064 75:1 Micro Metal Gearmotor HPCB 6V.
- Weapon servos: 2x Savox SH-0255MG+.
- Receiver: Matek ELRS-R24-P6 PWM receiver.
- Drive ESC: WEKA dual brushed ESC.
- BEC: Pololu D36V50F6 fixed 6 V, 5.5 A step-down module.

## Optional Growth Hardware

These are included in the Rev A schematic as future-ready hooks. They are not required
for the base robot to drive, flip, bind, or failsafe.

- `J44`: pit/debug power and comms header with `GND_PWR`, `VBAT_SW`,
  `SERVO_6V`, `RX_6V`, `CRSF_TX`, and `CRSF_RX`.
- `J45`: optional Pololu D24V5F3 3.3 V, 500 mA regulator module footprint.
  Pin order follows the Pololu edge pads: `SHDN`, `VIN`, `GND`, `VOUT`.
- `J46`/`J47`/`J48`: future MCU tap headers for 3.3 V power, CRSF,
  BEC power-good, I2C, PWM observation, analog rail sense, and RGB LED control.
- `J49`: 3.3 V I2C sensor connector using STEMMA QT/Qwiic order:
  `GND`, `AUX_3V3`, `I2C_SDA`, `I2C_SCL`.
- `J50`: common-anode RGB status LED header. `R50`/`R51`/`R52` provide
  330 ohm current limiting, and a future MCU sinks `STATUS_LED_*_N` low.
- `R40`-`R45`: 100 k / 47 k ADC dividers for `VBAT_SW`, `SERVO_6V`, and
  `RX_6V`. At an 8.7 V 2S LiHV maximum, `ADC_VBAT` is about 2.8 V.
- `R46`/`R47`: DNP 4.7 k I2C pull-ups to `AUX_3V3`; populate only if the
  installed I2C sensor stack does not already provide pull-ups.

## Schematic Acceptance Notes

- The removable link is represented as the only intentional connection between `VBAT_RAW` and `VBAT_SW`.
- The visible power LED assembly is fed from `VBAT_SW` through on-board `R1`, so it turns off when the link is removed and cannot be wired as a bare LED short.
- The receiver and weapon servos are powered from the external 6 V BEC path, not from the WEKA 5 V logic-only BEC.
- Four drive motors are connected as left pair and right pair fanouts from the two WEKA motor outputs.
- The visible power LED output is current-limited on board by `R1`, so a bare off-board LED cannot short directly across the battery rail.
- Spare switched VBAT is protected by `F1`, a 500 mA resettable PTC.
- `D1` adds a bidirectional TVS clamp across `VBAT_SW` and `GND_PWR` for motor/ESC transients.
- WEKA motor-output wiring enters through direct solder pads at `J22`, not a 0.1 inch pin header.
- Spare PWM, 6 V, VBAT, UART/CRSF, and test pads are included but documented as optional/unpopulated unless needed.
- The future MCU taps are passive observation/control points only. The base PWM
  nets remain receiver-driven; a future MCU must keep PWM pins high impedance
  unless the harness is intentionally reworked for MCU control.
- The optional 3.3 V rail is sourced from switched battery (`VBAT_SW`), so
  removing the main link also removes sensor/MCU/status-LED power.

Detailed growth notes live in `../docs/electrical-growth.md`.

Run ERC from repo root:

```bash
kicad-cli sch erc bots/flipping-cool/pcb/flipping-cool.kicad_sch
```
