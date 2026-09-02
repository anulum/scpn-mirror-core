// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Mirror Core — native level-0 physics kernels

//! Native level-0 device-physics kernels of SCPN Mirror Core.
//!
//! Every function mirrors one closed-form evaluation of the pure-Python
//! floor in `scpn_mirror_core.physics` with the identical operation
//! order, so the IEEE-754 double results agree bit for bit. The kernels
//! use only `+`, `-`, `*`, `/` and `sqrt` (all correctly rounded) plus the
//! vendored logarithm, exponential and power of the shared kernel library
//! crate (`scpn-reactor-kernels-rs`, pinned by commit in `Cargo.toml` and
//! in the manifest), which the Python floor evaluates through the same
//! library. Nothing here solves an equation and no value describes a real
//! machine; the design records are ADR 0005 and ADR 0006 of the
//! repository.

pub mod adiabaticity;
pub mod collisions;
pub mod confinement;
pub mod mirror;
pub mod stability;
pub mod tandem;

pub use scpn_reactor_kernels_native::numerics::transcendental::NumericsError;

/// Elementary charge in coulombs (exact SI 2019 value).
pub const ELEMENTARY_CHARGE_C: f64 = 1.602_176_634e-19;
/// Atomic mass constant in kilograms (CODATA 2018).
pub const ATOMIC_MASS_KG: f64 = 1.660_539_066_60e-27;
/// One kilo-electronvolt in joules, evaluated as the Python floor does.
pub const KEV_J: f64 = ELEMENTARY_CHARGE_C * 1.0e3;
/// `pi` as the Python floor's `math.pi`.
pub const PI: f64 = std::f64::consts::PI;

#[cfg(feature = "python")]
mod python {
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;

    fn numerics(err: crate::NumericsError) -> PyErr {
        PyValueError::new_err(err.to_string())
    }

    /// Diamagnetic mirror ratio, see `crate::mirror::effective_ratio`.
    #[pyfunction]
    fn effective_ratio(vacuum_ratio: f64, midplane_beta: f64) -> f64 {
        crate::mirror::effective_ratio(vacuum_ratio, midplane_beta)
    }

    /// Loss boundary tuple, see `crate::mirror::loss_boundary`.
    #[pyfunction]
    fn loss_boundary(
        effective_ratio: f64,
        charge_number: f64,
        energy_kev: f64,
        potential_drop_kev: f64,
    ) -> (f64, f64, f64, bool, bool) {
        let b = crate::mirror::loss_boundary(
            effective_ratio,
            charge_number,
            energy_kev,
            potential_drop_kev,
        );
        (
            b.potential_factor,
            b.sine_squared,
            b.isotropic_fraction,
            b.fully_confined,
            b.no_trapped_region,
        )
    }

    /// Collision times tuple, see `crate::collisions::collision_times`.
    #[pyfunction]
    fn collision_times(
        density_per_m3: f64,
        electron_temperature_kev: f64,
        ion_energy_kev: f64,
        ion_mass_amu: f64,
        charge_number: f64,
    ) -> PyResult<(f64, f64, f64, f64, f64)> {
        let c = crate::collisions::collision_times(
            density_per_m3,
            electron_temperature_kev,
            ion_energy_kev,
            ion_mass_amu,
            charge_number,
        )
        .map_err(numerics)?;
        Ok((
            c.density_unit,
            c.slowing_time_s,
            c.ion_scattering_time_s,
            c.electron_scattering_time_s,
            c.equal_time_electron_temperature_kev,
        ))
    }

    /// Confinement scalings tuple, see `crate::confinement::confinement_scalings`.
    #[pyfunction]
    fn confinement_scalings(
        effective_ratio: f64,
        plasma_half_length_m: f64,
        density_per_m3: f64,
        electron_temperature_kev: f64,
        ion_energy_kev: f64,
        ion_mass_amu: f64,
    ) -> PyResult<(f64, f64, f64, f64, f64)> {
        let s = crate::confinement::confinement_scalings(
            effective_ratio,
            plasma_half_length_m,
            density_per_m3,
            electron_temperature_kev,
            ion_energy_kev,
            ion_mass_amu,
        )
        .map_err(numerics)?;
        Ok((
            s.log10_mirror_ratio,
            s.classical_time_s,
            s.sound_speed_m_s,
            s.gas_dynamic_time_s,
            s.gas_dynamic_printed_time_s,
        ))
    }

    /// FLR criterion tuple, see `crate::stability::flr_criterion`.
    #[pyfunction]
    fn flr_criterion(
        plasma_radius_m: f64,
        plasma_half_length_m: f64,
        ion_energy_kev: f64,
        ion_mass_amu: f64,
        charge_number: f64,
        field_t: f64,
    ) -> (f64, f64, f64, f64, bool) {
        let f = crate::stability::flr_criterion(
            plasma_radius_m,
            plasma_half_length_m,
            ion_energy_kev,
            ion_mass_amu,
            charge_number,
            field_t,
        );
        (
            f.ion_speed_m_s,
            f.cyclotron_frequency_rad_s,
            f.ion_gyroradius_m,
            f.critical_mode_number,
            f.m2_stabilised,
        )
    }

    /// Adiabaticity tuple, see `crate::adiabaticity::adiabaticity`.
    #[pyfunction]
    fn adiabaticity(
        field_gradient_scale_length_m: f64,
        parallel_velocity_fraction: f64,
        ion_energy_kev: f64,
        ion_mass_amu: f64,
        charge_number: f64,
        field_t: f64,
    ) -> (f64, Option<f64>, Option<f64>, Option<bool>) {
        let a = crate::adiabaticity::adiabaticity(
            field_gradient_scale_length_m,
            parallel_velocity_fraction,
            ion_energy_kev,
            ion_mass_amu,
            charge_number,
            field_t,
        );
        (
            a.parallel_speed_m_s,
            a.parallel_gyroradius_m,
            a.alpha,
            a.adiabatic,
        )
    }

    /// Tandem confinement tuple, see `crate::tandem::tandem_confinement`.
    #[pyfunction]
    #[allow(clippy::too_many_arguments, clippy::type_complexity)]
    fn tandem_confinement(
        effective_ratio: f64,
        plug_density_per_m3: f64,
        central_density_per_m3: f64,
        electron_temperature_kev: f64,
        central_ion_temperature_kev: f64,
        ion_mass_amu: f64,
        charge_number: f64,
        central_field_t: f64,
        central_cell_length_m: f64,
        plasma_radius_m: f64,
        plug_electron_potential_kev: f64,
        parallel_velocity_fraction: f64,
    ) -> PyResult<(
        f64,
        f64,
        f64,
        f64,
        f64,
        f64,
        f64,
        f64,
        f64,
        f64,
        f64,
        Option<f64>,
    )> {
        let t = crate::tandem::tandem_confinement(
            effective_ratio,
            plug_density_per_m3,
            central_density_per_m3,
            electron_temperature_kev,
            central_ion_temperature_kev,
            ion_mass_amu,
            charge_number,
            central_field_t,
            central_cell_length_m,
            plasma_radius_m,
            plug_electron_potential_kev,
            parallel_velocity_fraction,
        )
        .map_err(numerics)?;
        Ok((
            t.ion_confining_potential_kev,
            t.potential_ratio,
            t.pastukhov_function,
            t.ion_scattering_time_s,
            t.pastukhov_time_s,
            t.ion_thermal_speed_m_s,
            t.trapping_time_s,
            t.ion_gyroradius_m,
            t.radial_time_s,
            t.combined_time_s,
            t.hole_denominator,
            t.ambipolar_hole_energy_kev,
        ))
    }

    /// Python module `scpn_mirror_native`.
    #[pymodule]
    fn scpn_mirror_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(effective_ratio, m)?)?;
        m.add_function(wrap_pyfunction!(loss_boundary, m)?)?;
        m.add_function(wrap_pyfunction!(collision_times, m)?)?;
        m.add_function(wrap_pyfunction!(confinement_scalings, m)?)?;
        m.add_function(wrap_pyfunction!(flr_criterion, m)?)?;
        m.add_function(wrap_pyfunction!(adiabaticity, m)?)?;
        m.add_function(wrap_pyfunction!(tandem_confinement, m)?)?;
        Ok(())
    }
}
