"""Testy wzorów + zgodność z tabelami przykładu (c'=30 kPa)."""

from __future__ import annotations

import math

from pantelidis import (
    EXAMPLE_SOIL,
    SeismicParams,
    SoilParams,
    K_ae,
    K_oe,
    K_pe,
    classic_coefficients,
    sigma_a,
    sigma_o,
    sigma_p,
)


def test_classic_ka_kp_k0():
    c = classic_coefficients(17.5)
    assert abs(c["Ka"] - 0.538) < 5e-3
    assert abs(c["Kp"] - 1.86) < 5e-3
    assert abs(c["K0"] - 0.699) < 5e-3


def test_example_cohesion_is_30():
    assert EXAMPLE_SOIL.c_prime == 30.0


def test_sigma_equals_K_times_gamma_z_no_seismic():
    soil = EXAMPLE_SOIL
    for z in (4.0, 5.0, 10.0):
        assert abs(sigma_o(soil, z) - K_oe(soil, z) * soil.gamma * z) < 1e-9
        assert abs(sigma_a(soil, z) - K_ae(soil, z) * soil.gamma * z) < 1e-9
        assert abs(sigma_p(soil, z) - K_pe(soil, z) * soil.gamma * z) < 1e-9


def test_book_table_K_and_sigma():
    """Tabele z rozdziału — przy c'=30 kPa i wzorach 2c'."""
    soil = EXAMPLE_SOIL
    # Kpe na płytkich z; Koe/Kae od 4 m
    assert abs(K_pe(soil, 1.0) - 5.757) < 5e-3
    assert abs(K_pe(soil, 2.0) - 3.808) < 5e-3
    assert abs(K_pe(soil, 3.0) - 3.159) < 5e-3
    assert abs(K_oe(soil, 4.0) - 0.176) < 5e-3
    assert abs(K_ae(soil, 4.0) - 0.014) < 5e-3
    assert abs(K_pe(soil, 4.0) - 2.834) < 5e-3
    assert abs(K_oe(soil, 5.0) - 0.280) < 5e-3
    assert abs(K_ae(soil, 5.0) - 0.119) < 5e-3
    assert abs(K_pe(soil, 5.0) - 2.639) < 5e-3
    assert abs(K_oe(soil, 10.0) - 0.490) < 5e-3
    assert abs(K_ae(soil, 10.0) - 0.328) < 5e-3
    assert abs(K_pe(soil, 10.0) - 2.250) < 5e-3

    assert abs(sigma_p(soil, 1.0) - 121) < 1.0
    assert abs(sigma_p(soil, 2.0) - 160) < 1.0
    assert abs(sigma_p(soil, 3.0) - 199) < 1.0
    assert abs(sigma_o(soil, 4.0) - 15) < 1.0
    assert abs(sigma_a(soil, 4.0) - 1) < 1.0
    assert abs(sigma_p(soil, 4.0) - 238) < 1.0
    assert abs(sigma_o(soil, 5.0) - 29) < 1.0
    assert abs(sigma_a(soil, 5.0) - 12) < 1.0
    assert abs(sigma_p(soil, 5.0) - 277) < 1.0
    assert abs(sigma_o(soil, 10.0) - 103) < 1.0
    assert abs(sigma_a(soil, 10.0) - 69) < 1.0
    assert abs(sigma_p(soil, 10.0) - 472) < 1.0


def test_seismic_reduces_to_static():
    soil = EXAMPLE_SOIL
    z = 5.0
    zero = SeismicParams(0.0, 0.0)
    assert abs(K_oe(soil, z, zero) - K_oe(soil, z)) < 1e-12
    assert abs(K_ae(soil, z, zero) - K_ae(soil, z)) < 1e-12
    assert abs(K_pe(soil, z, zero) - K_pe(soil, z)) < 1e-12


def test_cohesionless_limits():
    soil = SoilParams(gamma=20.0, c_prime=0.0, phi_deg=30.0)
    z = 5.0
    Ka = (1 - math.sin(math.radians(30))) / (1 + math.sin(math.radians(30)))
    Kp = 1.0 / Ka
    K0 = 1 - math.sin(math.radians(30))
    assert abs(K_ae(soil, z) - Ka) < 1e-12
    assert abs(K_pe(soil, z) - Kp) < 1e-12
    assert abs(K_oe(soil, z) - K0) < 1e-12


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
