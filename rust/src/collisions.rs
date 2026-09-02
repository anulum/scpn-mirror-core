// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Mirror Core — collisional time-scale kernels

//! Collisional time scales (Endrizzi et al. 2023, eqs. 3.1-3.3),
//! operation-for-operation identical to
//! `scpn_mirror_core.physics.collisions`.

use crate::NumericsError;
use scpn_reactor_kernels_native::numerics::transcendental::power;

/// `1e-3` as the Python floor's literal.
pub const MILLISECOND_S: f64 = 1.0e-3;
/// `1e-6` as the Python floor's literal.
pub const MICROSECOND_S: f64 = 1.0e-6;
/// `1e20 m^-3`.
pub const DENSITY_UNIT_PER_M3: f64 = 1.0e20;

/// Collisional time scales (seconds).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct CollisionTimes {
    /// `n / 1e20`.
    pub density_unit: f64,
    /// `tau_s`.
    pub slowing_time_s: f64,
    /// `tau_ii`.
    pub ion_scattering_time_s: f64,
    /// `tau_ee`.
    pub electron_scattering_time_s: f64,
    /// `E_i / 40^(2/3)`.
    pub equal_time_electron_temperature_kev: f64,
}

/// `x sqrt(x)`.
#[must_use]
pub fn three_halves(x: f64) -> f64 {
    x * x.sqrt()
}

/// `tau_ii` of eq. 3.2 in seconds.
#[must_use]
pub fn ion_scattering_time(
    density_per_m3: f64,
    ion_energy_kev: f64,
    ion_mass_amu: f64,
    charge_number: f64,
) -> f64 {
    let unit = density_per_m3 / DENSITY_UNIT_PER_M3;
    (three_halves(ion_energy_kev) * ion_mass_amu / (8.0 * charge_number * charge_number)) / unit
        * MILLISECOND_S
}

/// Evaluate the three time scales.
///
/// # Errors
/// Propagates the library's refusal of the power kernel (unreachable for
/// the fixed argument, kept for parity of the error surface).
pub fn collision_times(
    density_per_m3: f64,
    electron_temperature_kev: f64,
    ion_energy_kev: f64,
    ion_mass_amu: f64,
    charge_number: f64,
) -> Result<CollisionTimes, NumericsError> {
    let unit = density_per_m3 / DENSITY_UNIT_PER_M3;
    let z_squared = charge_number * charge_number;
    let slowing = (5.0 * three_halves(electron_temperature_kev) * ion_mass_amu / z_squared) / unit
        * MILLISECOND_S;
    let ion = ion_scattering_time(density_per_m3, ion_energy_kev, ion_mass_amu, charge_number);
    let electron = (5.8 * three_halves(electron_temperature_kev)) / unit * MICROSECOND_S;
    let equal = ion_energy_kev / power(40.0, 2.0 / 3.0)?;
    Ok(CollisionTimes {
        density_unit: unit,
        slowing_time_s: slowing,
        ion_scattering_time_s: ion,
        electron_scattering_time_s: electron,
        equal_time_electron_temperature_kev: equal,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn slowing_equals_scattering_at_the_stated_temperature() {
        let c = collision_times(1.0e20, 1.0, 1.0, 1.0, 1.0).unwrap();
        let equal =
            collision_times(1.0e20, c.equal_time_electron_temperature_kev, 1.0, 1.0, 1.0).unwrap();
        let relative = (equal.slowing_time_s - equal.ion_scattering_time_s).abs()
            / equal.ion_scattering_time_s;
        assert!(relative <= 1.0e-14);
        assert_eq!(c.ion_scattering_time_s, 1.0 / 8.0 * MILLISECOND_S);
    }
}
