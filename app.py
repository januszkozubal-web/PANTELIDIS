"""
Streamlit — limiting earth pressures (Pantelidis 2019), PL/EN UI.

    streamlit run app.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from i18n import t
from pantelidis import (
    EXAMPLE_DEPTHS,
    EXAMPLE_H,
    EXAMPLE_SOIL,
    SeismicParams,
    SoilParams,
    classic_coefficients,
    mobilized_profile,
    profile_table,
    z_effective_surcharge,
)
from sketch import situation_svg

REF_PANTELIDIS = (
    "Pantelidis, L. (2019). The Generalized Coefficients of Earth Pressure: "
    "A Unified Approach. *Applied Sciences*, 9(24), 5291. "
    "[doi:10.3390/app9245291](https://doi.org/10.3390/app9245291)"
)
REF_BOOK = (
    "Kozubal, J. W., Wyjadłowski, M. (2025). *Poradnik geotechniki*. "
    "Wrocław: Dolnośląskie Wydawnictwo Edukacyjne. ISBN 978-83-7125-308-9."
)

st.set_page_config(
    page_title="Pantelidis / Parcia",
    page_icon="🧱",
    layout="wide",
)

with st.sidebar:
    lang_label = st.radio(
        "Language / Język",
        ["English", "Polski"],
        index=0,
        horizontal=True,
    )
    lang = "en" if lang_label == "English" else "pl"

    st.header(t(lang, "soil_params"))
    use_example = st.checkbox(t(lang, "load_example"), value=True)

    if use_example:
        gamma = EXAMPLE_SOIL.gamma
        c_prime = EXAMPLE_SOIL.c_prime
        phi_deg = EXAMPLE_SOIL.phi_deg
        E = EXAMPLE_SOIL.E
        nu = EXAMPLE_SOIL.nu
        H = EXAMPLE_H
        st.info(
            f"γ={gamma} kN/m³, c′={c_prime} kPa, φ′={phi_deg}°, "
            f"E={E/1000:.0f} MPa, ν={nu}, H={H} m"
        )
    else:
        gamma = st.number_input("γ [kN/m³]", 10.0, 28.0, 21.0, 0.1)
        c_prime = st.number_input("c′ [kPa]", 0.0, 200.0, 30.0, 0.5)
        phi_deg = st.number_input("φ′ [°]", 0.0, 45.0, 17.5, 0.1)
        E = st.number_input("E [kPa]", 1_000.0, 500_000.0, 50_000.0, 1_000.0)
        nu = st.number_input("ν [-]", 0.05, 0.49, 0.30, 0.01)
        H = st.number_input(t(lang, "wall_height"), 1.0, 50.0, 7.0, 0.1)

    st.header(t(lang, "seismic"))
    use_seis = st.checkbox(t(lang, "use_seis"), value=False)
    kh = st.number_input("kh", 0.0, 0.5, 0.0, 0.01, disabled=not use_seis)
    kv = st.number_input("kv", -0.5, 0.5, 0.0, 0.01, disabled=not use_seis)

    st.header(t(lang, "surcharge"))
    q = st.number_input("q [kPa]", 0.0, 200.0, 0.0, 1.0)
    gQgG = st.number_input("γQ / γG", 0.5, 1.5, 1.0, 0.05)

    st.header(t(lang, "depth_grid"))
    z_max = st.number_input("z max [m]", 1.0, min(H - 0.05, 40.0), min(H - 0.05, 10.0), 0.5)
    n_pts = st.slider(t(lang, "n_pts"), 5, 80, 20)
    tension_cutoff = st.checkbox(t(lang, "tension_cutoff"), value=True)

    st.header(t(lang, "intermediate"))
    show_mob = st.checkbox(t(lang, "show_mob"), value=True)
    side_opts = [t(lang, "side_active"), t(lang, "side_passive")]
    side_i = st.selectbox(
        t(lang, "side"),
        options=[0, 1],
        format_func=lambda i: side_opts[i],
        key="side_i",
    )
    kin_opts = [
        t(lang, "kin_frac"),
        t(lang, "kin_trans"),
        t(lang, "kin_rot_bot"),
        t(lang, "kin_rot_top"),
    ]
    kin_idx = st.selectbox(
        t(lang, "kinematics"),
        options=[0, 1, 2, 3],
        format_func=lambda i: kin_opts[i],
        key="kin_i",
    )
    if kin_idx == 0:
        delta_ui = st.slider(t(lang, "frac_slider"), 0.0, 1.0, 0.5, 0.05)
        kin_mode = "local_fraction"
        delta_ref = delta_ui
    elif kin_idx == 1:
        delta_ui = st.number_input("Δx [mm]", 0.0, 500.0, 10.0, 0.5)
        kin_mode = "translation"
        delta_ref = delta_ui / 1000.0
    elif kin_idx == 2:
        delta_ui = st.number_input(t(lang, "dx_crown"), 0.0, 500.0, 20.0, 0.5)
        kin_mode = "rotation_bottom"
        delta_ref = delta_ui / 1000.0
    else:
        delta_ui = st.number_input(t(lang, "dx_toe"), 0.0, 500.0, 20.0, 0.5)
        kin_mode = "rotation_top"
        delta_ref = delta_ui / 1000.0
    side = "active" if side_i == 0 else "passive"

st.title(t(lang, "title"))

soil = SoilParams(gamma=gamma, c_prime=c_prime, phi_deg=phi_deg, E=E, nu=nu)
seismic = SeismicParams(kh=kh if use_seis else 0.0, kv=kv if use_seis else 0.0)

if use_example:
    depths = list(EXAMPLE_DEPTHS)
else:
    depths = list(np.linspace(max(0.25, z_max / n_pts), z_max, n_pts))

if q > 0:
    depths_calc = [z_effective_surcharge(z, gamma, q=q, gamma_Q_over_gamma_G=gQgG) for z in depths]
else:
    depths_calc = depths

col_sk, col_lit = st.columns([1.35, 1.0])
with col_sk:
    st.subheader(t(lang, "sketch"))
    components.html(
        situation_svg(mode=kin_mode, side=side, lang=lang),
        height=380,
        scrolling=False,
    )
with col_lit:
    st.subheader(t(lang, "literature"))
    st.markdown(f"1. {REF_BOOK}")
    st.markdown(f"2. {REF_PANTELIDIS}")
    st.caption(t(lang, "lit_caption"))

classic = classic_coefficients(phi_deg)
c1, c2, c3 = st.columns(3)
c1.metric("Ka (Rankine)", f"{classic['Ka']:.3f}")
c2.metric("Kp (Rankine)", f"{classic['Kp']:.3f}")
c3.metric("K₀ (Jaky)", f"{classic['K0']:.3f}")

tab = profile_table(
    soil,
    depths_calc,
    H=H,
    seismic=seismic,
    tension_cutoff=tension_cutoff,
)

df = pd.DataFrame(
    {
        "z [m]": depths,
        "z_eff [m]": depths_calc,
        "Koe": tab["Koe"],
        "Kae": tab["Kae"],
        "Kpe": tab["Kpe"],
        "σo [kPa]": tab["sigma_o"],
        "σa [kPa]": tab["sigma_a"],
        "σp [kPa]": tab["sigma_p"],
        "Δxa,lim [mm]": tab["dx_a_lim"] * 1000.0,
        "Δxp,lim [mm]": tab["dx_p_lim"] * 1000.0,
        "Ea,bil [kPa/m]": tab["Ea_bil"],
        "Ep,bil [kPa/m]": tab["Ep_bil"],
    }
)

if q == 0:
    df = df.drop(columns=["z_eff [m]"])

st.subheader(t(lang, "results"))
st.dataframe(
    df.style.format(
        {
            "z [m]": "{:.2f}",
            "z_eff [m]": "{:.2f}",
            "Koe": "{:.3f}",
            "Kae": "{:.3f}",
            "Kpe": "{:.3f}",
            "σo [kPa]": "{:.1f}",
            "σa [kPa]": "{:.1f}",
            "σp [kPa]": "{:.1f}",
            "Δxa,lim [mm]": "{:.2f}",
            "Δxp,lim [mm]": "{:.2f}",
            "Ea,bil [kPa/m]": "{:.0f}",
            "Ep,bil [kPa/m]": "{:.0f}",
        },
        na_rep="—",
    ),
    use_container_width=True,
    hide_index=True,
)


def _line_chart(df_long: pd.DataFrame, y_title: str, height: int = 360):
    data = df_long.dropna(subset=["value"])
    if data.empty:
        st.warning(t(lang, "chart_empty"))
        return
    fig = px.line(
        data,
        x="value",
        y="z",
        color="seria",
        markers=True,
        labels={"value": y_title, "z": "z [m]", "seria": ""},
    )
    fig.update_yaxes(autorange="reversed", title="z [m]")
    fig.update_xaxes(title=y_title)
    fig.update_layout(
        height=height,
        margin=dict(l=40, r=20, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def _melt_series(z_vals, series_map: dict[str, np.ndarray]) -> pd.DataFrame:
    frames = []
    for name, values in series_map.items():
        frames.append(pd.DataFrame({"z": z_vals, "seria": name, "value": values}))
    return pd.concat(frames, ignore_index=True)


g1, g2 = st.columns(2)
with g1:
    st.markdown(f"**{t(lang, 'K_title')}**")
    _line_chart(
        _melt_series(depths, {"Koe": tab["Koe"], "Kae": tab["Kae"], "Kpe": tab["Kpe"]}),
        "K [-]",
    )
with g2:
    st.markdown(f"**{t(lang, 'sigma_title')}**")
    _line_chart(
        _melt_series(
            depths,
            {"σo": tab["sigma_o"], "σa": tab["sigma_a"], "σp": tab["sigma_p"]},
        ),
        "σ [kPa]",
    )

st.markdown(f"**{t(lang, 'dx_title')}**")
_line_chart(
    _melt_series(
        depths,
        {
            "Δxa,lim": tab["dx_a_lim"] * 1000.0,
            "Δxp,lim": tab["dx_p_lim"] * 1000.0,
        },
    ),
    "Δx [mm]",
)

if show_mob:
    st.subheader(t(lang, "mob_title"))
    depths_mob = [z for z in depths if 0 < z < H]
    depths_mob_calc = (
        [z_effective_surcharge(z, gamma, q=q, gamma_Q_over_gamma_G=gQgG) for z in depths_mob]
        if q > 0
        else depths_mob
    )
    if len(depths_mob) < 2:
        st.warning(t(lang, "mob_few_pts"))
    else:
        mob = mobilized_profile(
            soil,
            depths_mob_calc,
            H=H,
            mode=kin_mode,
            delta_ref=delta_ref,
            side=side,
            seismic=seismic,
        )
        df_mob = pd.DataFrame(
            {
                "z [m]": depths_mob,
                "Δx [mm]": mob["dx"] * 1000.0,
                "Δx,lim [mm]": mob["dx_lim"] * 1000.0,
                "ξ = Δx/Δx,lim": mob["xi"],
                "σ [kPa]": mob["sigma"],
            }
        )
        st.dataframe(
            df_mob.style.format(
                {
                    "z [m]": "{:.2f}",
                    "Δx [mm]": "{:.2f}",
                    "Δx,lim [mm]": "{:.2f}",
                    "ξ = Δx/Δx,lim": "{:.3f}",
                    "σ [kPa]": "{:.1f}",
                },
                na_rep="—",
            ),
            use_container_width=True,
            hide_index=True,
        )
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"**{t(lang, 'dx_and_lim')}**")
            _line_chart(
                _melt_series(
                    depths_mob,
                    {"Δx": mob["dx"] * 1000.0, "Δx,lim": mob["dx_lim"] * 1000.0},
                ),
                "Δx [mm]",
            )
        with m2:
            st.markdown(f"**{t(lang, 'sigma_mob')}**")
            idx = [depths.index(z) for z in depths_mob]
            series = {
                "σ": mob["sigma"],
                "σo": np.asarray(tab["sigma_o"])[idx],
            }
            if side == "active":
                series["σa"] = np.asarray(tab["sigma_a"])[idx]
            else:
                series["σp"] = np.asarray(tab["sigma_p"])[idx]
            _line_chart(_melt_series(depths_mob, series), "σ [kPa]")

with st.expander(t(lang, "formulas")):
    st.latex(r"K_{oe}=(1-\sin\phi')-\frac{2c'}{\gamma z}\tan\left(45^\circ-\frac{\phi'}{2}\right)")
    st.latex(r"K_{ae}=\frac{1-\sin\phi'}{1+\sin\phi'}-\frac{2c'}{\gamma z}\tan\left(45^\circ-\frac{\phi'}{2}\right)")
    st.latex(r"K_{pe}=\frac{1+\sin\phi'}{1-\sin\phi'}+\frac{2c'}{\gamma z}\tan\left(45^\circ+\frac{\phi'}{2}\right)")
    st.latex(r"\sigma_o=K_{oe}\,\gamma z,\quad \sigma_a=K_a\gamma z-2c'\tan(45^\circ-\phi'/2)")
    st.latex(r"\sigma_p=K_p\gamma z+2c'\tan(45^\circ+\phi'/2)")
    st.latex(
        r"\Delta x_{a;\mathrm{lim}}=\frac{\pi}{4}\frac{1-\nu^2}{E}"
        r"\frac{(H+z)^3(H-z)}{H^2 z}(K_{oe}-K_{ae})\gamma z"
    )
    st.latex(
        r"\xi=\min\!\left(\frac{|\Delta x|}{\Delta x_{\lim}},1\right),"
        r"\quad \sigma=\sigma_o+\xi(\sigma_{\lim}-\sigma_o)"
    )

st.download_button(
    t(lang, "download"),
    df.to_csv(index=False).encode("utf-8"),
    file_name="pantelidis_earth_pressure.csv",
    mime="text/csv",
)
