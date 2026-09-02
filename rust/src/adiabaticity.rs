// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Mirror Core — fast-ion adiabaticity kernels

//! Fast-ion adiabaticity parameter (Endrizzi et al. 2023, section 3.6),
//! operation-for-operation identical to
//! `scpn_mirror_core.physics.adiabaticity`.

use crate::stability::ion_gyromotion;

/// `alpha` threshold of the disposition.
pub const ADIABATICITY_THRESHOLD: f64 = 10.0;

/// Adiabaticity quantities.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Adiabaticity {
    /// `f sqrt(2 E_i / m_i)`.
    pub parallel_speed_m_s: f64,
    /// `v_par / omega_ci`; `None` at zero fraction.
    pub parallel_gyroradius_m: Option<f64>,
    /// `L_B / rho_par`; `None` at zero fraction.
    pub alpha: Option<f64>,
    /// `alpha > 10`; `None` at zero fraction.
    pub adiabatic: Option<bool>,
}

/// Evaluate the parameter.
#[must_use]
pub fn adiabaticity(
    field_gradient_scale_length_m: f64,
    parallel_velocity_fraction: f64,
    ion_energy_kev: f64,
    ion_mass_amu: f64,
    charge_number: f64,
    field_t: f64,
) -> Adiabaticity {
    let (speed, frequency, _) =
        ion_gyromotion(ion_energy_kev, ion_mass_amu, charge_number, field_t);
    let parallel_speed = parallel_velocity_fraction * speed;
    if parallel_velocity_fraction == 0.0 {
        return Adiabaticity {
            parallel_speed_m_s: parallel_speed,
            parallel_gyroradius_m: None,
            alpha: None,
            adiabatic: None,
        };
    }
    let parallel_gyroradius = parallel_speed / frequency;
    let alpha = field_gradient_scale_length_m / parallel_gyroradius;
    Adiabaticity {
        parallel_speed_m_s: parallel_speed,
        parallel_gyroradius_m: Some(parallel_gyroradius),
        alpha: Some(alpha),
        adiabatic: Some(alpha > ADIABATICITY_THRESHOLD),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zero_fraction_is_not_applicable_and_alpha_scales_with_field_squared() {
        let none = adiabaticity(1.0, 0.0, 10.0, 2.0, 1.0, 1.0);
        assert!(none.alpha.is_none() && none.adiabatic.is_none());
        let low = adiabaticity(1.0, 0.5, 10.0, 2.0, 1.0, 1.0).alpha.unwrap();
        let high = adiabaticity(1.0, 0.5, 10.0, 2.0, 1.0, 2.0).alpha.unwrap();
        assert!((high / low - 2.0).abs() <= 1.0e-12);
    }
}
