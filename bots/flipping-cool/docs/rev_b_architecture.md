# Flipping Cool Rev B Architecture And Build Validation

## Board Class

Rev B is a 4-layer integrated control/power PCB targeting about
`120 x 100 mm`. It is assembly-service oriented rather than hand-assembly
first. The current generator is `../pcb/build_rev_b_pcb.py`.

## Off-Board Boundary

The PCB is not trying to embed the physical actuators or proven high-current
ESC module. These stay off-board:

- 2S LiHV battery pack.
- Four drive motors.
- Two weapon servos.
- External WEKA dual brushed ESC.
- External Matek ELRS-R24-P6 receiver.

## Power Tree

| Net | Source | Loads |
| --- | --- | --- |
| `VBAT_RAW` | Battery `J1` before link | Removable positive link only |
| `VBAT_SW` | Link output `J2` | WEKA power, regulators, TVS, LED, ADC divider |
| `SERVO_6V` | `U20` 6 V buck, 5.5 A minimum target | Receiver branch and servo outputs |
| `RX_6V` | Filtered `SERVO_6V` branch | Matek receiver and CRSF header power |
| `AUX_3V3` | `U30` dedicated buck | ESP32-S3, muxes, status, I2C, ADC network |
| `GND_PWR` | Common board return | Battery, ESC, regulators, receiver, MCU, servos |

Protection and observability:

- Removable link is the only intended `VBAT_RAW` to `VBAT_SW` bridge.
- `D1` clamps `VBAT_SW` transients to `GND_PWR`.
- `F1` protects auxiliary 3.3 V buck input branch.
- `TP1`-`TP6` expose primary rails.
- `R40`-`R45` sense `VBAT_SW`, `SERVO_6V`, and `RX_6V`.

## Control Authority Model

The mode switch is mandatory and user-visible:

| State | Hardware authority | MCU requirement | Intended use |
| --- | --- | --- | --- |
| `SAFE` | Outputs safe/inactive | None | Bench, pits, setup |
| `RX_DIRECT` | Receiver PWM direct path | MCU may be absent | Match fallback and first-drive validation |
| `MCU_CONTROL` | ESP32-S3 PWM path | MCU powered and healthy | BLE alternate control, telemetry-aware behavior |

Receiver-priority rule: Rev B must remain controllable in `RX_DIRECT` even
with the MCU unpowered or failed.

## Interface Pin Maps

### `J10` Matek Receiver PWM

| Pin | Net |
| ---: | --- |
| 1 | `GND_PWR` |
| 2 | `RX_6V` |
| 3 | `RX_PWM_DRIVE_LEFT` |
| 4 | `RX_PWM_DRIVE_RIGHT` |
| 5 | `RX_PWM_WEAPON_FR` |
| 6 | `RX_PWM_WEAPON_LR` |
| 7 | `PWM_RX_SPARE1` |
| 8 | `PWM_RX_SPARE2` |

### `J11` CRSF UART

| Pin | Net |
| ---: | --- |
| 1 | `GND_PWR` |
| 2 | `RX_6V` |
| 3 | `CRSF_RX_FROM_RX` |
| 4 | `CRSF_TX_TO_RX` |

### `J21` WEKA PWM

| Pin | Net |
| ---: | --- |
| 1 | `GND_PWR` |
| 2 | `WEKA_5V_BEC_NC_MON` |
| 3 | `PWM_DRIVE_LEFT` |
| 4 | `PWM_DRIVE_RIGHT` |

### Servo Outputs

`J30` and `J31` are weapon outputs; `J32` and `J33` are spare 6 V PWM outputs.

| Pin | Net |
| ---: | --- |
| 1 | `GND_PWR` |
| 2 | `SERVO_6V` |
| 3 | channel PWM |

## Bench Acceptance Checklist

- Verify no battery continuity from `VBAT_RAW` to `VBAT_SW` with link removed.
- Verify `VBAT_SW` appears only after link insertion.
- Load-test `SERVO_6V` across the expected servo/radio envelope, including
  sustained current and transient servo-load pulses.
- Load-test `AUX_3V3` with MCU, status, I2C, and mux loads.
- Confirm startup/shutdown does not inject unsafe pulses into WEKA or servo
  outputs.
- Confirm `SAFE` output inactivity.
- Confirm `RX_DIRECT` drives ESC and weapon outputs with MCU unpowered.
- Confirm `MCU_CONTROL` gives the ESP32-S3 authority only when physically
  selected.
- Confirm BLE command path is ignored outside `MCU_CONTROL`.
- Confirm CRSF pins are reachable by the MCU without breaking PWM mode.
- Confirm rail ADC readings track measured bench voltages.

## Current CAD Validation

The current Rev B board generator creates footprints, placement, routes,
Gerbers, drill, position CSV, STEP, renders, and DRC report. It is **not
print-ready** yet because KiCad PCB DRC is still failing. The next PCB task is
interactive routing cleanup or a stronger router pass until the DRC report has
zero errors and zero required unconnected items.
