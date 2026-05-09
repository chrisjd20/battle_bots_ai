#!/usr/bin/env python3
"""Generate the Flipping Cool Rev B integrated control/power PCB.

The Rev B board intentionally replaces the old Rev A harness board as the
active PCB target.  Rev A remains documented in the project history; this
script is the reproducible source for the integrated Rev B layout.
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from pathlib import Path
import os
import shutil
import subprocess

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "flipping-cool.kicad_pcb"
FAB_DIR = ROOT / "fab_rev_b"
FP_ROOT = Path(os.environ.get("KICAD9_FOOTPRINT_DIR", "/usr/share/kicad/footprints"))

MM = pcbnew.FromMM
P = pcbnew.VECTOR2I_MM


@dataclass(frozen=True)
class LibFootprint:
    lib: str
    name: str

    @property
    def path(self) -> str:
        return str(FP_ROOT / f"{self.lib}.pretty")


FP = {
    "xt30": LibFootprint("Connector_AMASS", "AMASS_XT30UPB-F_1x02_P5.0mm_Vertical"),
    "pin1x02": LibFootprint("Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical"),
    "pin1x03": LibFootprint("Connector_PinHeader_2.54mm", "PinHeader_1x03_P2.54mm_Vertical"),
    "pin1x04": LibFootprint("Connector_PinHeader_2.54mm", "PinHeader_1x04_P2.54mm_Vertical"),
    "pin1x05": LibFootprint("Connector_PinHeader_2.54mm", "PinHeader_1x05_P2.54mm_Vertical"),
    "pin1x06": LibFootprint("Connector_PinHeader_2.54mm", "PinHeader_1x06_P2.54mm_Vertical"),
    "pin1x08": LibFootprint("Connector_PinHeader_2.54mm", "PinHeader_1x08_P2.54mm_Vertical"),
    "jst_sh4": LibFootprint("Connector_JST", "JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"),
    "esp32s3": LibFootprint("RF_Module", "ESP32-S3-WROOM-1"),
    "sp3t": LibFootprint("Button_Switch_SMD", "SW_SP3T_PCM13"),
    "button": LibFootprint("Button_Switch_SMD", "SW_SPST_TL3305B"),
    "sot23_6": LibFootprint("Package_TO_SOT_SMD", "SOT-23-6"),
    "r0805": LibFootprint("Resistor_SMD", "R_0805_2012Metric"),
    "c0805": LibFootprint("Capacitor_SMD", "C_0805_2012Metric"),
    "cp63": LibFootprint("Capacitor_SMD", "CP_Elec_6.3x7.7"),
    "fuse1812": LibFootprint("Fuse", "Fuse_1812_4532Metric"),
    "sma_diode": LibFootprint("Diode_SMD", "D_SMA"),
    "led0805": LibFootprint("LED_SMD", "LED_0805_2012Metric"),
    "tp": LibFootprint("TestPoint", "TestPoint_Pad_D1.5mm"),
    "mh": LibFootprint("MountingHole", "MountingHole_3.2mm_M3"),
    "wirepad": LibFootprint("Connector_Wire", "SolderWirePad_1x01_SMD_5x10mm"),
}


def fp_exists(fp: LibFootprint) -> None:
    mod = Path(fp.path) / f"{fp.name}.kicad_mod"
    if not mod.exists():
        raise FileNotFoundError(mod)


def net(board: pcbnew.BOARD, name: str, nets: dict[str, pcbnew.NETINFO_ITEM]) -> pcbnew.NETINFO_ITEM:
    if name not in nets:
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item)
        nets[name] = item
    return nets[name]


def add_footprint(
    board: pcbnew.BOARD,
    ref: str,
    value: str,
    fp_key: str,
    x: float,
    y: float,
    rot: float = 0,
    locked: bool = False,
) -> pcbnew.FOOTPRINT:
    footprint = FP[fp_key]
    fp_exists(footprint)
    item = pcbnew.FootprintLoad(footprint.path, footprint.name)
    if item is None:
        raise RuntimeError(f"Unable to load footprint {footprint.lib}:{footprint.name}")
    item.SetReference(ref)
    item.SetValue(value)
    item.SetPosition(P(x, y))
    item.SetOrientationDegrees(rot)
    item.SetLocked(locked)
    for text in item.GraphicalItems():
        if isinstance(text, pcbnew.PCB_TEXT):
            if text.GetText() == ref:
                text.SetTextSize(P(1.0, 1.0))
            elif text.GetText() == value:
                text.SetVisible(False)
    board.Add(item)
    return item


def assign_nets(
    board: pcbnew.BOARD,
    fp: pcbnew.FOOTPRINT,
    pad_nets: dict[str, str],
    nets: dict[str, pcbnew.NETINFO_ITEM],
) -> None:
    for pad_no, net_name in pad_nets.items():
        pad = fp.FindPadByNumber(pad_no)
        if not pad:
            raise ValueError(f"{fp.GetReference()} has no pad {pad_no}")
        pad.SetNet(net(board, net_name, nets))


def track(
    board: pcbnew.BOARD,
    net_item: pcbnew.NETINFO_ITEM,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    width_mm: float,
    layer: int,
) -> None:
    if start == end:
        return
    item = pcbnew.PCB_TRACK(board)
    item.SetStart(start)
    item.SetEnd(end)
    item.SetWidth(MM(width_mm))
    item.SetLayer(layer)
    item.SetNet(net_item)
    board.Add(item)


def via(
    board: pcbnew.BOARD,
    net_item: pcbnew.NETINFO_ITEM,
    x: float,
    y: float,
    width_mm: float = 0.60,
    drill_mm: float = 0.30,
) -> None:
    item = pcbnew.PCB_VIA(board)
    item.SetPosition(P(x, y))
    item.SetWidth(MM(width_mm))
    item.SetDrill(MM(drill_mm))
    item.SetNet(net_item)
    board.Add(item)


def shape_segment(board: pcbnew.BOARD, a: tuple[float, float], b: tuple[float, float], layer: int, width: float = 0.10) -> None:
    item = pcbnew.PCB_SHAPE(board)
    item.SetShape(pcbnew.SHAPE_T_SEGMENT)
    item.SetStart(P(*a))
    item.SetEnd(P(*b))
    item.SetLayer(layer)
    item.SetWidth(MM(width))
    board.Add(item)


def add_text(
    board: pcbnew.BOARD,
    text: str,
    x: float,
    y: float,
    size: float = 1.2,
    layer: int = pcbnew.F_SilkS,
    rot: float = 0,
    bold: bool = False,
) -> None:
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(P(x, y))
    item.SetTextSize(P(size, size))
    item.SetTextThickness(MM(0.15 if size < 1.5 else 0.2))
    item.SetLayer(layer)
    item.SetTextAngleDegrees(rot)
    item.SetBold(bold)
    board.Add(item)


def add_zone(
    board: pcbnew.BOARD,
    net_item: pcbnew.NETINFO_ITEM,
    layer: int,
    points: list[tuple[float, float]],
    clearance_mm: float = 0.30,
) -> None:
    zone = pcbnew.ZONE(board)
    zone.SetNet(net_item)
    zone.SetLayer(layer)
    zone.SetIsFilled(True)
    zone.SetFillFlag(layer, True)
    zone.SetLocalClearance(MM(clearance_mm))
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in points:
        outline.Append(P(x, y))
    board.Add(zone)


def pad_center_mm(pad: pcbnew.PAD) -> tuple[float, float]:
    c = pad.GetCenter()
    return pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)


def pads_by_net(board: pcbnew.BOARD) -> dict[str, list[pcbnew.PAD]]:
    result: dict[str, list[pcbnew.PAD]] = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            name = pad.GetNetname()
            if name:
                result.setdefault(name, []).append(pad)
    return result


def route_net_bus(
    board: pcbnew.BOARD,
    name: str,
    pads: list[pcbnew.PAD],
    trunk_y: float,
    width_mm: float,
    route_layer: int = pcbnew.In1_Cu,
    drop_layer: int = pcbnew.In2_Cu,
    via_size: float = 0.60,
    via_drill: float = 0.30,
) -> None:
    if len(pads) < 2:
        return
    net_item = pads[0].GetNet()
    xs = []
    via_points: set[tuple[int, int]] = set()
    for pad in pads:
        x, y = pad_center_mm(pad)
        xs.append(x)
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
            key = (round(x * 1000), round(y * 1000))
            if key not in via_points:
                via(board, net_item, x, y, via_size, via_drill)
                via_points.add(key)
        trunk_key = (round(x * 1000), round(trunk_y * 1000))
        if trunk_key not in via_points:
            via(board, net_item, x, trunk_y, via_size, via_drill)
            via_points.add(trunk_key)
        track(board, net_item, P(x, y), P(x, trunk_y), width_mm, drop_layer)
    track(board, net_item, P(min(xs), trunk_y), P(max(xs), trunk_y), width_mm, route_layer)


def manual_manhattan(
    board: pcbnew.BOARD,
    net_item: pcbnew.NETINFO_ITEM,
    points: list[tuple[float, float]],
    width_mm: float,
    layer: int,
) -> None:
    for a, b in zip(points, points[1:]):
        track(board, net_item, P(*a), P(*b), width_mm, layer)


GRID_MM = 0.50
ROUTE_LAYERS = (pcbnew.In1_Cu, pcbnew.In2_Cu)
ROUTE_LAYER_NAMES = {pcbnew.In1_Cu: 0, pcbnew.In2_Cu: 1}


def grid_coord(v: float) -> int:
    return round(v / GRID_MM)


def world_coord(g: int) -> float:
    return g * GRID_MM


def mark_disc(blocked: set[tuple[int, int, int]], x: float, y: float, radius: float, layers: tuple[int, ...] = ROUTE_LAYERS) -> None:
    gx = grid_coord(x)
    gy = grid_coord(y)
    gr = max(1, math.ceil(radius / GRID_MM))
    for layer in layers:
        lid = ROUTE_LAYER_NAMES[layer]
        for ix in range(gx - gr, gx + gr + 1):
            for iy in range(gy - gr, gy + gr + 1):
                if (world_coord(ix) - x) ** 2 + (world_coord(iy) - y) ** 2 <= radius**2:
                    blocked.add((ix, iy, lid))


def mark_segment(blocked: set[tuple[int, int, int]], a: tuple[float, float], b: tuple[float, float], layer: int, radius: float) -> None:
    ax, ay = a
    bx, by = b
    dist = max(abs(bx - ax), abs(by - ay))
    steps = max(1, math.ceil(dist / (GRID_MM / 2)))
    for i in range(steps + 1):
        t = i / steps
        mark_disc(blocked, ax + (bx - ax) * t, ay + (by - ay) * t, radius, (layer,))


def base_route_obstacles(board: pcbnew.BOARD) -> dict[str, set[tuple[int, int, int]]]:
    """Return per-net internal-layer obstacles.

    SMD pads only exist on the outer layers, so the internal router may pass
    below them. PTH/NPTH pads and the ESP antenna keepout block all internal
    routing.
    """
    by_net: dict[str, set[tuple[int, int, int]]] = {}
    all_blocked: set[tuple[int, int, int]] = set()

    # Board boundary and ESP32 antenna keepout.
    for x in [i * GRID_MM for i in range(grid_coord(0), grid_coord(120) + 1)]:
        mark_disc(all_blocked, x, 0.0, 1.0)
        mark_disc(all_blocked, x, 100.0, 1.0)
    for y in [i * GRID_MM for i in range(grid_coord(0), grid_coord(100) + 1)]:
        mark_disc(all_blocked, 0.0, y, 1.0)
        mark_disc(all_blocked, 120.0, y, 1.0)
    for x in [i * GRID_MM for i in range(grid_coord(60), grid_coord(108) + 1)]:
        for y in [j * GRID_MM for j in range(grid_coord(4), grid_coord(25) + 1)]:
            mark_disc(all_blocked, x, y, 0.35)

    for fp in board.GetFootprints():
        for pad in fp.Pads():
            attr = pad.GetAttribute()
            if attr not in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                continue
            x, y = pad_center_mm(pad)
            radius = 1.25 if attr == pcbnew.PAD_ATTRIB_PTH else 2.2
            net_name = pad.GetNetname()
            for layer in ROUTE_LAYERS:
                lid = ROUTE_LAYER_NAMES[layer]
                gx = grid_coord(x)
                gy = grid_coord(y)
                gr = max(1, math.ceil(radius / GRID_MM))
                for ix in range(gx - gr, gx + gr + 1):
                    for iy in range(gy - gr, gy + gr + 1):
                        if (world_coord(ix) - x) ** 2 + (world_coord(iy) - y) ** 2 <= radius**2:
                            key = (ix, iy, lid)
                            all_blocked.add(key)
                            if net_name:
                                by_net.setdefault(net_name, set()).add(key)
    by_net["__all__"] = all_blocked
    return by_net


def astar_path(
    start: tuple[int, int, int],
    goals: set[tuple[int, int, int]],
    blocked: set[tuple[int, int, int]],
    max_x: int = grid_coord(119),
    max_y: int = grid_coord(99),
) -> list[tuple[int, int, int]] | None:
    def heuristic(node: tuple[int, int, int]) -> float:
        x, y, node_layer = node
        return min(abs(x - gx) + abs(y - gy) + (0 if node_layer == gl else 3) for gx, gy, gl in goals)

    queue: list[tuple[float, float, tuple[int, int, int]]] = []
    heapq.heappush(queue, (heuristic(start), 0.0, start))
    came_from: dict[tuple[int, int, int], tuple[int, int, int] | None] = {start: None}
    cost_so_far = {start: 0.0}

    while queue:
        _, cost, current = heapq.heappop(queue)
        if current in goals:
            path = [current]
            while came_from[path[-1]] is not None:
                path.append(came_from[path[-1]])
            path.reverse()
            return path
        x, y, layer = current
        candidates = [
            (x + 1, y, layer, 1.0),
            (x - 1, y, layer, 1.0),
            (x, y + 1, layer, 1.0),
            (x, y - 1, layer, 1.0),
            (x, y, 1 - layer, 6.0),
        ]
        for nx, ny, nl, step_cost in candidates:
            if nx < 2 or nx > max_x or ny < 2 or ny > max_y:
                continue
            nxt = (nx, ny, nl)
            if nxt in blocked and nxt not in goals:
                continue
            new_cost = cost_so_far[current] + step_cost
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                came_from[nxt] = current
                heapq.heappush(queue, (new_cost + heuristic(nxt), new_cost, nxt))
    return None


def emit_astar_route(
    board: pcbnew.BOARD,
    net_item: pcbnew.NETINFO_ITEM,
    path: list[tuple[int, int, int]],
    width_mm: float,
    via_size: float,
    via_drill: float,
    routed_obstacles: set[tuple[int, int, int]],
) -> None:
    if not path:
        return
    compressed: list[tuple[int, int, int]] = [path[0]]
    for point in path[1:]:
        if len(compressed) >= 2:
            a = compressed[-2]
            b = compressed[-1]
            same_dir = (a[2] == b[2] == point[2]) and (
                (a[0] == b[0] == point[0]) or (a[1] == b[1] == point[1])
            )
            if same_dir:
                compressed[-1] = point
                continue
        compressed.append(point)

    for a, b in zip(compressed, compressed[1:]):
        ax, ay, al = a
        bx, by, bl = b
        if al != bl:
            via(board, net_item, world_coord(ax), world_coord(ay), via_size, via_drill)
            mark_disc(routed_obstacles, world_coord(ax), world_coord(ay), via_size / 2 + 0.25)
        else:
            layer = ROUTE_LAYERS[al]
            start = (world_coord(ax), world_coord(ay))
            end = (world_coord(bx), world_coord(by))
            track(board, net_item, P(*start), P(*end), width_mm, layer)
            mark_segment(routed_obstacles, start, end, layer, width_mm / 2 + 0.30)


def route_board_with_astar(board: pcbnew.BOARD) -> list[str]:
    pad_map = pads_by_net(board)
    obstacles_by_net = base_route_obstacles(board)
    routed_obstacles_by_net: dict[str, set[tuple[int, int, int]]] = {}
    failures: list[str] = []

    net_order = [
        "VBAT_RAW",
        "VBAT_SW",
        "VBAT_SW_FUSED",
        "SERVO_6V",
        "RX_6V",
        "AUX_3V3",
    ] + sorted(n for n in pad_map if n not in {"GND_PWR", "VBAT_RAW", "VBAT_SW", "VBAT_SW_FUSED", "SERVO_6V", "RX_6V", "AUX_3V3"})

    for name in net_order:
        pads = pad_map.get(name, [])
        if len(pads) < 2:
            continue
        net_item = pads[0].GetNet()
        all_blocked = set(obstacles_by_net["__all__"])
        all_blocked.difference_update(obstacles_by_net.get(name, set()))
        for other_name, obs in routed_obstacles_by_net.items():
            if other_name != name:
                all_blocked.update(obs)
        width = 0.80 if name in {"VBAT_RAW", "VBAT_SW", "SERVO_6V"} else 0.24
        via_size = 0.75 if width >= 0.8 else 0.45
        via_drill = 0.35 if width >= 0.8 else 0.22
        routed_for_this_net: set[tuple[int, int, int]] = routed_obstacles_by_net.setdefault(name, set())
        source = pads[0]
        sx, sy = pad_center_mm(source)
        source_states = [(grid_coord(sx), grid_coord(sy), 0), (grid_coord(sx), grid_coord(sy), 1)]
        for pad in pads[1:]:
            dx, dy = pad_center_mm(pad)
            goals = {(grid_coord(dx), grid_coord(dy), 0), (grid_coord(dx), grid_coord(dy), 1)}
            path = None
            for start in source_states:
                candidate = astar_path(start, goals, all_blocked)
                if candidate and (path is None or len(candidate) < len(path)):
                    path = candidate
            if path is None:
                failures.append(f"{name}: {source.GetParentFootprint().GetReference()} to {pad.GetParentFootprint().GetReference()}")
                continue
            if source.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                via(board, net_item, sx, sy, via_size, via_drill)
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                via(board, net_item, dx, dy, via_size, via_drill)
            emit_astar_route(board, net_item, path, width, via_size, via_drill, routed_for_this_net)
        all_blocked.update(routed_for_this_net)
    return failures


def build_board() -> pcbnew.BOARD:
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    board.SetLayerName(pcbnew.In1_Cu, "In1.Cu")
    board.SetLayerName(pcbnew.In2_Cu, "In2.Cu")
    board.SetLayerType(pcbnew.F_Cu, pcbnew.LT_SIGNAL)
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.B_Cu, pcbnew.LT_SIGNAL)

    nets: dict[str, pcbnew.NETINFO_ITEM] = {}
    for name in [
        "GND_PWR",
        "VBAT_RAW",
        "VBAT_SW",
        "SERVO_6V",
        "RX_6V",
        "AUX_3V3",
        "MODE_SAFE",
        "MODE_RX_DIRECT",
        "MODE_MCU_CONTROL",
    ]:
        net(board, name, nets)

    outline = [(8, 0), (112, 0), (120, 8), (120, 92), (112, 100), (8, 100), (0, 92), (0, 8), (8, 0)]
    for a, b in zip(outline, outline[1:]):
        shape_segment(board, a, b, pcbnew.Edge_Cuts)

    add_text(board, "FLIPPING COOL REV B", 5.5, 5.0, 1.8, bold=True)
    add_text(board, "SAFE / RX_DIRECT / MCU_CONTROL", 5.5, 8.0, 1.0)
    add_text(board, "MCU FAILSAFE: RX_DIRECT BYPASSES MCU", 5.5, 10.0, 0.9)
    add_text(board, "ESP32-S3 ANTENNA KEEP-OUT", 63.0, 3.0, 0.8)
    shape_segment(board, (60, 4), (108, 4), pcbnew.F_SilkS, 0.12)
    shape_segment(board, (60, 25), (108, 25), pcbnew.F_SilkS, 0.12)
    shape_segment(board, (60, 4), (60, 25), pcbnew.F_SilkS, 0.12)
    shape_segment(board, (108, 4), (108, 25), pcbnew.F_SilkS, 0.12)

    # Mounting and board-level IO.
    for ref, x, y in [("MH1", 6, 6), ("MH2", 114, 6), ("MH3", 114, 94), ("MH4", 6, 94)]:
        add_footprint(board, ref, "M3 mounting", "mh", x, y)

    j1 = add_footprint(board, "J1", "BATTERY_XT30", "xt30", 13, 19, 90)
    assign_nets(board, j1, {"1": "VBAT_RAW", "2": "GND_PWR"}, nets)
    j2 = add_footprint(board, "J2", "REMOVE_LINK_VBAT", "pin1x02", 28, 12, -90)
    assign_nets(board, j2, {"1": "VBAT_RAW", "2": "VBAT_SW"}, nets)
    f1 = add_footprint(board, "F1", "PTC_500mA_AUX", "fuse1812", 41, 10)
    assign_nets(board, f1, {"1": "VBAT_SW", "2": "VBAT_SW_FUSED"}, nets)
    d1 = add_footprint(board, "D1", "SMBJ12CA_TVS", "sma_diode", 44, 21, 90)
    assign_nets(board, d1, {"1": "VBAT_SW", "2": "GND_PWR"}, nets)
    c1 = add_footprint(board, "C1", "470uF_16V_LOW_ESR", "cp63", 33, 24)
    assign_nets(board, c1, {"1": "VBAT_SW", "2": "GND_PWR"}, nets)
    c2 = add_footprint(board, "C2", "10uF_16V", "c0805", 43, 29)
    assign_nets(board, c2, {"1": "VBAT_SW", "2": "GND_PWR"}, nets)
    r1 = add_footprint(board, "R1", "2.2k", "r0805", 50, 8)
    assign_nets(board, r1, {"1": "VBAT_SW", "2": "PWR_LED_A"}, nets)
    d2 = add_footprint(board, "D2", "PWR_LED", "led0805", 56, 8)
    assign_nets(board, d2, {"1": "PWR_LED_A", "2": "GND_PWR"}, nets)
    tp1 = add_footprint(board, "TP1", "VBAT_RAW", "tp", 21, 7)
    assign_nets(board, tp1, {"1": "VBAT_RAW"}, nets)
    tp2 = add_footprint(board, "TP2", "VBAT_SW", "tp", 38, 7)
    assign_nets(board, tp2, {"1": "VBAT_SW"}, nets)
    tp3 = add_footprint(board, "TP3", "GND", "tp", 48, 7)
    assign_nets(board, tp3, {"1": "GND_PWR"}, nets)

    # Board-mounted power stages.  U20 uses the 5-pin high-current buck footprint
    # contract documented in Rev B; U30 follows the Pololu D24V5Fx pin order.
    u20 = add_footprint(board, "U20", "6V_BUCK_5.5A_MIN", "pin1x05", 17, 42)
    assign_nets(board, u20, {"1": "VBAT_SW", "2": "GND_PWR", "3": "SERVO_6V", "4": "BUCK6_EN", "5": "BUCK6_PG"}, nets)
    c20 = add_footprint(board, "C20", "1000uF_10V_SERVO", "cp63", 31, 42)
    assign_nets(board, c20, {"1": "SERVO_6V", "2": "GND_PWR"}, nets)
    c21 = add_footprint(board, "C21", "100uF_10V", "cp63", 43, 42)
    assign_nets(board, c21, {"1": "SERVO_6V", "2": "GND_PWR"}, nets)
    c22 = add_footprint(board, "C22", "10uF_10V", "c0805", 53, 42)
    assign_nets(board, c22, {"1": "SERVO_6V", "2": "GND_PWR"}, nets)
    fb1 = add_footprint(board, "FB1", "RX_6V_FILTER", "r0805", 56, 47)
    assign_nets(board, fb1, {"1": "SERVO_6V", "2": "RX_6V"}, nets)
    c23 = add_footprint(board, "C23", "22uF_RX", "c0805", 64, 47)
    assign_nets(board, c23, {"1": "RX_6V", "2": "GND_PWR"}, nets)
    tp4 = add_footprint(board, "TP4", "SERVO_6V", "tp", 33, 53)
    assign_nets(board, tp4, {"1": "SERVO_6V"}, nets)
    tp5 = add_footprint(board, "TP5", "RX_6V", "tp", 65, 53)
    assign_nets(board, tp5, {"1": "RX_6V"}, nets)

    u30 = add_footprint(board, "U30", "3V3_BUCK_POL_D24V5F3", "pin1x04", 17, 63)
    assign_nets(board, u30, {"1": "AUX_3V3_SHDN", "2": "VBAT_SW_FUSED", "3": "GND_PWR", "4": "AUX_3V3"}, nets)
    c30 = add_footprint(board, "C30", "47uF_6V3", "cp63", 31, 64)
    assign_nets(board, c30, {"1": "AUX_3V3", "2": "GND_PWR"}, nets)
    c31 = add_footprint(board, "C31", "10uF_6V3", "c0805", 42, 63)
    assign_nets(board, c31, {"1": "AUX_3V3", "2": "GND_PWR"}, nets)
    tp6 = add_footprint(board, "TP6", "AUX_3V3", "tp", 35, 72)
    assign_nets(board, tp6, {"1": "AUX_3V3"}, nets)

    # External ESC and motor harnesses stay off-board by design.
    j20 = add_footprint(board, "J20", "WEKA_POWER_XT30", "xt30", 13, 80, -90)
    assign_nets(board, j20, {"1": "VBAT_SW", "2": "GND_PWR"}, nets)
    j21 = add_footprint(board, "J21", "WEKA_PWM", "pin1x04", 30, 78)
    assign_nets(board, j21, {"1": "GND_PWR", "2": "WEKA_5V_BEC_NC_MON", "3": "PWM_DRIVE_LEFT", "4": "PWM_DRIVE_RIGHT"}, nets)
    motor_pads = [
        ("J23", "WEKA_M1A", 8, 34),
        ("J24", "WEKA_M1B", 8, 48),
        ("J25", "WEKA_M2A", 8, 62),
        ("J26", "WEKA_M2B", 8, 76),
    ]
    for ref, name, x, y in motor_pads:
        pad = add_footprint(board, ref, name, "wirepad", x, y, 90)
        assign_nets(board, pad, {"1": name}, nets)

    # Servo outputs: front/rear weapon channels plus spares.
    for ref, y, signal in [
        ("J30", 79, "PWM_WEAPON_FR"),
        ("J31", 88, "PWM_WEAPON_LR"),
        ("J32", 79, "PWM_SERVO_SPARE1"),
        ("J33", 88, "PWM_SERVO_SPARE2"),
    ]:
        x = 48 if ref in ("J30", "J31") else 63
        hdr = add_footprint(board, ref, f"{signal}_SERVO", "pin1x03", x, y, -90)
        assign_nets(board, hdr, {"1": "GND_PWR", "2": "SERVO_6V", "3": signal}, nets)

    # Receiver, CRSF, and hardware-selected control authority.
    j10 = add_footprint(board, "J10", "MATEK_ELRS_R24_P6_PWM", "pin1x08", 92, 72, 90)
    assign_nets(
        board,
        j10,
        {
            "1": "GND_PWR",
            "2": "RX_6V",
            "3": "RX_PWM_DRIVE_LEFT",
            "4": "RX_PWM_DRIVE_RIGHT",
            "5": "RX_PWM_WEAPON_FR",
            "6": "RX_PWM_WEAPON_LR",
            "7": "PWM_RX_SPARE1",
            "8": "PWM_RX_SPARE2",
        },
        nets,
    )
    j11 = add_footprint(board, "J11", "CRSF_UART", "jst_sh4", 108, 71, 180)
    assign_nets(board, j11, {"1": "GND_PWR", "2": "RX_6V", "3": "CRSF_RX_FROM_RX", "4": "CRSF_TX_TO_RX"}, nets)

    sw1 = add_footprint(board, "SW1", "MODE_SAFE_RX_MCU", "sp3t", 58, 60)
    assign_nets(board, sw1, {"1": "MODE_SAFE", "2": "AUX_3V3", "3": "MODE_RX_DIRECT", "4": "MODE_MCU_CONTROL"}, nets)
    add_text(board, "SW1: SAFE | RX | MCU", 48.5, 54.0, 0.9)

    mux_map = [
        ("U40", 62, 66, "RX_PWM_DRIVE_LEFT", "MCU_PWM_DRIVE_LEFT", "PWM_DRIVE_LEFT"),
        ("U41", 70, 66, "RX_PWM_DRIVE_RIGHT", "MCU_PWM_DRIVE_RIGHT", "PWM_DRIVE_RIGHT"),
        ("U42", 62, 74, "RX_PWM_WEAPON_FR", "MCU_PWM_WEAPON_FR", "PWM_WEAPON_FR"),
        ("U43", 70, 74, "RX_PWM_WEAPON_LR", "MCU_PWM_WEAPON_LR", "PWM_WEAPON_LR"),
    ]
    for ref, x, y, rx, mcu, out in mux_map:
        mux = add_footprint(board, ref, f"SPDT_PWM_MUX_{out}", "sot23_6", x, y)
        assign_nets(board, mux, {"1": rx, "2": "GND_PWR", "3": mcu, "4": out, "5": "MODE_MCU_CONTROL", "6": "AUX_3V3"}, nets)

    # ESP32-S3 module and boot/program/debug support.
    u10 = add_footprint(board, "U10", "ESP32-S3-WROOM-1", "esp32s3", 84, 32)
    assign_nets(
        board,
        u10,
        {
            "1": "GND_PWR",
            "2": "AUX_3V3",
            "3": "ESP_EN",
            "4": "MCU_PWM_DRIVE_LEFT",
            "5": "MCU_PWM_DRIVE_RIGHT",
            "6": "MCU_PWM_WEAPON_FR",
            "7": "MCU_PWM_WEAPON_LR",
            "8": "I2C_SDA",
            "9": "I2C_SCL",
            "10": "STATUS_LED_R_N",
            "11": "STATUS_LED_G_N",
            "12": "STATUS_LED_B_N",
            "15": "ADC_VBAT",
            "16": "ADC_SERVO_6V",
            "17": "ADC_RX_6V",
            "18": "MODE_SAFE",
            "19": "MODE_RX_DIRECT",
            "20": "MODE_MCU_CONTROL",
            "25": "ESP_BOOT",
            "34": "UART0_RXD",
            "35": "UART0_TXD",
            "36": "CRSF_RX_FROM_RX",
            "37": "CRSF_TX_TO_RX",
            "38": "GND_PWR",
            "39": "GND_PWR",
            "40": "GND_PWR",
            "41": "GND_PWR",
        },
        nets,
    )
    c10 = add_footprint(board, "C10", "10uF_3V3_LOCAL", "c0805", 80, 40)
    assign_nets(board, c10, {"1": "AUX_3V3", "2": "GND_PWR"}, nets)
    c11 = add_footprint(board, "C11", "100nF_3V3_LOCAL", "c0805", 84, 40)
    assign_nets(board, c11, {"1": "AUX_3V3", "2": "GND_PWR"}, nets)
    r10 = add_footprint(board, "R10", "10k_EN_PULLUP", "r0805", 79, 35)
    assign_nets(board, r10, {"1": "AUX_3V3", "2": "ESP_EN"}, nets)
    r11 = add_footprint(board, "R11", "10k_BOOT_PULLUP", "r0805", 84, 35)
    assign_nets(board, r11, {"1": "AUX_3V3", "2": "ESP_BOOT"}, nets)
    sw2 = add_footprint(board, "SW2", "RESET", "button", 78, 48)
    assign_nets(board, sw2, {"1": "ESP_EN", "2": "GND_PWR"}, nets)
    sw3 = add_footprint(board, "SW3", "BOOT", "button", 88, 48)
    assign_nets(board, sw3, {"1": "ESP_BOOT", "2": "GND_PWR"}, nets)
    j12 = add_footprint(board, "J12", "UART_PROGRAM", "pin1x06", 109, 37)
    assign_nets(board, j12, {"1": "GND_PWR", "2": "AUX_3V3", "3": "UART0_TXD", "4": "UART0_RXD", "5": "ESP_EN", "6": "ESP_BOOT"}, nets)

    # Sensing, status, and debug/growth ports are populated in Rev B.
    for ref, value, x, y, high, sense in [
        ("R40", "100k", 79, 56, "VBAT_SW", "ADC_VBAT"),
        ("R42", "100k", 79, 60, "SERVO_6V", "ADC_SERVO_6V"),
        ("R44", "100k", 79, 64, "RX_6V", "ADC_RX_6V"),
    ]:
        r = add_footprint(board, ref, value, "r0805", x, y)
        assign_nets(board, r, {"1": high, "2": sense}, nets)
    for ref, value, x, y, sense in [
        ("R41", "47k", 86, 56, "ADC_VBAT"),
        ("R43", "47k", 86, 60, "ADC_SERVO_6V"),
        ("R45", "47k", 86, 64, "ADC_RX_6V"),
    ]:
        r = add_footprint(board, ref, value, "r0805", x, y)
        assign_nets(board, r, {"1": sense, "2": "GND_PWR"}, nets)
    j44 = add_footprint(board, "J44", "PIT_DEBUG", "pin1x06", 106, 52, 90)
    assign_nets(board, j44, {"1": "GND_PWR", "2": "VBAT_SW", "3": "SERVO_6V", "4": "RX_6V", "5": "CRSF_TX_TO_RX", "6": "CRSF_RX_FROM_RX"}, nets)
    j46 = add_footprint(board, "J46", "MCU_POWER_COMMS", "pin1x06", 103, 86, 90)
    assign_nets(board, j46, {"1": "GND_PWR", "2": "AUX_3V3", "3": "BUCK6_PG", "4": "AUX_3V3_SHDN", "5": "CRSF_TX_TO_RX", "6": "CRSF_RX_FROM_RX"}, nets)
    j47 = add_footprint(board, "J47", "MCU_SIGNAL_TAPS", "pin1x06", 81, 86, 90)
    assign_nets(board, j47, {"1": "I2C_SDA", "2": "I2C_SCL", "3": "PWM_DRIVE_LEFT", "4": "PWM_DRIVE_RIGHT", "5": "PWM_WEAPON_FR", "6": "PWM_WEAPON_LR"}, nets)
    j48 = add_footprint(board, "J48", "MCU_SENSE_STATUS", "pin1x06", 81, 94, 90)
    assign_nets(board, j48, {"1": "ADC_VBAT", "2": "ADC_SERVO_6V", "3": "ADC_RX_6V", "4": "STATUS_LED_R_N", "5": "STATUS_LED_G_N", "6": "STATUS_LED_B_N"}, nets)
    j49 = add_footprint(board, "J49", "I2C_STEMMA_QT", "jst_sh4", 105, 94, 180)
    assign_nets(board, j49, {"1": "GND_PWR", "2": "AUX_3V3", "3": "I2C_SDA", "4": "I2C_SCL"}, nets)
    r46 = add_footprint(board, "R46", "4.7k_DNP", "r0805", 98, 92)
    assign_nets(board, r46, {"1": "AUX_3V3", "2": "I2C_SDA"}, nets)
    r47 = add_footprint(board, "R47", "4.7k_DNP", "r0805", 98, 96)
    assign_nets(board, r47, {"1": "AUX_3V3", "2": "I2C_SCL"}, nets)

    for ref, x, y, color_net in [
        ("R50", 50, 94, "STATUS_LED_R_A"),
        ("R51", 59, 94, "STATUS_LED_G_A"),
        ("R52", 68, 94, "STATUS_LED_B_A"),
    ]:
        r = add_footprint(board, ref, "330", "r0805", x, y)
        assign_nets(board, r, {"1": "AUX_3V3", "2": color_net}, nets)
    for ref, x, y, color_a, color_n in [
        ("D50", 53, 96, "STATUS_LED_R_A", "STATUS_LED_R_N"),
        ("D51", 62, 96, "STATUS_LED_G_A", "STATUS_LED_G_N"),
        ("D52", 71, 96, "STATUS_LED_B_A", "STATUS_LED_B_N"),
    ]:
        led = add_footprint(board, ref, "STATUS_LED", "led0805", x, y)
        assign_nets(board, led, {"1": color_a, "2": color_n}, nets)

    for idx, (name, x, y) in enumerate(
        [
            ("MODE_SAFE", 52, 67),
            ("MODE_RX_DIRECT", 52, 70),
            ("MODE_MCU_CONTROL", 52, 73),
            ("ADC_VBAT", 93, 56),
            ("ADC_SERVO_6V", 93, 60),
            ("ADC_RX_6V", 93, 64),
            ("PWM_DRIVE_LEFT", 37, 88),
            ("PWM_DRIVE_RIGHT", 40, 88),
            ("PWM_WEAPON_FR", 44, 88),
            ("PWM_WEAPON_LR", 47, 88),
        ],
        start=7,
    ):
        tp = add_footprint(board, f"TP{idx}", name, "tp", x, y)
        assign_nets(board, tp, {"1": name}, nets)

    # Ground pours on all copper layers, shaped around the ESP32 antenna keepout.
    gnd_poly = [(2, 2), (60, 2), (60, 26), (118, 26), (118, 92), (112, 98), (8, 98), (2, 92)]
    for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        add_zone(board, nets["GND_PWR"], layer, gnd_poly, 0.30)

    route_failures = route_board_with_astar(board)
    if route_failures:
        add_text(board, f"ROUTE REVIEW: {len(route_failures)} open nets", 5.5, 13.0, 0.9, pcbnew.F_SilkS)

    # Wide motor pass-through lanes for WEKA motor output harness pads.
    # These are single-pad external contracts in this board revision, but the
    # thick pads and silkscreen naming make the off-board wiring explicit.
    for ref, name, x, y in motor_pads:
        add_text(board, name, x + 4.0, y - 4.5, 0.9)

    for ref in ("J1", "J2", "J20", "J21", "J30", "J31", "J32", "J33", "J10", "J11"):
        fp = board.FindFootprintByReference(ref)
        if fp:
            x, y = pad_center_mm(next(iter(fp.Pads())))
            add_text(board, ref, x - 2.0, y - 3.0, 0.8)

    # Stitch GND across layers around the power and control sections while
    # staying out of the ESP antenna keepout.
    return board


def export_fab() -> None:
    FAB_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "--output", str(FAB_DIR), str(BOARD_PATH)], check=True)
    subprocess.run(["kicad-cli", "pcb", "export", "drill", "--output", str(FAB_DIR), str(BOARD_PATH)], check=True)
    subprocess.run(["kicad-cli", "pcb", "export", "pos", "--output", str(FAB_DIR / "flipping-cool-rev-b-pos.csv"), str(BOARD_PATH)], check=True)
    subprocess.run(["kicad-cli", "pcb", "export", "step", "--output", str(FAB_DIR / "flipping-cool-rev-b.step"), str(BOARD_PATH)], check=True)
    for view, layer in [("top", "F.Cu"), ("bottom", "B.Cu")]:
        subprocess.run(
            [
                "kicad-cli",
                "pcb",
                "render",
                "--side",
                view,
                "--output",
                str(FAB_DIR / f"flipping-cool-rev-b-{view}.png"),
                str(BOARD_PATH),
            ],
            check=True,
        )


def archive_fab() -> None:
    zip_path = FAB_DIR / "flipping-cool-rev-b-fab.zip"
    zip_path.unlink(missing_ok=True)
    tmp_zip_base = Path("/tmp/flipping-cool-rev-b-fab")
    tmp_zip = tmp_zip_base.with_suffix(".zip")
    tmp_zip.unlink(missing_ok=True)
    shutil.make_archive(str(tmp_zip_base), "zip", FAB_DIR)
    shutil.move(str(tmp_zip), str(zip_path))


def write_fab_readme() -> None:
    readme = FAB_DIR / "README.md"
    readme.write_text(
        """# Flipping Cool Rev B Fab Package

Generated by `../build_rev_b_pcb.py`.

Contents:

- Gerbers and drill files for the Rev B 4-layer integrated control/power PCB.
- Pick-and-place CSV for assembly-service review.
- STEP export and top/bottom renders for mechanical/visual checks.
- `flipping-cool-rev-b-fab.zip` archive of this folder.

Rev B target: about `120 x 100 mm`, ESP32-S3 controller, on-board `SERVO_6V`
and `AUX_3V3` regulators, receiver-priority hardware mode selection, external
Matek receiver, external WEKA ESC, external motors/servos/battery.

Status: this folder is a generated validation package, not an order-ready fab
release yet. Run KiCad DRC and do not fabricate until the report has zero
errors and zero required unconnected items.
""",
        encoding="utf-8",
    )


def main() -> None:
    board = build_board()
    pcbnew.SaveBoard(str(BOARD_PATH), board)
    # KiCad 9's Python zone filler is stable after a save/load round trip.
    # Filling directly on a brand-new in-memory board can crash pcbnew.
    board = pcbnew.LoadBoard(str(BOARD_PATH))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD_PATH), board)
    export_fab()
    write_fab_readme()
    archive_fab()
    print(f"Generated {BOARD_PATH}")
    print(f"Generated {FAB_DIR}")


if __name__ == "__main__":
    main()
