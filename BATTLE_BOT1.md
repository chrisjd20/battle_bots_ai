# BATTLE_BOT1

This is the `1 lb / 454 g` optimized version of the concept.

The earlier direction had the right idea, but it was not fully weight-optimized yet. At this class, the winning bot is not a tiny high-throw launcher. It is a **low, compact, durable four-way control flipper** that can attack from any side, self-right instantly, and keep working after repeated hits.

This plan assumes a normal plastic-ant interpretation: plastic structure and armor, with normal motors, electronics, shafts, and fasteners still allowed. If your event is stricter, re-check materials before locking anything in.

## 1 lb Verdict

The original concept was close, but not truly optimized for `454 g` because it still spent too much complexity on independence and not enough on packaging.

The biggest changes for a serious `1 lb` version are:

- stop thinking in terms of a huge flip
- optimize for **ground game, control, and recovery**
- pair opposite weapon faces into **2 weapon axes**
- build around a strict weight budget from day one
- keep electronics simple and proven for `v1`

## The Best 1 lb Version

If I were optimizing this concept specifically for `1 lb`, I would build a **chamfered-square tumbleweed control flipper**:

- four active flipper faces
- four short corner drive pods
- four-wheel drive
- two central weapon servos
- each servo drives one pair of opposite flippers

So you still keep the four-sided identity, but you stop paying the full weight and power penalty of four independent weapon channels.

That is the biggest improvement.

## Why 2 Weapon Axes Beats 4 Independent Flippers

At `1 lb`, full independence sounds cooler than it is useful.

Two paired axes is better because it:

- saves weight over four weapon servos
- reduces BEC load and brownout risk
- keeps the center of the robot available for battery and wiring
- simplifies driving under match stress
- still lets the bot attack and self-right from any orientation

Control layout should be:

- standard tank drive
- one momentary input for `front + rear`
- one momentary input for `left + right`

That is much more realistic in an actual fight than four separate weapon controls.

## Shape And Packaging

Do **not** build a true regular octagon.

Build a **square with clipped corners**:

- four long weapon faces
- four short corner pods for wheels and impact protection
- slightly crowned top and bottom so the robot rolls into a recoverable attitude instead of landing dead-flat

Target envelope:

- about `90 to 95 mm` square overall
- about `26 to 30 mm` tall
- as low as possible with the battery centered near the floor

The robot should look low and dense, not dramatic or tall.

## Weapon Geometry

Each active face should be a **low scoop-flipper**, not a vertical door.

The right motion is:

- closed position already forms a shallow wedge
- open position travels only far enough to lift, upset, and roll an opponent
- fast reset matters more than total throw

Think:

- **snap-lifter**
- **control flipper**
- **wheel-pop and turnover tool**

Not:

- catapult
- big theatrical launch

## Weapon Mechanism

The `1 lb` optimized mechanism is:

- `2x` stronger metal-gear weapon servos in the center
- `2x` lightweight cross-shafts, one per axis
- short mirrored bellcranks or pushrods to each pair of opposite flippers
- hard mechanical stops in both directions

Very important details:

- never drive the flipper plate directly from a servo horn
- keep the linkage short and protected
- set the closed position slightly **over-center**
- make impacts load the chassis stop, not the servo gears

At this scale, servo failures come from shock and back-driving more often than from lack of nominal torque.

## Drive System

For this concept, I would keep `4WD`.

Why:

- the corners are the cleanest place to put wheels
- you preserve all four long weapon faces
- the robot keeps traction no matter which side becomes the front

Recommended direction:

- `4x` small brushed gearmotors in the corner pods
- left pair electrically tied together
- right pair electrically tied together
- normal tank drive from the radio point of view

Good target behavior:

- quick acceleration
- moderate top speed
- strong pushing, not drag-race speed

If you must save weight, cut body mass before cutting drive traction.

## Electronics

Keep `v1` boring and reliable:

- `ELRS` receiver
- `dual brushed ESC` or equivalent two-channel brushed drive setup
- `2S LiPo/LiHV`
- direct receiver control for the two weapon axes

Do **not** start with:

- a custom PCB
- a microcontroller dependency
- fancy automation that the robot needs in order to function

You can always add smart features later, like:

- self-right macro
- servo pulse shaping
- orientation-aware mixing

But the first robot should be able to win without any of that.

## Power Strategy

The biggest electrical threat is not drive current.

It is **weapon-servo brownout and reset behavior**.

Design around that from the start:

- use an external servo power rail or BEC that can actually feed the weapon servos
- do not rely on a weak ESC BEC for the whole robot
- keep receiver power clean
- add capacitance near the receiver/BEC rail

Plain-English rule:

**If four corners drive and two weapon axes move at the same time, the radio must stay alive.**

## Realistic Weight Budget

Build to this budget, not to vibes:

- chassis tub, top shell, bottom shell, corner pods: `115 g max`
- four flipper plates, hinge hardware, linkage arms: `46 g max`
- two weapon servos: `42 g max`
- four drive motors: `52 g max`
- wheels, tires, hubs: `28 g max`
- battery: `35 g max`
- drive ESC: `15 g max`
- receiver: `3 g max`
- external BEC, capacitor, small power board: `18 g max`
- wiring, connectors, switch: `20 g max`
- bolts, nuts, axles, retainers: `30 g max`
- reserve for tuning and surprises: `50 g`

Total target: `454 g`

That reserve is intentional. A `1 lb` bot with no reserve is not optimized. It is just unfinished.

## Material Strategy

If `PETG` is what you have, use it carefully rather than using it everywhere at the same thickness.

Best approach:

- printed chassis tub in `PETG` or tougher plastic if available
- printed shell designed with ribs, not just thick walls
- flipper faces in `polycarbonate` sheet if your rules allow it
- otherwise printed flippers with replaceable leading lips
- metal hinge pins and fasteners if the rules permit them

Make these parts modular and replaceable:

- flipper faces
- corner guards
- skid/lip inserts
- linkage tabs

Those are consumables.

## Layout That Actually Fits

Top-down, the packaging should work like this:

- battery in the center and as low as possible
- receiver tucked above or beside the battery
- drive ESC close to the battery
- BEC and capacitor near receiver power entry
- two weapon servos centered on the two main axes
- cross-shafts running front/rear and left/right
- drive motors in the four corner pods

That keeps:

- mass centralized
- weapon linkages short
- the outer shell free to absorb impacts

## What To Avoid

Avoid these completely in the `1 lb` version:

- a true regular octagon
- `CO2` or any pneumatic system
- four fully independent weapon controls
- direct-driving a plate from the servo spline
- exposed servo arms
- tall flipper doors
- custom electronics as the first milestone
- powering weapon servos from a weak built-in BEC

Height is a trap on control bots. Stay low.

## Build Priorities

Build in this order:

1. driving chassis that makes weight
2. one weapon axis with hard stops
3. second weapon axis
4. replaceable lips and corner armor
5. radio mapping and self-right testing

Do not design the whole robot around version-2 electronics before the version-1 chassis survives impacts.

## Final 1 lb Spec

If I were locking the design today, I would commit to this:

- chamfered-square chassis
- four low scoop-flippers
- four corner drive wheels
- two central weapon servos
- opposite sides paired into two weapon axes
- no custom PCB in `v1`
- low-profile control-flipper tuning, not giant-launch tuning
- hard weight budget with at least `40 to 50 g` reserved until late in the build

That is the version most optimized for `1 lb`: simpler, lighter, easier to package, easier to drive, and more likely to survive real matches.