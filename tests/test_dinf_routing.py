"""Regression tests for the D-infinity reference router."""
import numpy as np
import pytest

from backend.services.dinf_routing import route_dinf


def test_single_cell_uses_physical_cell_area_and_is_terminal():
    result = route_dinf(np.array([[7.0]]), cell_size_x=2.0, cell_size_y=3.0)

    assert result.contributing_area[0, 0] == pytest.approx(6.0)
    assert result.terminal_mask[0, 0]
    assert np.isnan(result.flow_direction[0, 0])


def test_planar_surface_routes_along_steepest_facet_and_conserves_area():
    rows, cols = np.mgrid[0:5, 0:5]
    x, y = cols.astype(float), -rows.astype(float)
    elevation = -2.0 * x - 1.0 * y

    result = route_dinf(elevation)

    assert result.flow_direction[2, 2] == pytest.approx(np.arctan2(1.0, 2.0))
    terminal_area = result.contributing_area[result.terminal_mask].sum()
    assert terminal_area == pytest.approx(elevation.size)


def test_nodata_and_nonfinite_cells_do_not_receive_or_route_area():
    elevation = np.array(
        [[9.0, 8.0, 9999.0], [8.0, np.nan, 5.0], [7.0, 6.0, 4.0]]
    )

    result = route_dinf(elevation, cell_size_x=2.0, cell_size_y=3.0, nodata=9999.0)

    assert result.valid_mask.sum() == 7
    assert np.isnan(result.flow_direction[0, 2])
    assert np.isnan(result.flow_direction[1, 1])
    assert np.all(result.contributing_area[~result.valid_mask] == 0.0)
    assert result.contributing_area[result.terminal_mask].sum() == pytest.approx(42.0)


def test_rectangular_grid_uses_map_unit_area():
    result = route_dinf(np.ones((2, 2)), cell_size_x=4.0, cell_size_y=1.5)

    assert np.all(result.contributing_area == 6.0)
    assert result.terminal_mask.all()


@pytest.mark.parametrize(
    ("elevation", "kwargs"),
    [
        (np.array([1.0, 2.0]), {}),
        (np.empty((0, 1)), {}),
        (np.ones((2, 2)), {"cell_size_x": 0.0}),
        (np.ones((2, 2)), {"cell_size_y": float("inf")}),
        (np.ones((2, 2), dtype=complex), {}),
    ],
)
def test_rejects_invalid_inputs(elevation, kwargs):
    with pytest.raises(ValueError):
        route_dinf(elevation, **kwargs)


@pytest.mark.parametrize("seed", [7, 42, 2026])
def test_random_terrain_and_nodata_conserve_area(seed):
    rng = np.random.default_rng(seed)
    elevation = rng.normal(size=(12, 9))
    elevation[rng.random(elevation.shape) < 0.15] = np.nan

    result = route_dinf(elevation, cell_size_x=2.5, cell_size_y=1.25)

    valid_area = np.count_nonzero(result.valid_mask) * 2.5 * 1.25
    routed_area = result.contributing_area[result.terminal_mask].sum()
    assert routed_area == pytest.approx(valid_area, rel=1e-12, abs=1e-12)


def test_empty_valid_domain_returns_empty_masks_and_zero_area():
    result = route_dinf(np.array([[np.nan, np.inf]]))

    assert not result.valid_mask.any()
    assert not result.terminal_mask.any()
    assert not result.contributing_area.any()
    assert np.isnan(result.flow_direction).all()
