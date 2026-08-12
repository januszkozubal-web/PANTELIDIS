"""Szkic sytuacji: naziom, wykop, ściana + translacja / obrót."""

from __future__ import annotations


def situation_svg(
    mode: str = "translation",
    side: str = "active",
    width: int = 640,
    height: int = 360,
) -> str:
    """
    SVG przekroju.
    mode: translation | rotation_bottom | rotation_top | local_fraction
    side: active (ściana od gruntu / w wykop) | passive (w grunt)
    """
    # kierunek ruchu ściany w szkicu: +x w prawo (w wykop)
    into_excavation = side == "active"
    dx_sign = 1 if into_excavation else -1

    # geometria w jednostkach viewBox
    W, H = width, height
    ground_y = 70
    trench_y = 250
    wall_x0 = 300
    wall_t = 14
    embed = 40  # zagłębienie poniżej dna wykopu
    toe_y = trench_y + embed
    crown_y = ground_y

    # przemieszczenie narysowane (przesada wizualna)
    d = 28 * dx_sign

    def wall_poly(x_shift_crown: float, x_shift_toe: float) -> str:
        x_c = wall_x0 + x_shift_crown
        x_t = wall_x0 + x_shift_toe
        # lekko trapezoidalny prostokąt ściany (linia środkowa)
        return (
            f"{x_c},{crown_y} {x_c + wall_t},{crown_y} "
            f"{x_t + wall_t},{toe_y} {x_t},{toe_y}"
        )

    if mode == "rotation_bottom":
        # dno utwierdzone
        wall_fill = wall_poly(d, 0)
        wall_dash = wall_poly(0, 0)
        motion_note = "obrót względem dna"
        hinge_cx, hinge_cy = wall_x0 + wall_t / 2, toe_y
        show_hinge_top = False
        show_hinge_bot = True
    elif mode == "rotation_top":
        wall_fill = wall_poly(0, d)
        wall_dash = wall_poly(0, 0)
        motion_note = "obrót względem góry"
        hinge_cx, hinge_cy = wall_x0 + wall_t / 2, crown_y
        show_hinge_top = True
        show_hinge_bot = False
    else:
        # translacja / ułamek lokalny — rysuj jak translację
        wall_fill = wall_poly(d, d)
        wall_dash = wall_poly(0, 0)
        motion_note = (
            "translacja Δx"
            if mode == "translation"
            else "przemieszczenie lokalne (ułamek Δx,lim)"
        )
        hinge_cx = hinge_cy = 0
        show_hinge_top = show_hinge_bot = False

    side_note = "strona aktywna (parcie)" if side == "active" else "strona bierna (odpor)"
    arrow_y = (crown_y + trench_y) / 2
    ax0 = wall_x0 + wall_t / 2
    ax1 = ax0 + d

    # wypełnienia gruntu
    soil_back = f"M 40,{ground_y} L {wall_x0},{ground_y} L {wall_x0},{toe_y} L 40,{toe_y} Z"
    soil_front = (
        f"M {wall_x0 + wall_t},{trench_y} L 600,{trench_y} L 600,{toe_y} "
        f"L {wall_x0 + wall_t},{toe_y} Z"
    )

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

  <!-- grunt za ścianą + naziom -->
  <path d="{soil_back}" fill="url(#hatch)" opacity="0.55"/>
  <path d="{soil_back}" fill="#c4b48a" opacity="0.35"/>
  <line x1="40" y1="{ground_y}" x2="{wall_x0}" y2="{ground_y}" stroke="#333" stroke-width="2"/>
  <text x="90" y="{ground_y - 12}" font-family="Georgia, serif" font-size="14" fill="#222">naziom</text>
  <text x="70" y="160" font-family="Georgia, serif" font-size="13" fill="#444">grunt</text>

  <!-- wykop -->
  <path d="{soil_front}" fill="#c4b48a" opacity="0.25"/>
  <line x1="{wall_x0 + wall_t}" y1="{trench_y}" x2="600" y2="{trench_y}" stroke="#333" stroke-width="2"/>
  <text x="420" y="{trench_y - 10}" font-family="Georgia, serif" font-size="14" fill="#222">dno wykopu</text>
  <text x="450" y="200" font-family="Georgia, serif" font-size="13" fill="#666">wykop</text>

  <!-- ściana początkowa (przerywana) -->
  <polygon points="{wall_dash}" fill="none" stroke="#888" stroke-width="1.5" stroke-dasharray="5 4"/>
  <!-- ściana po ruchu -->
  <polygon points="{wall_fill}" fill="#4a5560" stroke="#1a1a1a" stroke-width="1.2"/>
  <text x="{wall_x0 - 70}" y="{crown_y + 20}" font-family="Georgia, serif" font-size="13" fill="#222">ściana</text>

  <!-- wymiar H -->
  <line x1="250" y1="{crown_y}" x2="250" y2="{trench_y}" stroke="#222" stroke-width="1"/>
  <line x1="244" y1="{crown_y}" x2="256" y2="{crown_y}" stroke="#222"/>
  <line x1="244" y1="{trench_y}" x2="256" y2="{trench_y}" stroke="#222"/>
  <text x="220" y="{(crown_y + trench_y) / 2}" font-family="Georgia, serif" font-size="14" fill="#222">H</text>

  <!-- z w dół -->
  <line x1="55" y1="{ground_y}" x2="55" y2="{ground_y + 70}" stroke="#222" stroke-width="1.2" marker-end="url(#arrow)"/>
  <text x="62" y="{ground_y + 45}" font-family="Georgia, serif" font-size="13" fill="#222">z</text>

  <!-- strzałka ruchu -->
  <line x1="{ax0}" y1="{arrow_y}" x2="{ax1}" y2="{arrow_y}" stroke="#1a1a1a" stroke-width="2.2" marker-end="url(#arrow)"/>
  <text x="{(ax0 + ax1) / 2 - 10}" y="{arrow_y - 10}" font-family="Georgia, serif" font-size="13" fill="#111">Δx</text>
'''

    if show_hinge_bot or show_hinge_top:
        svg += (
            f'  <circle cx="{hinge_cx}" cy="{hinge_cy}" r="6" '
            f'fill="#f7f4ef" stroke="#1a1a1a" stroke-width="2"/>\n'
            f'  <text x="{hinge_cx + 12}" y="{hinge_cy + 4}" '
            f'font-family="Georgia, serif" font-size="12" fill="#222">przegub</text>\n'
        )

    # etykiety stref
    if side == "active":
        svg += f'''  <text x="120" y="{trench_y + 28}" font-family="Georgia, serif" font-size="12" fill="#333">strefa aktywna (parcie)</text>
'''
    else:
        svg += f'''  <text x="120" y="{trench_y + 28}" font-family="Georgia, serif" font-size="12" fill="#333">strefa bierna (odpor)</text>
'''

    svg += f'''  <text x="40" y="330" font-family="Georgia, serif" font-size="13" fill="#111">{motion_note} — {side_note}</text>
  <text x="40" y="348" font-family="Georgia, serif" font-size="11" fill="#555">linia przerywana: położenie początkowe</text>
</svg>'''
    return svg
