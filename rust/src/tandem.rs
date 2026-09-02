// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Mirror Core — tandem-mirror confinement kernels

//! Tandem-mirror confinement closed forms (Frank et al. 2025, eqs.
//! 3.2-3.7 and 4.3), operation-for-operation identical to
//! `scpn_mirror_core.physics.tandem`.

use crate::collisions::ion_scattering_time;
use crate::{NumericsError, ATOMIC_MASS_KG, ELEMENTARY_CHARGE_C, KEV_J, PI};
use scpn_reactor_kernels_native::numerics::transcendental::{exponential, natural_log};

/// Tandem confinement quantities (SI in the names).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct TandemConfinement {
    /// `phi_i`.
    pub ion_confining_potential_kev: f64,
    /// `phi_i / T_ic`.
    pub potential_ratio: f64,
    /// `G(R_mc)`.
    pub pastukhov_function: f64,
    /// `tau_ii` at `E_i = T_ic`.
    pub ion_scattering_time_s: f64,
    /// `tau_Past`.
    pub pastukhov_time_s: f64,
    /// `v_thic`.
    pub ion_thermal_speed_m_s: f64,
    /// `tau_f`.
    pub trapping_time_s: f64,
    /// `rho_ic`.
    pub ion_gyroradius_m: f64,
    /// `tau_rho`.
    pub radial_time_s: f64,
    /// `tau_c`.
    pub combined_time_s: f64,
    /// `R_m sin^2 theta - 1`.
    pub hole_denominator: f64,
    /// `E_h`; `None` when the denominator is not positive.
    pub ambipolar_hole_energy_kev: Option<f64>,
}

/// `G(x)` of eq. 3.5.
///
/// # Errors
/// Propagates the library's refusal of the logarithm.
pub fn pastukhov_function(mirror_ratio: f64) -> Result<f64, NumericsError> {
    let root = (1.0 + 1.0 / mirror_ratio).sqrt();
    Ok(root * natural_log((root + 1.0) / (root - 1.0))?)
}

/// Evaluate the tandem closed forms.
///
/// # Errors
/// Propagates the library's refusal of the logarithm or the exponential.
#[allow(clippy::too_many_arguments)]
pub fn tandem_confinement(
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
) -> Result<TandemConfinement, NumericsError> {
    let potential =
        electron_temperature_kev * natural_log(plug_density_per_m3 / central_density_per_m3)?;
    let ratio = potential / central_ion_temperature_kev;
    let function = pastukhov_function(effective_ratio)?;
    let scattering = ion_scattering_time(
        central_density_per_m3,
        central_ion_temperature_kev,
        ion_mass_amu,
        charge_number,
    );
    let half = central_ion_temperature_kev / (2.0 * potential);
    let growth = exponential(ratio)?;
    let pastukhov =
        ((PI.sqrt() / 2.0) * scattering * ratio * growth * function) / (1.0 + half - half * half);
    let ion_mass_kg = ion_mass_amu * ATOMIC_MASS_KG;
    let thermal_speed = (central_ion_temperature_kev * KEV_J / (2.0 * ion_mass_kg)).sqrt();
    let trapping = PI.sqrt() * effective_ratio * (central_cell_length_m / thermal_speed) * growth;
    let cyclotron = charge_number * ELEMENTARY_CHARGE_C * central_field_t / ion_mass_kg;
    let gyroradius = thermal_speed / cyclotron;
    let radial_ratio = plasma_radius_m / gyroradius;
    let radial = 0.25 * (radial_ratio * radial_ratio) * scattering;
    let combined = 1.0 / (1.0 / (pastukhov + trapping) + 1.0 / radial);
    let sine_squared = 1.0 - parallel_velocity_fraction * parallel_velocity_fraction;
    let denominator = effective_ratio * sine_squared - 1.0;
    let hole = if denominator > 0.0 {
        Some(plug_electron_potential_kev / denominator)
    } else {
        None
    };
    Ok(TandemConfinement {
        ion_confining_potential_kev: potential,
        potential_ratio: ratio,
        pastukhov_function: function,
        ion_scattering_time_s: scattering,
        pastukhov_time_s: pastukhov,
        ion_thermal_speed_m_s: thermal_speed,
        trapping_time_s: trapping,
        ion_gyroradius_m: gyroradius,
        radial_time_s: radial,
        combined_time_s: combined,
        hole_denominator: denominator,
        ambipolar_hole_energy_kev: hole,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn g_of_one_matches_the_closed_form() {
        let expected = 2.0_f64.sqrt() * natural_log(3.0 + 2.0 * 2.0_f64.sqrt()).unwrap();
        assert!((pastukhov_function(1.0).unwrap() - expected).abs() <= 1.0e-14);
    }

    #[test]
    fn combined_time_is_below_both_channels_and_the_hole_is_absent_at_low_ratio() {
        let t = tandem_confinement(
            20.0, 5.0e20, 1.0e20, 5.0, 10.0, 2.5, 1.0, 0.86, 10.0, 0.2, 30.0, 0.7,
        )
        .unwrap();
        assert!(t.combined_time_s < t.pastukhov_time_s + t.trapping_time_s);
        assert!(t.combined_time_s < t.radial_time_s);
        assert!(t.ambipolar_hole_energy_kev.is_some());
        let none = tandem_confinement(
            1.5, 5.0e20, 1.0e20, 5.0, 10.0, 2.5, 1.0, 0.86, 10.0, 0.2, 30.0, 0.7,
        )
        .unwrap();
        assert!(none.ambipolar_hole_energy_kev.is_none());
    }
}
