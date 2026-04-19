# Flipping Cool v1 BOM Baseline

## Purpose

This document locks the first round of purchased and mechanical components for
`flipping-cool`.

These choices are the baseline for:

- CAD packaging
- power sizing
- ESC / BEC / receiver selection
- later PCB work

Treat these as "locked for packaging" rather than "never change". If a core
part changes later, revisit weight, packaging, and power before moving on.

## Design assumptions

- `1 lb / 454 g` robot
- four active flipper faces
- two weapon axes
- four corner drive pods
- `2S` battery
- simple and reliable `v1`

## Locked for packaging

### Drive motors

- Qty: `4`
- Part: `Pololu 75:1 Micro Metal Gearmotor HPCB 6V`
- Pololu item: `3064`
- Critical specs:
  - `10 x 12 x 25 mm` body
  - `9.5 g`
  - `3 mm` D-shaft
  - `430 rpm @ 6V`
  - `1.5 A` stall current
  - `1.1 kg-cm` stall torque
- Why this part:
  - compact antweight-proven form factor
  - favors control and pushing over top speed
  - carbon-brush version is preferred for combat duty

### Wheels

- Qty: `4`
- Part: `BBB 22 mm Antweight Wheels`
- Critical specs:
  - `22 mm` diameter
  - `10.7 mm` max width
  - about `3.5 g` each
- Why this part:
  - compact and grippy
  - antweight-proven size
  - works cleanly with the chosen motor shaft standard

### Weapon servos

- Qty: `2`
- Part: `Savox SH-0255MG+`
- Critical specs:
  - `22.8 x 12 x 29.4 mm`
  - `15.8 g`
  - `3.9 kg/cm @ 6V`
  - `0.13 s / 60 deg @ 6V`
  - `1.4 A` stall current
  - `21T` spline
- Why this part:
  - strong enough to drive paired flipper faces
  - still fits a compact center package
  - published current specs make later power design easier

### Battery

- Qty: `1`
- Part: `GNB 2S 450mAh HV 80C XT30`
- Model: `GNB4502S80AHV`
- Critical specs:
  - `14 x 17 x 61 mm`
  - `28 g`
  - `7.6 V` nominal
  - `XT30` discharge connector
- Why this part:
  - enough current headroom for `v1`
  - fits a compact central bay
  - stays inside the current battery weight target

## Locked mechanical standards

- Drive shaft standard: `3 mm` D-shaft
- Wheel standard: `22 mm` OD, about `11 mm` width
- Weapon cross-shaft standard: `3 mm` round stainless
- Flipper hinge pin standard: `2 mm` stainless
- Linkage hardware standard: `M2`, in double shear where possible
- Flipper face material target: `2.0 mm` polycarbonate if rules allow
- Battery bay target envelope: at least `65 x 20 x 18 mm`
- Servo pocket target envelope: at least `24 x 13 x 31 mm` each
- Weapon mechanism rule: hard stops and linkages carry impact loads, not servo
  gears

## Weight sanity check

- Drive motors: `38.0 g` total
- Wheels: about `14.0 g` total
- Weapon servos: `31.6 g` total
- Battery: about `28.0 g`
- Combined locked core mass: about `111.6 g` before hubs, shafts, fasteners,
  and wiring

This fits the intent of the current weight budget and leaves room for chassis,
flippers, electronics, and reserve.

## Electrical requirements created by these choices

- Drive current budget: plan for roughly `6 A` combined motor stall at the
  motor ratings, then add margin because the robot runs on `2S` and combat
  loads are sharp
- Weapon rail budget: two servos can demand about `2.8 A` combined stall at
  `6V`
- Battery connector standard: `XT30`
- The weapon servos must not rely on a tiny built-in ESC BEC
- Future power system should provide a clean `5V` to `6V` servo / radio rail
  with at least `4 A` real headroom

## Immediate next steps

1. Build a top-down packaging sketch or simple CAD layout around the locked
   motor, wheel, battery, and servo envelopes.
2. Freeze flipper geometry: hinge location, closed wedge angle, max open angle,
   horn radius, bellcrank ratio, and hard-stop positions.
3. Decide the power architecture from these loads: drive ESC class, external
   BEC, receiver, switch, capacitor, and whether `v1` uses a harness or a tiny
   power board.
4. Turn this into a tracked BOM with vendor, unit price, order status, and
   measured mass once real parts are in hand.
5. Only after packaging is stable, start the PCB around the chosen connector
   layout and power rails.

## Open items not locked yet

- Exact cross-shaft lengths and retention method
- Exact hub / adapter choice between motor shaft and wheels
- Exact flipper face profile and replaceable lip design
- Exact BEC, ESC, receiver, switch, and capacitor part numbers
- Exact screw lengths, inserts, and fastener counts

## Change control

If any of the four locked core parts change, re-check all three of these before
continuing:

- packaging
- current budget
- weight spreadsheet
