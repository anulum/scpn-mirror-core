// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Mirror Core — FLR interchange criterion kernels

//! FLR interchange criterion (Endrizzi et al. 2023, eq. 3.7),
//! operation-for-operation identical to
//! `scpn_mirror_core.physics.stability`.

use crate::{ATOMIC_MASS_KG, ELEMENTARY_CHARGE_C, KEV_J};

/// Mode-number threshold of the disposition.
pub const FLR_MODE_THRESHOLD: f64 = 2.0;

/// FLR criterion quantities.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct FlrCriterion {
    /// `sqrt(2 E_i / m_i)`.
    pub ion_speed_m_s: f64,
    /// `Z e B_0 / m_i`.
    pub cyclotron_frequency_rad_s: f64,
    /// `v / omega_ci`.
    pub ion_gyroradius_m: f64,
    /// `2 a^2 / (L_p rho_i)`.
    pub critical_mode_number: f64,
    /// `critical < 2`.
    pub m2_stabilised: bool,
}

/// `(v, omega_ci, rho_i)`.
#[must_use]
pub fn ion_gyromotion(
    ion_energy_kev: f64,
    ion_mass_amu: f64,
    charge_number: f64,
    field_t: f64,
) -> (f64, f64, f64) {
    let ion_mass_kg = ion_mass_amu * ATOMIC_MASS_KG;
    let speed = (2.0 * ion_energy_kev * KEV_J / ion_mass_kg).sqrt();
    let frequency = charge_number * ELEMENTARY_CHARGE_C * field_t / ion_mass_kg;
    (speed, frequency, speed / frequency)
}

/// `2 a^2 / (L_p rho_i)`.
#[must_use]
pub fn critical_mode_number(
    plasma_radius_m: f64,
    plasma_half_length_m: f64,
    ion_gyroradius_m: f64,
) -> f64 {
    2.0 * plasma_radius_m * plasma_radius_m / (plasma_half_length_m * ion_gyroradius_m)
}

/// Evaluate the criterion.
#[must_use]
pub fn flr_criterion(
    plasma_radius_m: f64,
    plasma_half_length_m: f64,
    ion_energy_kev: f64,
    ion_mass_amu: f64,
    charge_number: f64,
    field_t: f64,
) -> FlrCriterion {
    let (speed, frequency, gyroradius) =
        ion_gyromotion(ion_energy_kev, ion_mass_amu, charge_number, field_t);
    let critical = critical_mode_number(plasma_radius_m, plasma_half_length_m, gyroradius);
    FlrCriterion {
        ion_speed_m_s: speed,
        cyclotron_frequency_rad_s: frequency,
        ion_gyroradius_m: gyroradius,
        critical_mode_number: critical,
        m2_stabilised: critical < FLR_MODE_THRESHOLD,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn worked_case_gives_zero_point_eight() {
        assert!((critical_mode_number(0.1, 1.0, 0.025) - 0.8).abs() <= 1.0e-15);
    }
}
