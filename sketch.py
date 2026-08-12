"""Situation sketch: ground surface, excavation, wall + translation / rotation."""

from __future__ import annotations

from i18n import t


def situation_svg(
    mode: str = "translation",
    side: str = "active",
    lang: str = "pl",
    width: int = 640,
    height: int = 360,
) -> str:
    """
    Cross-section SVG.
    mode: translation | rotation_bottom | rotation_top | local_fraction
    side: active | passive
    lang: pl | en
    """
    into_excavation = side == "active"
    dx_sign = 1 if into_excavation else -1

    W, H = width, height
    ground_y = 70
    trench_y = 250
    wall_x0 = 300
    wall_t = 14
    embed = 40
    toe_y = trench_y + embed
    crown_y = ground_y
    d = 28 * dx_sign

    def wall_poly(x_shift_crown: float, x_shift_toe: float) -> str:
        x_c = wall_x0 + x_shift_crown
        x_t = wall_x0 + x_shift_toe
        return (
            f"{x_c},{crown_y} {x_c + wall_t},{crown_y} "
            f"{x_t + wall_t},{toe_y} {x_t},{toe_y}"
        )

    if mode == "rotation_bottom":
        wall_fill = wall_poly(d, 0)
        wall_dash = wall_poly(0, 0)
        motion_note = t(lang, "sk_motion_rot_bot")
        hinge_cx, hinge_cy = wall_x0 + wall_t / 2, toe_y
        show_hinge_top = False
        show_hinge_bot = True
    elif mode == "rotation_top":
        wall_fill = wall_poly(0, d)
        wall_dash = wall_poly(0, 0)
        motion_note = t(lang, "sk_motion_rot_top")
        hinge_cx, hinge_cy = wall_x0 + wall_t / 2, crown_y
        show_hinge_top = True
        show_hinge_bot = False
    else:
        wall_fill = wall_poly(d, d)
        wall_dash = wall_poly(0, 0)
        motion_note = (
            t(lang, "sk_motion_trans")
            if mode == "translation"
            else t(lang, "sk_motion_frac")
        )
        hinge_cx = hinge_cy = 0
        show_hinge_top = show_hinge_bot = False

    side_note = t(lang, "sk_side_a") if side == "active" else t(lang, "sk_side_p")
    arrow_y = (crown_y + trench_y) / 2
    ax0 = wall_x0 + wall_t / 2
    ax1 = ax0 + d

    soil_back = f"M 40,{ground_y} L {wall_x0},{ground_y} L {wall_x0},{toe_y} L 40,{toe_y} Z"
    soil_front = (
        f"M {wall_x0 + wall_t},{trench_y} L 600,{trench_y} L 600,{toe_y} "
        f"L {wall_x0 + wall_t},{toe_y} Z"
    )

    lbl_ground = t(lang, "sk_ground")
    lbl_soil = t(lang, "sk_soil")
    lbl_trench = t(lang, "sk_trench_bottom")
    lbl_exc = t(lang, "sk_excavation")
    lbl_wall = t(lang, "sk_wall")
    lbl_hinge = t(lang, "sk_hinge")
    lbl_zone = t(lang, "sk_zone_a") if side == "active" else t(lang, "sk_zone_p")
    lbl_dash = t(lang, "sk_dashed")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
      <line x1="0" y1="0" x2="0" y2="8" stroke="#8a7a5a" stroke-width="1.2"/>
    </pattern>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#1a1a1a"/>
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#f7f4ef"/>

  <path d="{soil_back}" fill="url(#hatch)" opacity="0.55"/>
  <path d="{soil_back}" fill="#c4b48a" opacity="0.35"/>
  <line x1="40" y1="{ground_y}" x2="{wall_x0}" y2="{ground_y}" stroke="#333" stroke-width="2"/>
  <text x="90" y="{ground_y - 12}" font-family="Georgia, serif" font-size="14" fill="#222">{lbl_ground}</text>
  <text x="70" y="160" font-family="Georgia, serif" font-size="13" fill="#444">{lbl_soil}</text>

  <path d="{soil_front}" fill="#c4b48a" opacity="0.25"/>
  <line x1="{wall_x0 + wall_t}" y1="{trench_y}" x2="600" y2="{trench_y}" stroke="#333" stroke-width="2"/>
  <text x="400" y="{trench_y - 10}" font-family="Georgia, serif" font-size="14" fill="#222">{lbl_trench}</text>
  <text x="450" y="200" font-family="Georgia, serif" font-size="13" fill="#666">{lbl_exc}</text>

  <polygon points="{wall_dash}" fill="none" stroke="#888" stroke-width="1.5" stroke-dasharray="5 4"/>
  <polygon points="{wall_fill}" fill="#4a5560" stroke="#1a1a1a" stroke-width="1.2"/>
  <text x="{wall_x0 - 70}" y="{crown_y + 20}" font-family="Georgia, serif" font-size="13" fill="#222">{lbl_wall}</text>

  <line x1="250" y1="{crown_y}" x2="250" y2="{trench_y}" stroke="#222" stroke-width="1"/>
  <line x1="244" y1="{crown_y}" x2="256" y2="{crown_y}" stroke="#222"/>
  <line x1="244" y1="{trench_y}" x2="256" y2="{trench_y}" stroke="#222"/>
  <text x="220" y="{(crown_y + trench_y) / 2}" font-family="Georgia, serif" font-size="14" fill="#222">H</text>

  <line x1="55" y1="{ground_y}" x2="55" y2="{ground_y + 70}" stroke="#222" stroke-width="1.2" marker-end="url(#arrow)"/>
  <text x="62" y="{ground_y + 45}" font-family="Georgia, serif" font-size="13" fill="#222">z</text>

  <line x1="{ax0}" y1="{arrow_y}" x2="{ax1}" y2="{arrow_y}" stroke="#1a1a1a" stroke-width="2.2" marker-end="url(#arrow)"/>
  <text x="{(ax0 + ax1) / 2 - 10}" y="{arrow_y - 10}" font-family="Georgia, serif" font-size="13" fill="#111">Δx</text>
'''

    if show_hinge_bot or show_hinge_top:
        svg += (
            f'  <circle cx="{hinge_cx}" cy="{hinge_cy}" r="6" '
            f'fill="#f7f4ef" stroke="#1a1a1a" stroke-width="2"/>\n'
            f'  <text x="{hinge_cx + 12}" y="{hinge_cy + 4}" '
            f'font-family="Georgia, serif" font-size="12" fill="#222">{lbl_hinge}</text>\n'
        )

    svg += f'''  <text x="120" y="{trench_y + 28}" font-family="Georgia, serif" font-size="12" fill="#333">{lbl_zone}</text>
  <text x="40" y="330" font-family="Georgia, serif" font-size="13" fill="#111">{motion_note} — {side_note}</text>
  <text x="40" y="348" font-family="Georgia, serif" font-size="11" fill="#555">{lbl_dash}</text>
</svg>'''
    return svg
