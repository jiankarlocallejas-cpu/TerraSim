"""D-infinity flow direction and upslope contributing-area routing.

Each cell routes along the steepest descent over one of eight triangular
facets and splits its contribution between the facet's lower neighbors,
following Tarboton (1997). This is terrain routing, not a fluid solver.
Depressions are left as terminal cells for explicit upstream conditioning.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


# Counterclockwise from east; raster rows increase south.
_NEIGHBORS: tuple[tuple[int, int], ...] = (
    (0, 1),    # E
    (-1, 1),   # NE
    (-1, 0),   # N
    (-1, -1),  # NW
    (0, -1),   # W
    (1, -1),   # SW
    (1, 0),    # S
    (1, 1),    # SE
)
_NO_ROUTE = np.uint8(255)


@dataclass(frozen=True)
class DInfinityResult:
    """Routing outputs on the input raster grid.

    Direction is radians counterclockwise from east. Contributing area uses
    square map units and includes each cell's own area. Direction is NaN for
    nodata cells and terminal cells. The masks distinguish those cases.
    """

    flow_direction: np.ndarray
    contributing_area: np.ndarray
    terminal_mask: np.ndarray
    valid_mask: np.ndarray


def route_dinf(
    elevation: np.ndarray,
    cell_size_x: float = 1.0,
    cell_size_y: float | None = None,
    nodata: float | None = None,
) -> DInfinityResult:
    """Compute D-infinity directions and upslope contributing area.

    Input coordinates are assumed to be in a projected CRS with linear units.
    Flats and depressions are not filled or breached. Flow is routed only to
    valid in-grid cells, so terminal area remains on sinks and at the boundary.
    """
    dem = np.asarray(elevation, dtype=np.float64)
    if dem.ndim != 2:
        raise ValueError("elevation must be a two-dimensional array")
    if dem.size == 0:
        raise ValueError("elevation grid cannot be empty")
    if not math.isfinite(cell_size_x) or cell_size_x <= 0:
        raise ValueError("cell_size_x must be positive and finite")
    if cell_size_y is None:
        cell_size_y = cell_size_x
    if not math.isfinite(cell_size_y) or cell_size_y <= 0:
        raise ValueError("cell_size_y must be positive and finite")

    valid = np.isfinite(dem)
    if nodata is not None and math.isfinite(nodata):
        valid &= dem != nodata

    rows, cols = dem.shape
    count = dem.size
    flat_dem = dem.ravel()
    flat_valid = valid.ravel()

    # Compact routing state: sector and split fraction identify both receivers.
    sector = np.full(count, _NO_ROUTE, dtype=np.uint8)
    split_second = np.zeros(count, dtype=np.float32)
    direction = np.full(count, np.nan, dtype=np.float32)
    inflow_count = np.zeros(count, dtype=np.uint8)

    distances = [
        math.hypot(dc * cell_size_x, dr * cell_size_y)
        for dr, dc in _NEIGHBORS
    ]
    bearings = [
        math.atan2(-dr * cell_size_y, dc * cell_size_x) % (2.0 * math.pi)
        for dr, dc in _NEIGHBORS
    ]
    spans = [
        (bearings[(i + 1) % 8] - bearings[i]) % (2.0 * math.pi)
        for i in range(8)
    ]

    # Find the steepest edge or in-facet plane descent for each cell.
    # Receivers are strictly lower, making the graph acyclic.
    for row in range(rows):
        for col in range(cols):
            source = row * cols + col
            if not flat_valid[source]:
                continue
            z0 = flat_dem[source]
            best_slope = 0.0
            best_sector = -1
            best_split = 0.0
            best_direction = math.nan

            neighbor_z = [math.nan] * 8
            neighbor_index = [-1] * 8
            for i, (dr, dc) in enumerate(_NEIGHBORS):
                rr, cc = row + dr, col + dc
                if 0 <= rr < rows and 0 <= cc < cols:
                    target = rr * cols + cc
                    if flat_valid[target]:
                        neighbor_index[i] = target
                        neighbor_z[i] = flat_dem[target]
                        drop = z0 - neighbor_z[i]
                        if drop > 0.0:
                            slope = drop / distances[i]
                            if slope > best_slope:
                                best_slope = slope
                                best_sector = i
                                best_split = 0.0
                                best_direction = bearings[i]

            # Fit a plane over each adjacent triangular facet. Keep a plane
            # descent only when its bearing falls inside that facet's sector.
            for i in range(8):
                j = (i + 1) % 8
                if neighbor_index[i] < 0 or neighbor_index[j] < 0:
                    continue
                dr1, dc1 = _NEIGHBORS[i]
                dr2, dc2 = _NEIGHBORS[j]
                x1, y1 = dc1 * cell_size_x, -dr1 * cell_size_y
                x2, y2 = dc2 * cell_size_x, -dr2 * cell_size_y
                determinant = x1 * y2 - x2 * y1
                if determinant == 0.0:
                    continue
                dz1 = neighbor_z[i] - z0
                dz2 = neighbor_z[j] - z0
                gx = (dz1 * y2 - dz2 * y1) / determinant
                gy = (x1 * dz2 - x2 * dz1) / determinant
                down_x, down_y = -gx, -gy
                slope = math.hypot(down_x, down_y)
                if slope <= best_slope or slope <= 0.0:
                    continue

                angle = math.atan2(down_y, down_x) % (2.0 * math.pi)
                delta = (angle - bearings[i]) % (2.0 * math.pi)
                span = spans[i]
                if delta <= span + 1e-12:
                    best_slope = slope
                    best_sector = i
                    best_split = min(1.0, max(0.0, delta / span))
                    best_direction = angle

            if best_sector >= 0:
                sector[source] = best_sector
                split_second[source] = best_split
                direction[source] = best_direction
                first_target = neighbor_index[best_sector]
                second_target = neighbor_index[(best_sector + 1) % 8]
                if first_target >= 0 and best_split < 1.0:
                    inflow_count[first_target] += 1
                if best_split > 0.0 and second_target >= 0:
                    inflow_count[second_target] += 1

    # Kahn traversal avoids a global elevation sort and supports split flow.
    queue = np.empty(count, dtype=np.int64)
    tail = 0
    for cell in range(count):
        if flat_valid[cell] and inflow_count[cell] == 0:
            queue[tail] = cell
            tail += 1

    area = np.zeros(count, dtype=np.float64)
    area[flat_valid] = cell_size_x * cell_size_y
    head = 0
    processed = 0
    while head < tail:
        source = int(queue[head])
        head += 1
        processed += 1
        route_sector = int(sector[source])
        if route_sector == int(_NO_ROUTE):
            continue

        row, col = divmod(source, cols)
        first_weight = 1.0 - float(split_second[source])
        second_weight = float(split_second[source])
        for direction_index, weight in (
            (route_sector, first_weight),
            ((route_sector + 1) % 8, second_weight),
        ):
            if weight <= 0.0:
                continue
            dr, dc = _NEIGHBORS[direction_index]
            rr, cc = row + dr, col + dc
            if not (0 <= rr < rows and 0 <= cc < cols):
                continue
            target = rr * cols + cc
            if not flat_valid[target]:
                continue
            area[target] += area[source] * weight
            inflow_count[target] -= 1
            if inflow_count[target] == 0:
                queue[tail] = target
                tail += 1

    if processed != int(np.count_nonzero(flat_valid)):
        raise RuntimeError(
            "D-infinity receiver graph was not acyclic; "
            "check strict downhill routing and nodata handling"
        )

    terminal = flat_valid & (sector == _NO_ROUTE)
    return DInfinityResult(
        flow_direction=direction.reshape(rows, cols),
        contributing_area=area.reshape(rows, cols),
        terminal_mask=terminal.reshape(rows, cols),
        valid_mask=valid,
    )
