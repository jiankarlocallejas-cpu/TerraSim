//! Optional PyO3 bindings for the pure Rust terrain kernel.

mod core;

#[cfg(feature = "python-extension")]
use numpy::ndarray::Array2;
#[cfg(feature = "python-extension")]
use numpy::{PyArray2, PyReadonlyArray2};
#[cfg(feature = "python-extension")]
use pyo3::exceptions::PyValueError;
#[cfg(feature = "python-extension")]
use pyo3::prelude::*;
#[cfg(feature = "python-extension")]
use pyo3::types::PyModule;

#[cfg(feature = "python-extension")]
/// Evaluate sediment-flux divergence and the matching conservative timestep bound.
///
/// Inputs must be C-contiguous float64/bool NumPy arrays. The input data is copied
/// before releasing the GIL so another Python thread cannot mutate it mid-kernel.
#[cfg(feature = "python-extension")]
#[allow(clippy::too_many_arguments)]
#[pyfunction]
#[pyo3(signature = (
    elevation,
    valid_mask,
    cell_size_x,
    cell_size_y,
    alpha,
    beta,
    critical_slope_threshold,
    d_xx,
    d_xy,
    d_yy,
    cfl
))]
fn evaluate_flux_divergence<'py>(
    py: Python<'py>,
    elevation: PyReadonlyArray2<'py, f64>,
    valid_mask: PyReadonlyArray2<'py, bool>,
    cell_size_x: f64,
    cell_size_y: f64,
    alpha: f64,
    beta: f64,
    critical_slope_threshold: f64,
    d_xx: f64,
    d_xy: f64,
    d_yy: f64,
    cfl: f64,
) -> PyResult<(Bound<'py, PyArray2<f64>>, f64)> {
    let elevation_view = elevation.as_array();
    let valid_view = valid_mask.as_array();
    if elevation_view.raw_dim() != valid_view.raw_dim() {
        return Err(PyValueError::new_err(
            "elevation and validity mask must have the same 2D shape",
        ));
    }
    let (rows, cols) = (elevation_view.nrows(), elevation_view.ncols());
    let elevation_values = elevation
        .as_slice()
        .map_err(|_| PyValueError::new_err("elevation must be C-contiguous"))?
        .to_vec();
    let valid_values = valid_mask
        .as_slice()
        .map_err(|_| PyValueError::new_err("valid_mask must be C-contiguous"))?
        .to_vec();
    drop(elevation_view);
    drop(valid_view);
    drop(elevation);
    drop(valid_mask);

    let evaluated = py.detach(move || {
        core::evaluate_flux_divergence(
            &elevation_values,
            &valid_values,
            rows,
            cols,
            cell_size_x,
            cell_size_y,
            alpha,
            beta,
            critical_slope_threshold,
            d_xx,
            d_xy,
            d_yy,
            cfl,
        )
    });
    let (divergence, stable_timestep) = evaluated.map_err(PyValueError::new_err)?;
    let array = Array2::from_shape_vec((rows, cols), divergence)
        .map_err(|error| PyValueError::new_err(error.to_string()))?;
    Ok((PyArray2::from_owned_array(py, array), stable_timestep))
}

#[cfg(feature = "python-extension")]
#[pymodule]
fn terrasim_compute(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(evaluate_flux_divergence, module)?)?;
    Ok(())
}

