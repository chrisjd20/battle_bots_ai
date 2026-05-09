# Flipping Cool Rev B Electrical Integration

## What Changed From Rev A

Rev A was intentionally receiver-driven. Its growth headers were passive taps
for future telemetry and debug.

Rev B makes those growth ideas active board features:

- ESP32-S3 module is on the PCB.
- 6 V servo/radio regulation is on the PCB.
- 3.3 V MCU/sensor regulation is on the PCB.
- PWM authority is selected by hardware using `SAFE / RX_DIRECT / MCU_CONTROL`.
- CRSF, I2C, ADC sensing, status LEDs, boot/reset, and debug headers are placed
  instead of being future-only placeholders.

## Power Tree

`VBAT_RAW` enters from the 2S XT30 battery connector and reaches `VBAT_SW` only
through the removable positive link. `VBAT_SW` feeds:

- WEKA ESC power connector.
- `U20` 6 V buck stage for `SERVO_6V`.
- fused input to `U30` 3.3 V buck stage for `AUX_3V3`.
- TVS clamp, bulk capacitance, power LED, and test points.

`SERVO_6V` powers receiver and servo outputs. `RX_6V` is the filtered receiver
branch. `AUX_3V3` powers MCU, muxes, sensors, status, and debug logic.

## Control Authority

Rev B does not let firmware silently take over the robot. The physical mode
switch is the contract:

| Switch | Required behavior |
| --- | --- |
| `SAFE` | Outputs inactive/safe. Used for bench setup and pit handling. |
| `RX_DIRECT` | Matek receiver PWM drives the ESC and weapon outputs without MCU dependency. |
| `MCU_CONTROL` | ESP32-S3 path may command outputs; BLE alternate control is allowed only here. |

The default safety policy is receiver-priority. If the MCU is unpowered or has
failed, `RX_DIRECT` must still be drivable once the receiver and 6 V rail are
alive.

## Integrated Interfaces

- `J10`: Matek ELRS-R24-P6 PWM receiver header.
- `J11`: optional CRSF UART between receiver and MCU.
- `J20`: WEKA switched battery input.
- `J21`: WEKA PWM harness; WEKA 5 V BEC remains monitor/no-connect.
- `J23`-`J26`: motor harness solder pads for off-board motors.
- `J30`/`J31`: weapon servo PWM outputs.
- `J32`/`J33`: spare 6 V PWM outputs.
- `J44`: pit/debug rail and comms header.
- `J46`-`J48`: MCU power/comms, signal, ADC, and status debug headers.
- `J49`: I2C sensor connector.

## Validation Gate

Rev B is not allowed to be ordered until:

- KiCad ERC is zero-error for the Rev B schematic representation.
- KiCad PCB DRC is zero-error and required nets have zero unconnected items.
- `SAFE`, `RX_DIRECT`, and `MCU_CONTROL` are bench-tested with the MCU powered
  and unpowered.
- 6 V and 3.3 V rails are load-tested for regulation, startup, shutdown,
  brownout observability, and thermal sanity.
- BLE alternate control is confirmed to be ignored unless `MCU_CONTROL` is
  physically selected.

Current status: the Rev B generated PCB/fab package exists, but DRC is failing
and must be cleaned before fabrication.
