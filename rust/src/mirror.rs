// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Mirror Core — mirror ratio and loss boundary kernels

//! Diamagnetic mirror ratio (Endrizzi et al. 2023, eq. 3.6) and the
//! potential-modified loss boundary (Frank et al. 2025, eqs. 2.3-2.5 in
//! the form derived from the invariants), operation-for-operation
//! identical to `scpn_mirror_core.physics.mirror`.

/// Loss boundary of one species at one energy.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct LossBoundary {
    /// `1 + q Delta phi / E`.
    pub potential_factor: f64,
    /// `sin^2 theta` of the boundary.
    pub sine_squared: f64,
    /// Fraction of an isotropic distribution inside the cone.
    pub isotropic_fraction: f64,
    /// Confined at every pitch.
    pub fully_confined: bool,
    /// No trapped region.
    pub no_trapped_region: bool,
}

/// `R_vac / sqrt(1 - beta)`.
///
/// Inputs are validated by the Python floor (`0 <= beta < 1`); the kernel
/// assumes them.
#[must_use]
pub fn effective_ratio(vacuum_ratio: f64, midplane_beta: f64) -> f64 {
    vacuum_ratio / (1.0 - midplane_beta).sqrt()
}

/// Evaluate the loss boundary.
#[must_use]
pub fn loss_boundary(
    effective_ratio: f64,
    charge_number: f64,
    energy_kev: f64,
    potential_drop_kev: f64,
) -> LossBoundary {
    let factor = 1.0 + charge_number * potential_drop_kev / energy_kev;
    if factor <= 0.0 {
        return LossBoundary {
            potential_factor: factor,
            sine_squared: 0.0,
            isotropic_fraction: 0.0,
            fully_confined: true,
            no_trapped_region: false,
        };
    }
    let sine_squared = factor / effective_ratio;
    if sine_squared >= 1.0 {
        return LossBoundary {
            potential_factor: factor,
            sine_squared,
            isotropic_fraction: 1.0,
            fully_confined: false,
            no_trapped_region: true,
        };
    }
    LossBoundary {
        potential_factor: factor,
        sine_squared,
        isotropic_fraction: 1.0 - (1.0 - sine_squared).sqrt(),
        fully_confined: false,
        no_trapped_region: false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zero_potential_is_the_standard_cone() {
        let b = loss_boundary(10.0, 1.0, 5.0, 0.0);
        assert_eq!(b.sine_squared, 0.1);
        assert!(!b.fully_confined && !b.no_trapped_region);
        assert_eq!(effective_ratio(10.0, 0.0), 10.0);
    }

    #[test]
    fn electrons_below_the_drop_are_confined() {
        let b = loss_boundary(10.0, -1.0, 1.0, 5.0);
        assert!(b.fully_confined);
        let c = loss_boundary(1.5, 1.0, 1.0, 5.0);
        assert!(c.no_trapped_region);
    }
}
