# Flipping Cool Rev A Electrical Growth Hooks

## Purpose

The base robot still works as a simple, reliable receiver-driven battle bot:

- battery link arms `VBAT_SW`
- WEKA drives the four brushed motors
- the external 6 V BEC powers the receiver and weapon servos
- the Matek PWM receiver directly commands drive and weapon channels

This document covers the optional future hooks added to Rev A so we can add
debugging, telemetry, sensors, status indication, or a tiny controller later
without redesigning the whole electrical system.

These hooks are not required for first-drive or first-fight operation.

## Easy Wins Added

### Pit/debug header: `J44`

This is the quick checkup port. It gives a multimeter or logic analyzer access
to the rails and comms lines we are most likely to inspect in the pits.

Pinout:

1. `GND_PWR`
2. `VBAT_SW`
3. `SERVO_6V`
4. `RX_6V`
5. `CRSF_TX`
6. `CRSF_RX`

Use this for measuring and setup only. It is not a high-current battery,
servo, or accessory output.

### Optional 3.3 V rail: `J45` and `AUX_3V3`

Most useful future sensors and microcontrollers expect 3.3 V logic. Rev A now
has a footprint for a Pololu D24V5F3 3.3 V, 500 mA step-down module.

The Pololu D24V5F3 accepts the 2S LiHV switched pack rail comfortably: its
input range is 3.4 V to 36 V for this 3.3 V version, and its output is fixed at
3.3 V. It is enabled by default through the module's SHDN pull-up, so `SHDN`
can be left alone unless future firmware needs to turn sensors off.

`J45` pinout:

1. `AUX_3V3_SHDN`
2. `VBAT_SW`
3. `GND_PWR`
4. `AUX_3V3`

Important: the D24V5F3 module does not include reverse-voltage protection, so
the board-side wiring and connector orientation need to stay unambiguous.

### Future MCU headers: `J46`, `J47`, `J48`

These headers are the parking spot for a future tiny controller. The intent is
not to make Rev A depend on code. The intent is to leave clean attachment
points for future features.

Potential future uses:

- self-righting or orientation-aware macros
- smoother servo pulse shaping
- receiver/servo/battery rail telemetry
- colored status indications
- I2C orientation sensor support
- CRSF telemetry experiments

`J46` power/comms pinout:

1. `GND_PWR`
2. `AUX_3V3`
3. `BEC_PG`
4. `AUX_3V3_SHDN`
5. `CRSF_TX`
6. `CRSF_RX`

`J47` signal tap pinout:

1. `I2C_SDA`
2. `I2C_SCL`
3. `PWM_DRIVE_LEFT`
4. `PWM_DRIVE_RIGHT`
5. `PWM_WEAPON_FR`
6. `PWM_WEAPON_LR`

The PWM pins are taps on receiver-driven nets. A future MCU should treat them
as inputs/high-impedance observation points unless the harness is deliberately
changed so the MCU becomes the signal source. This avoids two outputs fighting
on the same signal line.

`J48` sense/status pinout:

1. `ADC_VBAT`
2. `ADC_SERVO_6V`
3. `ADC_RX_6V`
4. `STATUS_LED_R_N`
5. `STATUS_LED_G_N`
6. `STATUS_LED_B_N`

### I2C sensor connector: `J49`

`J49` is for a future orientation sensor or similar low-current I2C module. It
uses the STEMMA QT/Qwiic-style 4-pin order:

1. `GND_PWR`
2. `AUX_3V3`
3. `I2C_SDA`
4. `I2C_SCL`

Many STEMMA/Qwiic sensor boards already include I2C pull-ups, so `R46` and
`R47` are marked DNP. Populate those 4.7 k pull-ups only if the actual sensor
stack needs board-side pull-ups.

### RGB status LED: `J50`, `R50`, `R51`, `R52`

`J50` supports one off-board common-anode RGB LED. The LED common anode is tied
to `AUX_3V3`; each color cathode returns through a 330 ohm resistor to a future
MCU sink pin.

Pinout:

1. `AUX_3V3`
2. red cathode via `R50`
3. green cathode via `R51`
4. blue cathode via `R52`

Firmware behavior is simple: drive `STATUS_LED_*_N` low to turn that color on,
and leave it high/high-impedance to turn that color off. With 330 ohm resistors
from a 3.3 V rail, channel current stays in the small indicator-LED range
rather than becoming a power load.

Suggested future color meanings:

- green: receiver linked and armed
- blue: sensor/MCU alive
- amber/red: low battery or rail brownout warning
- purple: failsafe or setup mode

## Analog Sense Dividers

`R40` through `R45` create high-impedance voltage dividers for future MCU ADC
inputs:

- `VBAT_SW` -> `R40` 100 k -> `ADC_VBAT` -> `R41` 47 k -> `GND_PWR`
- `SERVO_6V` -> `R42` 100 k -> `ADC_SERVO_6V` -> `R43` 47 k -> `GND_PWR`
- `RX_6V` -> `R44` 100 k -> `ADC_RX_6V` -> `R45` 47 k -> `GND_PWR`

This ratio keeps the measured voltages under a 3.3 V ADC range:

- 8.7 V full 2S LiHV pack reads about 2.8 V at `ADC_VBAT`
- 6.0 V servo/receiver rail reads about 1.9 V at the ADC pin

The divider current is tiny, but the readings are high impedance. Future
firmware should sample slowly or add filtering if noisy rail readings matter.

## What This Still Does Not Do

Rev A still does not require a microcontroller. It also does not yet create a
true MCU-in-the-middle PWM architecture. If we later want the MCU to modify
receiver commands before they reach the ESC or servos, Rev B should add
intentional input/output routing or solder jumpers so signal ownership is
unambiguous.

## Source Specs Used

- Pololu D24V5F3: https://www.pololu.com/product/2842
- Pololu D24V5Fx dimension/pin callout PDF: https://www.pololu.com/file/0J1498/d24v5fx-step-down-voltage-regulator-dimensions.pdf
- STEMMA QT technical pin order: https://learn.adafruit.com/introducing-adafruit-stemma-qt/technical-specs
