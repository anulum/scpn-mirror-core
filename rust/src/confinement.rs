// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Mirror Core — confinement scaling kernels

//! Classical and gas-dynamic confinement scalings (Endrizzi et al. 2023,
//! eqs. 3.4 and 3.5), operation-for-operation identical to
//! `scpn_mirror_core.physics.confinement`.

use crate::collisions::{three_halves, DENSITY_UNIT_PER_M3, MICROSECOND_S, MILLISECOND_S};
use crate::{NumericsError, ATOMIC_MASS_KG, KEV_J};
use scpn_reactor_kernels_native::numerics::transcendental::natural_log;

/// Both scalings (seconds); the regime disposition lives on the floor.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ConfinementScalings {
    /// `log10 R_m`.
    pub log10_mirror_ratio: f64,
    /// `tau_p` of eq. 3.4.
    pub classical_time_s: f64,
    /// `sqrt(T_e / m_i)`.
    pub sound_speed_m_s: f64,
    /// `R_m L_p / c_s`.
    pub gas_dynamic_time_s: f64,
    /// `5.2 R_m L_p T_e^(-1/2) us`.
    pub gas_dynamic_printed_time_s: f64,
}

/// `(log10 R_m, tau_p)` of eq. 3.4.
///
/// # Errors
/// Propagates the library's refusal of the logarithm.
pub fn classical_confinement_time(
    density_per_m3: f64,
    ion_energy_kev: f64,
    effective_ratio: f64,
) -> Result<(f64, f64), NumericsError> {
    let log10_ratio = natural_log(effective_ratio)? / natural_log(10.0)?;
    let unit = density_per_m3 / DENSITY_UNIT_PER_M3;
    let scaled = ion_energy_kev / 100.0;
    Ok((
        log10_ratio,
        (250.0 * three_halves(scaled) * log10_ratio) / unit * MILLISECOND_S,
    ))
}

/// `(c_s, tau_GDT dimensional, tau_GDT printed)` of eq. 3.5.
#[must_use]
pub fn gas_dynamic_confinement_time(
    effective_ratio: f64,
    plasma_half_length_m: f64,
    electron_temperature_kev: f64,
    ion_mass_amu: f64,
) -> (f64, f64, f64) {
    let ion_mass_kg = ion_mass_amu * ATOMIC_MASS_KG;
    let sound_speed = (electron_temperature_kev * KEV_J / ion_mass_kg).sqrt();
    let dimensional = effective_ratio * plasma_half_length_m / sound_speed;
    let printed = (5.2 * effective_ratio * plasma_half_length_m / electron_temperature_kev.sqrt())
        * MICROSECOND_S;
    (sound_speed, dimensional, printed)
}

/// Evaluate both scalings.
///
/// # Errors
/// Propagates the library's refusal of the logarithm.
pub fn confinement_scalings(
    effective_ratio: f64,
    plasma_half_length_m: f64,
    density_per_m3: f64,
    electron_temperature_kev: f64,
    ion_energy_kev: f64,
    ion_mass_amu: f64,
) -> Result<ConfinementScalings, NumericsError> {
    let (log10_ratio, classical) =
        classical_confinement_time(density_per_m3, ion_energy_kev, effective_ratio)?;
    let (sound_speed, dimensional, printed) = gas_dynamic_confinement_time(
        effective_ratio,
        plasma_half_length_m,
        electron_temperature_kev,
        ion_mass_amu,
    );
    Ok(ConfinementScalings {
        log10_mirror_ratio: log10_ratio,
        classical_time_s: classical,
        sound_speed_m_s: sound_speed,
        gas_dynamic_time_s: dimensional,
        gas_dynamic_printed_time_s: printed,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn beta_gain_is_one_half_at_ratio_ten() {
        let (_, t0) = classical_confinement_time(1.0e20, 100.0, 10.0).unwrap();
        let (_, t9) = classical_confinement_time(1.0e20, 100.0, 10.0 / 0.1_f64.sqrt()).unwrap();
        assert!((t9 / t0 - 1.5).abs() <= 1.0e-14);
    }

    #[test]
    fn printed_coefficient_within_three_percent() {
        let (_, dimensional, printed) = gas_dynamic_confinement_time(1.0, 1.0, 1.0, 2.5);
        assert!((dimensional / printed - 1.0).abs() <= 0.03);
    }
}
