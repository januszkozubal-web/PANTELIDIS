"""
Parcia i odpory graniczne w ujęciu Pantelidisa (2019).

Wzory bez sejsmiki zgodne z zestawieniem „pinkbox” (ściana gładka).
Opcjonalnie: kh, kv oraz obciążenie naziomu (przeliczenie z → z_eff).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

DEG = np.pi / 180.0


@dataclass(frozen=True)
class SoilParams:
    gamma: float  # kN/m³
    c_prime: float  # kPa
    phi_deg: float  # °
    E: float = 50_000.0  # kPa (moduł Younga)
    nu: float = 0.30  # współczynnik Poissona
    c_m: float | None = None  # spójność resztkowa; domyślnie c'
    phi_m_deg: float | None = None  # nieużywane w uproszczonych wzorach K

    @property
    def phi(self) -> float:
        return self.phi_deg * DEG

    @property
    def cm(self) -> float:
        return self.c_prime if self.c_m is None else self.c_m


@dataclass(frozen=True)
class SeismicParams:
    kh: float = 0.0
    kv: float = 0.0

    @property
    def active(self) -> bool:
        return abs(self.kh) > 0.0 or abs(self.kv) > 0.0


def _trig(phi: float) -> tuple[float, float, float, float, float]:
    s = np.sin(phi)
    Ka = (1.0 - s) / (1.0 + s)
    Kp = (1.0 + s) / (1.0 - s)
    K0 = 1.0 - s
    t_minus = np.tan(np.pi / 4.0 - phi / 2.0)
    t_plus = np.tan(np.pi / 4.0 + phi / 2.0)
    return Ka, Kp, K0, t_minus, t_plus


def classic_coefficients(phi_deg: float) -> dict[str, float]:
    """Stałe Rankine/Jaky: Ka, Kp, K0 (bez spójności)."""
    Ka, Kp, K0, _, _ = _trig(phi_deg * DEG)
    return {"Ka": float(Ka), "Kp": float(Kp), "K0": float(K0)}


def z_effective_surcharge(
    z: float,
    gamma: float,
    q: float = 0.0,
    gamma_Q_over_gamma_G: float = 1.0,
    layers_above: Iterable[tuple[float, float]] | None = None,
) -> float:
    """
    Przeliczenie współrzędnej z przy obciążeniu naziomu / warstwach.

    Warstwa przypowierzchniowa: z1 = z + (q/γ1)*(γQ/γG)
    Warstwa poniżej h: z2 = z - h + (q/γ2)*(γQ/γG) + (γ1*h)/γ2
    `layers_above`: lista (h_i, γ_i) warstw powyżej bieżącej.
    """
    z_eff = float(z) + (q / gamma) * gamma_Q_over_gamma_G
    if layers_above:
        for h_i, g_i in layers_above:
            z_eff += (g_i * h_i) / gamma
            z_eff -= h_i
    return z_eff


def K_oe(soil: SoilParams, z: float, seismic: SeismicParams | None = None) -> float:
    """Współczynnik parcia spoczynkowego K_oe(z)."""
    seismic = seismic or SeismicParams()
    _, _, K0, t_minus, _ = _trig(soil.phi)
    kh, kv = seismic.kh, seismic.kv
    if abs(1.0 - kv) < 1e-12:
        raise ValueError("kv nie może wynosić 1")
    term_seis = 1.0 + (kh / (1.0 - kv)) * np.tan(soil.phi)
    cohes = (1.0 / (1.0 - kv)) * (2.0 * soil.cm / (soil.gamma * z)) * t_minus
    return float(K0 * term_seis - cohes)


def K_ae(soil: SoilParams, z: float, seismic: SeismicParams | None = None) -> float:
    """Współczynnik parcia aktywnego K_ae(z)."""
    seismic = seismic or SeismicParams()
    Ka, _, _, t_minus, _ = _trig(soil.phi)
    kh, kv = seismic.kh, seismic.kv
    if abs(1.0 - kv) < 1e-12:
        raise ValueError("kv nie może wynosić 1")
    term_seis = 1.0 + 2.0 * (kh / (1.0 - kv)) * np.tan(soil.phi)
    cohes = (1.0 / (1.0 - kv)) * (2.0 * soil.cm / (soil.gamma * z)) * t_minus
    return float(Ka * term_seis - cohes)


def K_pe(soil: SoilParams, z: float, seismic: SeismicParams | None = None) -> float:
    """Współczynnik odporu biernego K_pe(z)."""
    seismic = seismic or SeismicParams()
    _, Kp, _, _, t_plus = _trig(soil.phi)
    kh, kv = seismic.kh, seismic.kv
    if abs(1.0 - kv) < 1e-12:
        raise ValueError("kv nie może wynosić 1")
    term_seis = 1.0 - 2.0 * (kh / (1.0 - kv)) * np.tan(soil.phi)
    cohes = (1.0 / (1.0 - kv)) * (2.0 * soil.cm / (soil.gamma * z)) * t_plus
    return float(Kp * term_seis + cohes)


def sigma_o(soil: SoilParams, z: float, seismic: SeismicParams | None = None) -> float:
    """Naprężenie poziome spoczynkowe σ_o [kPa]."""
    seismic = seismic or SeismicParams()
    return float(K_oe(soil, z, seismic) * (1.0 - seismic.kv) * soil.gamma * z)


def sigma_a(soil: SoilParams, z: float, seismic: SeismicParams | None = None) -> float:
    """Naprężenie aktywne σ_a [kPa] (bez sejsmiki = wzór pinkbox)."""
    seismic = seismic or SeismicParams()
    if not seismic.active:
        Ka, _, _, t_minus, _ = _trig(soil.phi)
        return float(Ka * soil.gamma * z - 2.0 * soil.c_prime * t_minus)
    return float(K_ae(soil, z, seismic) * (1.0 - seismic.kv) * soil.gamma * z)


def sigma_p(soil: SoilParams, z: float, seismic: SeismicParams | None = None) -> float:
    """Naprężenie bierne σ_p [kPa] (bez sejsmiki = wzór pinkbox)."""
    seismic = seismic or SeismicParams()
    if not seismic.active:
        _, Kp, _, _, t_plus = _trig(soil.phi)
        return float(Kp * soil.gamma * z + 2.0 * soil.c_prime * t_plus)
    return float(K_pe(soil, z, seismic) * (1.0 - seismic.kv) * soil.gamma * z)


def _geom_smooth(H: float, z: float) -> float:
    """(H+z)^3 (H-z) / (H^2 z)"""
    if z <= 0 or z >= H:
        return np.nan
    return ((H + z) ** 3 * (H - z)) / (H**2 * z)


def delta_x_lim_smooth(
    soil: SoilParams,
    H: float,
    z: float,
    delta_K: float,
    seismic: SeismicParams | None = None,
) -> float:
    """
    Maksymalne przemieszczenie poziome [m] — ściana gładka.
    Δx = (π/4)(1-ν²)/E * geom * ΔK * (1-kv) * γ * z
    """
    seismic = seismic or SeismicParams()
    pref = (np.pi / 4.0) * (1.0 - soil.nu**2) / soil.E
    return float(pref * _geom_smooth(H, z) * delta_K * (1.0 - seismic.kv) * soil.gamma * z)


def delta_x_a_lim(
    soil: SoilParams,
    H: float,
    z: float,
    seismic: SeismicParams | None = None,
) -> float:
    """Δx_a;lim — przemieszczenie do stanu aktywnego."""
    dK = K_oe(soil, z, seismic) - K_ae(soil, z, seismic)
    return delta_x_lim_smooth(soil, H, z, dK, seismic)


def delta_x_p_lim(
    soil: SoilParams,
    H: float,
    z: float,
    seismic: SeismicParams | None = None,
) -> float:
    """Δx_p;lim — przemieszczenie do stanu biernego."""
    dK = K_pe(soil, z, seismic) - K_oe(soil, z, seismic)
    return delta_x_lim_smooth(soil, H, z, dK, seismic)


def E_a_bilinear(soil: SoilParams, H: float, z: float, seismic: SeismicParams | None = None) -> float:
    """Zastępczy moduł dwuliniowy obszaru parć [kPa/m] ≈ kPa / m."""
    dx = delta_x_a_lim(soil, H, z, seismic)
    if dx is None or not np.isfinite(dx) or abs(dx) < 1e-15:
        return np.nan
    return float(sigma_a(soil, z, seismic) / dx)


def E_p_bilinear(soil: SoilParams, H: float, z: float, seismic: SeismicParams | None = None) -> float:
    """Zastępczy moduł dwuliniowy obszaru odporów [kPa/m]."""
    dx = delta_x_p_lim(soil, H, z, seismic)
    if dx is None or not np.isfinite(dx) or abs(dx) < 1e-15:
        return np.nan
    return float(sigma_p(soil, z, seismic) / dx)


def wall_displacement_profile(
    depths: Iterable[float],
    H: float,
    mode: str,
    delta_ref: float,
) -> np.ndarray:
    """
    Profil przemieszczenia poziomego ściany sztywnej [m].

    mode:
      - "translation" — Δx(z) = delta_ref (stałe)
      - "rotation_bottom" — dno utwierdzone (z=H): Δx = delta_ref * (H-z)/H
        (delta_ref = przemieszczenie korony)
      - "rotation_top" — góra utwierdzona (z=0): Δx = delta_ref * z/H
        (delta_ref = przemieszczenie stopy)
      - "local_fraction" — Δx(z) = |delta_ref| * Δx_lim(z) w miejscu użycia
        (tu zwraca same wagi; lim mnoży caller)
    """
    zs = np.asarray(list(depths), dtype=float)
    if mode == "translation":
        return np.full_like(zs, float(delta_ref), dtype=float)
    if mode == "rotation_bottom":
        return float(delta_ref) * (H - zs) / H
    if mode == "rotation_top":
        return float(delta_ref) * zs / H
    if mode == "local_fraction":
        return np.full_like(zs, float(delta_ref), dtype=float)
    raise ValueError(f"Nieznany mode: {mode}")


def sigma_bilinear_mobilized(
    soil: SoilParams,
    H: float,
    z: float,
    delta_x: float,
    side: str = "active",
    seismic: SeismicParams | None = None,
) -> float:
    """
    Naprężenie w modelu dwuliniowym dla zadanego |Δx| [m].

    side="active": ściana od gruntu (parcie ↓ od σo do σa)
    side="passive": ściana w grunt (odpor ↑ od σo do σp)
    Ułamek mobilizacji ξ = min(|Δx|/Δx_lim, 1).
    """
    seismic = seismic or SeismicParams()
    s0 = sigma_o(soil, z, seismic)
    if side == "active":
        slim = sigma_a(soil, z, seismic)
        dlim = delta_x_a_lim(soil, H, z, seismic)
    elif side == "passive":
        slim = sigma_p(soil, z, seismic)
        dlim = delta_x_p_lim(soil, H, z, seismic)
    else:
        raise ValueError("side musi być 'active' albo 'passive'")
    if dlim is None or not np.isfinite(dlim) or dlim <= 0 or not np.isfinite(s0) or not np.isfinite(slim):
        return np.nan
    xi = min(abs(float(delta_x)) / dlim, 1.0)
    return float(s0 + xi * (slim - s0))


def mobilized_profile(
    soil: SoilParams,
    depths: Iterable[float],
    H: float,
    mode: str,
    delta_ref: float,
    side: str = "active",
    seismic: SeismicParams | None = None,
) -> dict[str, np.ndarray]:
    """Profil Δx(z), ξ(z) i σ(z) dla translacji / obrotu / ułamka lokalnego limitu."""
    zs = np.asarray(list(depths), dtype=float)
    if mode == "local_fraction":
        frac = abs(float(delta_ref))
        if side == "active":
            dlims = np.array([delta_x_a_lim(soil, H, z, seismic) for z in zs])
        else:
            dlims = np.array([delta_x_p_lim(soil, H, z, seismic) for z in zs])
        dx = frac * dlims
    else:
        dx = wall_displacement_profile(zs, H, mode, delta_ref)
        if side == "active":
            dlims = np.array([delta_x_a_lim(soil, H, z, seismic) for z in zs])
        else:
            dlims = np.array([delta_x_p_lim(soil, H, z, seismic) for z in zs])

    xi = np.array(
        [
            min(abs(d) / lim, 1.0) if (lim is not None and np.isfinite(lim) and lim > 0 and np.isfinite(d)) else np.nan
            for d, lim in zip(dx, dlims)
        ]
    )
    sig = np.array(
        [sigma_bilinear_mobilized(soil, H, z, d, side=side, seismic=seismic) for z, d in zip(zs, dx)]
    )
    return {"z": zs, "dx": dx, "dx_lim": dlims, "xi": xi, "sigma": sig}


def profile_table(
    soil: SoilParams,
    depths: Iterable[float],
    H: float,
    seismic: SeismicParams | None = None,
    tension_cutoff: bool = True,
) -> dict[str, np.ndarray]:
    """
    Tablica wyników vs głębokość.
    Przy tension_cutoff ujemne K/σ oznaczane jako NaN (jak „—” w przykładzie).
    """
    zs = np.asarray(list(depths), dtype=float)
    out = {
        "z": zs,
        "Koe": np.array([K_oe(soil, z, seismic) for z in zs]),
        "Kae": np.array([K_ae(soil, z, seismic) for z in zs]),
        "Kpe": np.array([K_pe(soil, z, seismic) for z in zs]),
        "sigma_o": np.array([sigma_o(soil, z, seismic) for z in zs]),
        "sigma_a": np.array([sigma_a(soil, z, seismic) for z in zs]),
        "sigma_p": np.array([sigma_p(soil, z, seismic) for z in zs]),
        "dx_a_lim": np.array([delta_x_a_lim(soil, H, z, seismic) for z in zs]),
        "dx_p_lim": np.array([delta_x_p_lim(soil, H, z, seismic) for z in zs]),
        "Ea_bil": np.array([E_a_bilinear(soil, H, z, seismic) for z in zs]),
        "Ep_bil": np.array([E_p_bilinear(soil, H, z, seismic) for z in zs]),
    }
    if tension_cutoff:
        for key in ("Koe", "Kae", "sigma_o", "sigma_a", "dx_a_lim", "Ea_bil"):
            out[key] = np.where(out[key] < 0, np.nan, out[key])
    return out


# Parametry przykładu z rozdziału (c'=30 kPa — zgodne z tabelami przy wzorach 2c')
EXAMPLE_SOIL = SoilParams(gamma=21.0, c_prime=30.0, phi_deg=17.5, E=50_000.0, nu=0.30)
EXAMPLE_DEPTHS = (1.0, 2.0, 3.0, 4.0, 5.0, 10.0)
EXAMPLE_H = 7.0  # nie podano w tekście; dobrane pod tabelę Δx przy E=50 MPa, ν=0.3
