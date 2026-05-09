#!/usr/bin/env python3
"""Generate the Flipping Cool Rev B integrated control/power PCB.

The Rev B board intentionally replaces the old Rev A harness board as the
active PCB target.  Rev A remains documented in the project history; this
script is the reproducible source for the integrated Rev B layout.
"""

from __future__ import annotations

import argparse
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
                text.SetVisible(False)
            elif text.GetText() == value:
                text.SetVisible(False)
    item.Reference().SetVisible(False)
    item.Value().SetVisible(False)
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
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in points:
        outline.Append(P(x, y))
    board.Add(zone)


def pad_center_mm(pad: pcbnew.PAD) -> tuple[float, float]:
    c = pad.GetCenter()
    return pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)


def pad_clearance_radius_mm(pad: pcbnew.PAD) -> float:
    """Conservative keep-out radius for a pad on internal routing layers."""
    size = pad.GetSize()
    pad_radius = max(pcbnew.ToMM(size.x), pcbnew.ToMM(size.y)) / 2.0
    # Keep a manufacturing-friendly buffer so internal routes do not clip
    # annular rings or create near-pad clearance/soldermask violations.
    return pad_radius + 0.40


def pads_by_net(board: pcbnew.BOARD) -> dict[str, list[pcbnew.PAD]]:
    result: dict[str, list[pcbnew.PAD]] = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            name = pad.GetNetname()
            if name:
                result.setdefault(name, []).append(pad)
    return result


def dedupe_exact_vias(board: pcbnew.BOARD) -> int:
    """Remove exact duplicate vias generated by back-to-back routing steps."""
    seen: set[tuple[int, int, int, int, int, str]] = set()
    removed = 0
    for item in list(board.GetTracks()):
        if not isinstance(item, pcbnew.PCB_VIA):
            continue
        pos = item.GetPosition()
        key = (
            pos.x,
            pos.y,
            item.GetNetCode(),
            item.GetWidth(pcbnew.F_Cu),
            item.GetDrillValue(),
            item.GetLayerSet().FmtHex(),
        )
        if key in seen:
            board.Delete(item)
            removed += 1
            continue
        seen.add(key)
    return removed


def bridge_local_islands(board: pcbnew.BOARD) -> None:
    """Bridge known near-touch islands left by coarse grid autorouting."""

    nets = board.GetNetsByName()

    def add_seg(net_name: str, x1: float, y1: float, x2: float, y2: float, layer: int, width_mm: float = 0.20) -> None:
        if net_name not in nets:
            return
        if x1 == x2 and y1 == y2:
            return
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(P(x1, y1))
        t.SetEnd(P(x2, y2))
        t.SetWidth(MM(width_mm))
        t.SetLayer(layer)
        t.SetNet(nets[net_name])
        board.Add(t)

    def add_via(net_name: str, x: float, y: float, size_mm: float = 0.40, drill_mm: float = 0.20) -> None:
        if net_name not in nets:
            return
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(P(x, y))
        v.SetWidth(MM(size_mm))
        v.SetDrill(MM(drill_mm))
        v.SetNet(nets[net_name])
        board.Add(v)

    # Keep deterministic local stitches minimal; larger broad-stroke stitching
    # regresses into shorts/crossings in dense clusters.
    add_seg("MCU_PWM_DRIVE_RIGHT", 75.25, 31.82, 75.00, 32.00, pcbnew.In2_Cu, 0.20)
    add_seg("CRSF_RX_FROM_RX", 92.75, 31.82, 93.00, 32.50, pcbnew.In2_Cu, 0.20)
    add_seg("ESP_EN", 75.00, 29.50, 75.25, 29.28, pcbnew.In1_Cu, 0.20)
    add_seg("ESP_EN", 75.00, 29.50, 75.25, 29.28, pcbnew.In2_Cu, 0.20)
    add_seg("STATUS_LED_B_N", 75.00, 40.50, 75.25, 40.71, pcbnew.In2_Cu, 0.20)
    add_seg("MODE_SAFE", 55.00, 58.57, 52.00, 58.57, pcbnew.F_Cu, 0.20)
    add_seg("MODE_SAFE", 52.00, 58.57, 52.00, 67.00, pcbnew.F_Cu, 0.20)
    add_seg("STATUS_LED_R_N", 75.25, 38.17, 74.20, 38.80, pcbnew.F_Cu, 0.20)
    add_seg("STATUS_LED_R_N", 74.20, 38.80, 66.00, 38.80, pcbnew.F_Cu, 0.20)
    add_seg("STATUS_LED_R_N", 66.00, 38.80, 66.00, 80.00, pcbnew.F_Cu, 0.20)
    add_seg("STATUS_LED_R_N", 66.00, 80.00, 64.80, 80.00, pcbnew.F_Cu, 0.20)
    add_seg("STATUS_LED_R_N", 64.80, 80.00, 64.80, 82.20, pcbnew.F_Cu, 0.20)
    add_seg("STATUS_LED_R_N", 64.80, 82.20, 66.00, 82.20, pcbnew.F_Cu, 0.20)
    add_seg("STATUS_LED_R_N", 66.00, 82.20, 66.00, 98.00, pcbnew.F_Cu, 0.20)
    add_seg("STATUS_LED_R_N", 66.00, 98.00, 53.9375, 98.00, pcbnew.F_Cu, 0.20)
    add_seg("STATUS_LED_R_N", 53.9375, 98.00, 53.9375, 96.00, pcbnew.F_Cu, 0.20)



def prune_known_orphan_stubs(board: pcbnew.BOARD) -> None:
    """Delete deterministic orphan micro-stubs that trigger dangling-track DRC."""

    def is_near(val: float, target: float, tol: float = 0.35) -> bool:
        return abs(val - target) <= tol

    for item in list(board.GetTracks()):
        if isinstance(item, pcbnew.PCB_VIA):
            if item.GetNetname() == "STATUS_LED_R_N":
                p = item.GetPosition()
                x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
                if is_near(x, 75.25) and is_near(y, 38.17):
                    board.Delete(item)
            continue
        net = item.GetNetname()
        layer = item.GetLayer()
        start = item.GetStart()
        end = item.GetEnd()
        sx, sy = pcbnew.ToMM(start.x), pcbnew.ToMM(start.y)
        ex, ey = pcbnew.ToMM(end.x), pcbnew.ToMM(end.y)
        cx, cy = (sx + ex) / 2.0, (sy + ey) / 2.0
        length = math.hypot(ex - sx, ey - sy)

        if (
            net == "CRSF_RX_FROM_RX"
            and layer == pcbnew.In2_Cu
            and length <= 0.70
            and is_near(cx, 93.0)
            and is_near(cy, 32.5)
        ):
            board.Delete(item)
            continue

        if (
            net == "STATUS_LED_R_N"
            and layer == pcbnew.In2_Cu
            and length <= 2.10
            and is_near(cx, 73.0)
            and is_near(cy, 38.0)
        ):
            board.Delete(item)
            continue

        if (
            net == "ESP_EN"
            and layer == pcbnew.In1_Cu
            and length <= 1.20
            and is_near(cx, 74.5)
            and is_near(cy, 30.0)
        ):
            board.Delete(item)
            continue

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

    All copper pads are treated as keep-outs on internal routing layers. While
    SMD pads are on outer copper, route vias/segments generated by this script
    can otherwise clip pad clearances and trigger short/mask violations.
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
            x, y = pad_center_mm(pad)
            if attr == pcbnew.PAD_ATTRIB_NPTH:
                radius = max(2.2, pad_clearance_radius_mm(pad))
            else:
                radius = pad_clearance_radius_mm(pad)
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


def astar_path_2d(
    start: tuple[int, int],
    goals: set[tuple[int, int]],
    blocked: set[tuple[int, int]],
    max_x: int = grid_coord(119),
    max_y: int = grid_coord(99),
) -> list[tuple[int, int]] | None:
    def heuristic(node: tuple[int, int]) -> float:
        x, y = node
        return min(abs(x - gx) + abs(y - gy) for gx, gy in goals)

    queue: list[tuple[float, float, tuple[int, int]]] = []
    heapq.heappush(queue, (heuristic(start), 0.0, start))
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    cost_so_far = {start: 0.0}

    while queue:
        _, cost, current = heapq.heappop(queue)
        if current in goals:
            path = [current]
            while came_from[path[-1]] is not None:
                path.append(came_from[path[-1]])
            path.reverse()
            return path
        x, y = current
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nx < 2 or nx > max_x or ny < 2 or ny > max_y:
                continue
            nxt = (nx, ny)
            if nxt in blocked and nxt not in goals:
                continue
            new_cost = cost_so_far[current] + 1.0
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                came_from[nxt] = current
                heapq.heappush(queue, (new_cost + heuristic(nxt), new_cost, nxt))
    return None


def mark_disc_2d(blocked: set[tuple[int, int]], x: float, y: float, radius: float) -> None:
    gx = grid_coord(x)
    gy = grid_coord(y)
    gr = max(1, math.ceil(radius / GRID_MM))
    for ix in range(gx - gr, gx + gr + 1):
        for iy in range(gy - gr, gy + gr + 1):
            if (world_coord(ix) - x) ** 2 + (world_coord(iy) - y) ** 2 <= radius**2:
                blocked.add((ix, iy))


def mark_segment_2d(blocked: set[tuple[int, int]], a: tuple[float, float], b: tuple[float, float], radius: float) -> None:
    ax, ay = a
    bx, by = b
    dist = max(abs(bx - ax), abs(by - ay))
    steps = max(1, math.ceil(dist / (GRID_MM / 2)))
    for i in range(steps + 1):
        t = i / steps
        mark_disc_2d(blocked, ax + (bx - ax) * t, ay + (by - ay) * t, radius)


def back_layer_obstacles(
    board: pcbnew.BOARD,
    net_name: str,
    *,
    pad_scale: float = 1.0,
    track_margin: float = 0.25,
) -> set[tuple[int, int]]:
    blocked: set[tuple[int, int]] = set()

    # Board edges and antenna keepout.
    for x in [i * GRID_MM for i in range(grid_coord(0), grid_coord(120) + 1)]:
        mark_disc_2d(blocked, x, 0.0, 1.0)
        mark_disc_2d(blocked, x, 100.0, 1.0)
    for y in [i * GRID_MM for i in range(grid_coord(0), grid_coord(100) + 1)]:
        mark_disc_2d(blocked, 0.0, y, 1.0)
        mark_disc_2d(blocked, 120.0, y, 1.0)
    for x in [i * GRID_MM for i in range(grid_coord(60), grid_coord(108) + 1)]:
        for y in [j * GRID_MM for j in range(grid_coord(4), grid_coord(25) + 1)]:
            mark_disc_2d(blocked, x, y, 0.35)

    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == net_name:
                continue
            x, y = pad_center_mm(pad)
            attr = pad.GetAttribute()
            if attr == pcbnew.PAD_ATTRIB_NPTH:
                radius = max(2.2 * pad_scale, pad_clearance_radius_mm(pad) * pad_scale)
            else:
                radius = pad_clearance_radius_mm(pad) * pad_scale
            mark_disc_2d(blocked, x, y, radius)

    for item in board.GetTracks():
        if item.GetNetname() == net_name:
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            p = item.GetPosition()
            x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
            via_size = pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu))
            mark_disc_2d(blocked, x, y, via_size / 2 + track_margin)
            continue
        if item.GetLayer() != pcbnew.B_Cu:
            continue
        s = item.GetStart()
        e = item.GetEnd()
        a = (pcbnew.ToMM(s.x), pcbnew.ToMM(s.y))
        b = (pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))
        width = pcbnew.ToMM(item.GetWidth())
        mark_segment_2d(blocked, a, b, width / 2 + track_margin)

    return blocked


def inner_layer_obstacles(
    board: pcbnew.BOARD,
    net_name: str,
    *,
    pad_scale: float = 1.0,
    track_margin: float = 0.25,
) -> set[tuple[int, int, int]]:
    blocked: set[tuple[int, int, int]] = set()

    # Board edges and antenna keepout.
    for x in [i * GRID_MM for i in range(grid_coord(0), grid_coord(120) + 1)]:
        mark_disc(blocked, x, 0.0, 1.0)
        mark_disc(blocked, x, 100.0, 1.0)
    for y in [i * GRID_MM for i in range(grid_coord(0), grid_coord(100) + 1)]:
        mark_disc(blocked, 0.0, y, 1.0)
        mark_disc(blocked, 120.0, y, 1.0)
    for x in [i * GRID_MM for i in range(grid_coord(60), grid_coord(108) + 1)]:
        for y in [j * GRID_MM for j in range(grid_coord(4), grid_coord(25) + 1)]:
            mark_disc(blocked, x, y, 0.35)

    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == net_name:
                continue
            x, y = pad_center_mm(pad)
            attr = pad.GetAttribute()
            if attr == pcbnew.PAD_ATTRIB_NPTH:
                radius = max(2.2 * pad_scale, pad_clearance_radius_mm(pad) * pad_scale)
            else:
                radius = pad_clearance_radius_mm(pad) * pad_scale
            mark_disc(blocked, x, y, radius)

    for item in board.GetTracks():
        if item.GetNetname() == net_name:
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            p = item.GetPosition()
            x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
            via_size = pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu))
            mark_disc(blocked, x, y, via_size / 2 + track_margin)
            continue
        if item.GetLayer() not in ROUTE_LAYERS:
            continue
        s = item.GetStart()
        e = item.GetEnd()
        a = (pcbnew.ToMM(s.x), pcbnew.ToMM(s.y))
        b = (pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))
        width = pcbnew.ToMM(item.GetWidth())
        mark_segment(blocked, a, b, item.GetLayer(), width / 2 + track_margin)

    return blocked


def ensure_terminal_via(
    board: pcbnew.BOARD,
    net_item: pcbnew.NETINFO_ITEM,
    x: float,
    y: float,
    size_mm: float,
    drill_mm: float,
) -> None:
    tx = MM(x)
    ty = MM(y)
    for item in board.GetTracks():
        if not isinstance(item, pcbnew.PCB_VIA):
            continue
        if item.GetNetCode() != net_item.GetNetCode():
            continue
        p = item.GetPosition()
        if abs(p.x - tx) <= MM(0.01) and abs(p.y - ty) <= MM(0.01):
            return
    via(board, net_item, x, y, size_mm, drill_mm)


def best_pad_pair_for_refs(board: pcbnew.BOARD, net_name: str, src_ref: str, dst_ref: str) -> tuple[pcbnew.PAD, pcbnew.PAD] | None:
    src_fp = board.FindFootprintByReference(src_ref)
    dst_fp = board.FindFootprintByReference(dst_ref)
    if not src_fp or not dst_fp:
        return None
    src_pads = [pad for pad in src_fp.Pads() if pad.GetNetname() == net_name]
    dst_pads = [pad for pad in dst_fp.Pads() if pad.GetNetname() == net_name]
    if not src_pads or not dst_pads:
        return None
    best: tuple[float, pcbnew.PAD, pcbnew.PAD] | None = None
    for sp in src_pads:
        sx, sy = pad_center_mm(sp)
        for dp in dst_pads:
            dx, dy = pad_center_mm(dp)
            d = abs(sx - dx) + abs(sy - dy)
            if best is None or d < best[0]:
                best = (d, sp, dp)
    if best is None:
        return None
    return best[1], best[2]


def route_failed_pair_on_back(
    board: pcbnew.BOARD,
    failure: str,
    *,
    pad_scale: float = 1.0,
    track_margin: float = 0.25,
) -> bool:
    # Format: "<NET>: <SRC_REF> to <DST_REF>"
    if ": " not in failure or " to " not in failure:
        return False
    net_name, rest = failure.split(": ", 1)
    src_ref, dst_ref = rest.split(" to ", 1)

    pair = best_pad_pair_for_refs(board, net_name, src_ref.strip(), dst_ref.strip())
    if pair is None:
        return False
    src_pad, dst_pad = pair
    net_item = src_pad.GetNet()
    sx, sy = pad_center_mm(src_pad)
    dx, dy = pad_center_mm(dst_pad)

    blocked = back_layer_obstacles(board, net_name, pad_scale=pad_scale, track_margin=track_margin)
    start = (grid_coord(sx), grid_coord(sy))
    goal = (grid_coord(dx), grid_coord(dy))
    blocked.discard(start)
    blocked.discard(goal)
    path = astar_path_2d(start, {goal}, blocked)
    if path is None:
        return False

    if src_pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
        ensure_terminal_via(board, net_item, sx, sy, 0.40, 0.20)
    if dst_pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
        ensure_terminal_via(board, net_item, dx, dy, 0.40, 0.20)

    compressed: list[tuple[int, int]] = [path[0]]
    for point in path[1:]:
        if len(compressed) >= 2:
            ax, ay = compressed[-2]
            bx, by = compressed[-1]
            px, py = point
            if (ax == bx == px) or (ay == by == py):
                compressed[-1] = point
                continue
        compressed.append(point)

    for (ax, ay), (bx, by) in zip(compressed, compressed[1:]):
        track(
            board,
            net_item,
            P(world_coord(ax), world_coord(ay)),
            P(world_coord(bx), world_coord(by)),
            0.20,
            pcbnew.B_Cu,
        )
    return True


def route_failed_pair_on_inner(
    board: pcbnew.BOARD,
    failure: str,
    *,
    pad_scale: float = 1.0,
    track_margin: float = 0.25,
) -> bool:
    # Format: "<NET>: <SRC_REF> to <DST_REF>"
    if ": " not in failure or " to " not in failure:
        return False
    net_name, rest = failure.split(": ", 1)
    src_ref, dst_ref = rest.split(" to ", 1)

    pair = best_pad_pair_for_refs(board, net_name, src_ref.strip(), dst_ref.strip())
    if pair is None:
        return False
    src_pad, dst_pad = pair
    net_item = src_pad.GetNet()
    sx, sy = pad_center_mm(src_pad)
    dx, dy = pad_center_mm(dst_pad)

    blocked = inner_layer_obstacles(board, net_name, pad_scale=pad_scale, track_margin=track_margin)
    starts = [(grid_coord(sx), grid_coord(sy), 0), (grid_coord(sx), grid_coord(sy), 1)]
    goals = {(grid_coord(dx), grid_coord(dy), 0), (grid_coord(dx), grid_coord(dy), 1)}
    for node in starts:
        blocked.discard(node)
    for node in goals:
        blocked.discard(node)

    best_path: list[tuple[int, int, int]] | None = None
    for st in starts:
        path = astar_path(st, goals, blocked)
        if path is None:
            continue
        if best_path is None or len(path) < len(best_path):
            best_path = path
    if best_path is None:
        return False

    if src_pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
        ensure_terminal_via(board, net_item, sx, sy, 0.40, 0.20)
    if dst_pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
        ensure_terminal_via(board, net_item, dx, dy, 0.40, 0.20)

    emit_astar_route(board, net_item, best_path, 0.20, 0.40, 0.20, set())
    return True


def route_failed_pairs_on_back(board: pcbnew.BOARD, failures: list[str]) -> list[str]:
    unresolved: list[str] = []
    for failure in failures:
        if route_failed_pair_on_back(board, failure):
            continue
        # Alternate pairings for multi-node nets that can still satisfy the
        # missing connection without forcing the original source/destination.
        if failure.startswith("MODE_SAFE:"):
            if route_failed_pair_on_inner(board, "MODE_SAFE: U10 to SW1"):
                continue
            if route_failed_pair_on_inner(board, failure):
                continue
            if route_failed_pair_on_back(board, "MODE_SAFE: U10 to SW1", pad_scale=0.60, track_margin=0.10):
                continue
        if failure.startswith("STATUS_LED_R_N:"):
            if route_failed_pair_on_back(board, "STATUS_LED_R_N: U10 to J48"):
                continue
            if route_failed_pair_on_back(board, "STATUS_LED_R_N: U10 to J48", pad_scale=0.45, track_margin=0.05):
                continue
        unresolved.append(failure)
    return unresolved


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
            mark_disc(routed_obstacles, world_coord(ax), world_coord(ay), via_size / 2 + 0.35)
        else:
            layer = ROUTE_LAYERS[al]
            start = (world_coord(ax), world_coord(ay))
            end = (world_coord(bx), world_coord(by))
            track(board, net_item, P(*start), P(*end), width_mm, layer)
            mark_segment(routed_obstacles, start, end, layer, width_mm / 2 + 0.40)


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
        width = 0.70 if name in {"VBAT_RAW", "VBAT_SW", "SERVO_6V"} else 0.20
        via_size = 0.65 if width >= 0.7 else 0.40
        via_drill = 0.30 if width >= 0.7 else 0.20
        routed_for_this_net: set[tuple[int, int, int]] = routed_obstacles_by_net.setdefault(name, set())
        placed_terminal_vias: set[tuple[int, int]] = set()
        connected = [pads[0]]
        remaining = pads[1:]

        while remaining:
            best = None
            for src in connected:
                sx, sy = pad_center_mm(src)
                starts = [(grid_coord(sx), grid_coord(sy), 0), (grid_coord(sx), grid_coord(sy), 1)]
                for dst in remaining:
                    dx, dy = pad_center_mm(dst)
                    goals = {(grid_coord(dx), grid_coord(dy), 0), (grid_coord(dx), grid_coord(dy), 1)}
                    for st in starts:
                        candidate = astar_path(st, goals, all_blocked)
                        if candidate is None:
                            continue
                        score = len(candidate)
                        if best is None or score < best[0]:
                            best = (score, src, dst, candidate, sx, sy, dx, dy)

            if best is None:
                source = connected[0]
                failures.extend(
                    f"{name}: {source.GetParentFootprint().GetReference()} to {pad.GetParentFootprint().GetReference()}"
                    for pad in remaining
                )
                break

            _, source, pad, path, sx, sy, dx, dy = best
            if source.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                key = (round(sx * 1000), round(sy * 1000))
                if key not in placed_terminal_vias:
                    via(board, net_item, sx, sy, via_size, via_drill)
                    placed_terminal_vias.add(key)
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                key = (round(dx * 1000), round(dy * 1000))
                if key not in placed_terminal_vias:
                    via(board, net_item, dx, dy, via_size, via_drill)
                    placed_terminal_vias.add(key)
            emit_astar_route(board, net_item, path, width, via_size, via_drill, routed_for_this_net)
            connected.append(pad)
            remaining.remove(pad)
        all_blocked.update(routed_for_this_net)
    return failures


def build_board() -> pcbnew.BOARD:
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.m_ViasMinSize = MM(0.40)
    ds.m_MinThroughDrill = MM(0.20)
    ds.m_HoleClearance = MM(0.15)
    ds.m_HoleToHoleMin = MM(0.15)
    ds.m_ViasMinAnnularWidth = MM(0.10)
    ds.m_MinClearance = MM(0.0)
    ds.m_SilkClearance = MM(0.0)
    ds.SetCustomViaSize(MM(0.40))
    ds.SetCustomViaDrill(MM(0.20))
    ds.UseCustomTrackViaSize(True)
    board.SetCopperLayerCount(4)
    board.SetLayerName(pcbnew.In1_Cu, "In1.Cu")
    board.SetLayerName(pcbnew.In2_Cu, "In2.Cu")
    board.SetLayerType(pcbnew.F_Cu, pcbnew.LT_SIGNAL)
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.B_Cu, pcbnew.LT_SIGNAL)
    default_nc = board.GetAllNetClasses().get("Default")
    if default_nc is not None:
        default_nc.SetClearance(MM(0.10))

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

    shape_segment(board, (60, 4), (108, 4), pcbnew.Cmts_User, 0.12)
    shape_segment(board, (60, 25), (108, 25), pcbnew.Cmts_User, 0.12)
    shape_segment(board, (60, 4), (60, 25), pcbnew.Cmts_User, 0.12)
    shape_segment(board, (108, 4), (108, 25), pcbnew.Cmts_User, 0.12)

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
    tp2 = add_footprint(board, "TP2", "VBAT_SW", "tp", 34, 6)
    assign_nets(board, tp2, {"1": "VBAT_SW"}, nets)
    tp3 = add_footprint(board, "TP3", "GND", "tp", 44, 6)
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
        ("J26", "WEKA_M2B", 8, 70),
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
    j11 = add_footprint(board, "J11", "CRSF_UART", "jst_sh4", 114, 64, 180)
    assign_nets(board, j11, {"1": "GND_PWR", "2": "RX_6V", "3": "CRSF_RX_FROM_RX", "4": "CRSF_TX_TO_RX"}, nets)

    sw1 = add_footprint(board, "SW1", "MODE_SAFE_RX_MCU", "sp3t", 58, 60)
    assign_nets(board, sw1, {"1": "MODE_SAFE", "2": "AUX_3V3", "3": "MODE_RX_DIRECT", "4": "MODE_MCU_CONTROL"}, nets)
    add_text(board, "SW1: SAFE | RX | MCU", 48.5, 54.0, 0.9, pcbnew.Cmts_User)

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
    for pad in u10.Pads():
        if pad.GetNumber() == "41":
            pad.SetNet(nets["GND_PWR"])
    c10 = add_footprint(board, "C10", "10uF_3V3_LOCAL", "c0805", 72, 52)
    assign_nets(board, c10, {"1": "AUX_3V3", "2": "GND_PWR"}, nets)
    c11 = add_footprint(board, "C11", "100nF_3V3_LOCAL", "c0805", 76, 52)
    assign_nets(board, c11, {"1": "AUX_3V3", "2": "GND_PWR"}, nets)
    r10 = add_footprint(board, "R10", "10k_EN_PULLUP", "r0805", 72, 44)
    assign_nets(board, r10, {"1": "AUX_3V3", "2": "ESP_EN"}, nets)
    r11 = add_footprint(board, "R11", "10k_BOOT_PULLUP", "r0805", 68, 46)
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
    j44 = add_footprint(board, "J44", "PIT_DEBUG", "pin1x06", 100, 58, 90)
    assign_nets(board, j44, {"1": "VBAT_SW", "2": "GND_PWR", "3": "SERVO_6V", "4": "RX_6V", "5": "CRSF_TX_TO_RX", "6": "CRSF_RX_FROM_RX"}, nets)
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
                ("PWM_DRIVE_LEFT", 37, 84),
                ("PWM_DRIVE_RIGHT", 40, 84),
                ("PWM_WEAPON_FR", 44, 84),
                ("PWM_WEAPON_LR", 47, 84),
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
    route_failures = route_failed_pairs_on_back(board, route_failures)
    dedupe_exact_vias(board)
    bridge_local_islands(board)
    prune_known_orphan_stubs(board)
    if route_failures:
        print("Route failures:")
        for failure in route_failures:
            print(f"  {failure}")
        add_text(board, f"ROUTE REVIEW: {len(route_failures)} open nets", 5.5, 13.0, 0.9, pcbnew.Cmts_User)

    # Wide motor pass-through lanes for WEKA motor output harness pads.
    # These are single-pad external contracts in this board revision, but the
    # thick pads and silkscreen naming make the off-board wiring explicit.
    for ref, name, x, y in motor_pads:
        add_text(board, name, x + 4.0, y - 4.5, 0.9, pcbnew.Cmts_User)

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
    parser = argparse.ArgumentParser(description="Build Flipping Cool Rev B PCB")
    parser.add_argument(
        "--with-fab",
        action="store_true",
        help="also regenerate fab_rev_b outputs (only after ERC/DRC are clean)",
    )
    args = parser.parse_args()

    board = build_board()
    pcbnew.SaveBoard(str(BOARD_PATH), board)
    # KiCad 9's Python zone filler is stable after a save/load round trip.
    # Filling directly on a brand-new in-memory board can crash pcbnew.
    board = pcbnew.LoadBoard(str(BOARD_PATH))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD_PATH), board)
    if args.with_fab:
        export_fab()
        write_fab_readme()
        archive_fab()
    print(f"Generated {BOARD_PATH}")
    if args.with_fab:
        print(f"Generated {FAB_DIR}")


if __name__ == "__main__":
    main()
