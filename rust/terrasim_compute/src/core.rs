//! Fused, allocation-light reference kernel for terrain flux divergence.
//!
//! The kernel intentionally mirrors `backend.services.paper_model` so the
//! Python implementation remains the oracle and fallback.

#[allow(clippy::too_many_arguments)]
pub fn evaluate_flux_divergence(
    elevation: &[f64],
    valid: &[bool],
    rows: usize,
    cols: usize,
    cell_size_x: f64,
    cell_size_y: f64,
    alpha: f64,
    beta: f64,
    critical_slope_threshold: f64,
    d_xx: f64,
    d_xy: f64,
    d_yy: f64,
    cfl: f64,
) -> Result<(Vec<f64>, f64), String> {
    let count = rows
        .checked_mul(cols)
        .ok_or_else(|| "grid dimensions overflow addressable memory".to_string())?;
    if rows == 0 || cols == 0 || elevation.len() != count || valid.len() != count {
        return Err("elevation and validity mask must match a non-empty 2D grid".into());
    }
    if !cell_size_x.is_finite() || cell_size_x <= 0.0 {
        return Err("cell_size_x must be positive and finite".into());
    }
    if !cell_size_y.is_finite() || cell_size_y <= 0.0 {
        return Err("cell_size_y must be positive and finite".into());
    }
    if !alpha.is_finite() || alpha < 0.0 {
        return Err("alpha must be finite and non-negative".into());
    }
    if !beta.is_finite() || beta < 0.0 {
        return Err("beta must be finite and non-negative".into());
    }
    if !critical_slope_threshold.is_finite() || critical_slope_threshold < 0.0 {
        return Err("critical slope threshold must be finite and non-negative".into());
    }
    if !d_xx.is_finite() || !d_xy.is_finite() || !d_yy.is_finite() {
        return Err("diffusion tensor must be finite".into());
    }
    if d_xx <= 0.0 || d_xx * d_yy - d_xy * d_xy <= 0.0 {
        return Err("diffusion tensor must be positive-definite".into());
    }
    if !cfl.is_finite() || !(0.0 < cfl && cfl <= 1.0) {
        return Err("cfl must be finite and in (0, 1]".into());
    }
    if !valid.iter().any(|cell| *cell) {
        return Err("elevation grid contains no valid cells".into());
    }
    if elevation
        .iter()
        .zip(valid)
        .any(|(z, is_valid)| *is_valid && !z.is_finite())
    {
        return Err("valid elevation cells must be finite".into());
    }

    // Two flux buffers replace the many full-size intermediate arrays created
    // by the NumPy reference path. They are reused for the face calculation.
    let mut flux_x = vec![0.0; count];
    let mut flux_y = vec![0.0; count];
    let mut max_jac_xx: f64 = 0.0;
    let mut max_jac_yy: f64 = 0.0;
    let mut max_abs_jac_xy: f64 = 0.0;

    for index in 0..count {
        if !valid[index] {
            continue;
        }
        let dz_dx = gradient_x(elevation, valid, rows, cols, index, cell_size_x);
        // Raster row indices increase south; model y coordinates increase north.
        let dz_dy = gradient_y(elevation, valid, rows, cols, index, cell_size_y);
        let tensor_grad_x = d_xx * dz_dx + d_xy * dz_dy;
        let tensor_grad_y = d_xy * dz_dx + d_yy * dz_dy;
        let slope_measure = (dz_dx * tensor_grad_x + dz_dy * tensor_grad_y).max(0.0);
        let active = slope_measure > critical_slope_threshold;
        let excess = (slope_measure - critical_slope_threshold).max(0.0);
        let capacity = alpha * excess + beta;

        flux_x[index] = -capacity * tensor_grad_x;
        flux_y[index] = -capacity * tensor_grad_y;

        let active_alpha = if active { 2.0 * alpha } else { 0.0 };
        let jac_xx = capacity * d_xx + active_alpha * tensor_grad_x * tensor_grad_x;
        let jac_yy = capacity * d_yy + active_alpha * tensor_grad_y * tensor_grad_y;
        let jac_xy = capacity * d_xy + active_alpha * tensor_grad_x * tensor_grad_y;
        max_jac_xx = max_jac_xx.max(jac_xx);
        max_jac_yy = max_jac_yy.max(jac_yy);
        max_abs_jac_xy = max_abs_jac_xy.max(jac_xy.abs());
    }

    let rate_bound = 2.0
        * (max_jac_xx / cell_size_x.powi(2)
            + max_jac_yy / cell_size_y.powi(2)
            + max_abs_jac_xy / (cell_size_x * cell_size_y));
    if !rate_bound.is_finite() {
        return Err("terrain stability-rate bound is non-finite".into());
    }
    let stable_timestep = if rate_bound > 0.0 {
        cfl / rate_bound
    } else {
        f64::INFINITY
    };

    let mut divergence = vec![0.0; count];
    for row in 0..rows {
        for col in 0..cols {
            let index = row * cols + col;
            if !valid[index] {
                continue;
            }

            let left_face = if col > 0 && valid[index - 1] {
                0.5 * (flux_x[index - 1] + flux_x[index])
            } else {
                0.0
            };
            let right_face = if col + 1 < cols && valid[index + 1] {
                0.5 * (flux_x[index] + flux_x[index + 1])
            } else {
                0.0
            };
            let north_face = if row > 0 && valid[index - cols] {
                0.5 * (flux_y[index - cols] + flux_y[index])
            } else {
                0.0
            };
            let south_face = if row + 1 < rows && valid[index + cols] {
                0.5 * (flux_y[index] + flux_y[index + cols])
            } else {
                0.0
            };
            divergence[index] =
                (right_face - left_face) / cell_size_x + (south_face - north_face) / cell_size_y;
        }
    }
    if divergence
        .iter()
        .zip(valid)
        .any(|(value, is_valid)| *is_valid && !value.is_finite())
    {
        return Err("non-finite sediment-flux divergence".into());
    }
    Ok((divergence, stable_timestep))
}

fn gradient_x(
    elevation: &[f64],
    valid: &[bool],
    _rows: usize,
    cols: usize,
    index: usize,
    spacing: f64,
) -> f64 {
    let col = index % cols;
    let has_left = col > 0 && valid[index - 1];
    let has_right = col + 1 < cols && valid[index + 1];
    match (has_left, has_right) {
        (true, true) => (elevation[index + 1] - elevation[index - 1]) / (2.0 * spacing),
        (true, false) => (elevation[index] - elevation[index - 1]) / spacing,
        (false, true) => (elevation[index + 1] - elevation[index]) / spacing,
        (false, false) => 0.0,
    }
}

fn gradient_y(
    elevation: &[f64],
    valid: &[bool],
    rows: usize,
    cols: usize,
    index: usize,
    spacing: f64,
) -> f64 {
    let row = index / cols;
    let has_north = row > 0 && valid[index - cols];
    let has_south = row + 1 < rows && valid[index + cols];
    match (has_north, has_south) {
        (true, true) => (elevation[index - cols] - elevation[index + cols]) / (2.0 * spacing),
        (true, false) => (elevation[index - cols] - elevation[index]) / spacing,
        (false, true) => (elevation[index] - elevation[index + cols]) / spacing,
        (false, false) => 0.0,
    }
}

#[cfg(test)]
mod tests {
    use super::evaluate_flux_divergence;

    #[test]
    fn flat_grid_has_zero_divergence() {
        let elevation = vec![12.0; 12];
        let valid = vec![true; 12];
        let (divergence, stable) = evaluate_flux_divergence(
            &elevation, &valid, 3, 4, 30.0, 30.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.25,
        )
        .unwrap();
        assert!(divergence.iter().all(|value| *value == 0.0));
        assert!(stable.is_infinite());
    }

    #[test]
    fn invalid_cells_are_no_flux_holes() {
        let elevation = vec![0.0, 1.0, 2.0, 0.0, 99.0, 2.0, 0.0, 1.0, 2.0];
        let valid = vec![true, true, true, true, false, true, true, true, true];
        let (divergence, _) = evaluate_flux_divergence(
            &elevation, &valid, 3, 3, 1.0, 1.0, 0.1, 0.02, 0.0, 1.0, 0.0, 1.0, 0.2,
        )
        .unwrap();
        assert_eq!(divergence[4], 0.0);
        assert!((divergence.iter().sum::<f64>()).abs() < 1e-12);
    }

    #[test]
    fn rejects_shape_mismatch_and_non_positive_tensor() {
        assert!(evaluate_flux_divergence(
            &[0.0],
            &[true],
            2,
            2,
            1.0,
            1.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            1.0,
            0.2
        )
        .is_err());
        assert!(evaluate_flux_divergence(
            &[0.0],
            &[true],
            1,
            1,
            1.0,
            1.0,
            0.0,
            0.0,
            0.0,
            1.0,
            2.0,
            1.0,
            0.2
        )
        .is_err());
    }
}

