#!/usr/bin/env python3
"""Identidade HoryNotes: hexagono do HoryTools com a estrela no lugar do H.

Reaproveita o gerador do HoryTools (mesmos glifos, mesmo ruido, mesma
semente), para o wordmark sair igual ao HORY TOOLS.
"""

import importlib.util
import math
import os
import random
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE + "/"
HT_ASSETS = os.path.normpath(os.path.join(HERE, "..", "..", "assets"))
MARK_SVG = next((p for p in (
    os.path.join(HT_ASSETS, "HoryTools-Mark.svg"),
    "/home/gabriel/Projects/HoryTools/assets/HoryTools-Mark.svg",
) if os.path.exists(p)), "")
GEN = next((p for p in (
    os.path.join(HT_ASSETS, "generate-horytools-logo.py"),
    "/home/gabriel/Projects/HoryTools/assets/generate-horytools-logo.py",
) if os.path.exists(p)), "")

KHAKI = "#A99A7A"     # hexagono, estrela e wordmark, igual ao HoryTools

spec = importlib.util.spec_from_file_location("horytools_logo", GEN)
HT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HT)

CAP = HT.CAP                 # 300
STROKE = HT.STROKE           # 0.0556
SEED = 20261016


# --------------------------------------------------- glifos que faltavam
def G_N(w=0.350):
    return [(0.032, 0.025, 0.032, 0.975),
            (w - 0.032, 0.030, w - 0.032, 0.975),
            (0.036, 0.055, w - 0.036, 0.960)]


def G_E(w=0.300):
    return [(0.030, 0.020, 0.030, 0.972),
            (0.022, 0.046, w - 0.014, 0.028),
            (0.044, 0.500, w - 0.052, 0.486),
            (0.022, 0.958, w - 0.014, 0.938)]


SMALL = {"N": (G_N(), 0.350), "O": (HT.G_O(0.375), 0.375), "T": (HT.G_T(), 0.330),
         "E": (G_E(), 0.300), "S": (HT.G_S(), 0.330)}


# ------------------------------------------------------------ geometria
def star_profile():
    return [v for _, v in HT_STAR]


def catmull(vals, t):
    n = len(vals) - 1
    i = min(int(t), n - 1)
    f = t - i
    p0 = vals[max(i - 1, 0)]
    p1, p2 = vals[i], vals[i + 1]
    p3 = vals[min(i + 2, n)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * f * f * f)


def sparkle(cx, cy, r, n=168):
    vals = star_profile()
    out = []
    for i in range(n):
        a = 360.0 * i / n
        t = a % 90
        if t > 45:
            t = 90 - t
        rad = catmull(vals, t / 45 * (len(vals) - 1)) * r
        out.append((cx + rad * math.cos(math.radians(a)),
                    cy + rad * math.sin(math.radians(a))))
    out.append(out[0])
    return out


# raio do ✦ lido do proprio glifo do app, a cada 1,5 grau
HT_STAR = [
    (0.0, 1.0000), (1.5, 0.9076), (3.0, 0.8037), (4.5, 0.7468), (6.0, 0.7052),
    (7.5, 0.6686), (9.0, 0.6423), (10.5, 0.6157), (12.0, 0.5945), (13.5, 0.5771),
    (15.0, 0.5623), (16.5, 0.5484), (18.0, 0.5361), (19.5, 0.5247), (21.0, 0.5138),
    (22.5, 0.5044), (24.0, 0.4993), (25.5, 0.4898), (27.0, 0.4814), (28.5, 0.4773),
    (30.0, 0.4722), (31.5, 0.4685), (33.0, 0.4620), (34.5, 0.4585), (36.0, 0.4570),
    (37.5, 0.4550), (39.0, 0.4534), (40.5, 0.4521), (42.0, 0.4510), (43.5, 0.4494),
    (45.0, 0.4500),
]


def hexagono_horytools():
    """Hexagono exato do HoryTools-Mark.svg (mesmos pontos, ja com o ruido)."""
    root = ET.parse(MARK_SVG).getroot()
    p = root[0]
    pts = [tuple(map(float, t.split())) for t in
           p.get("d")[1:].replace("Z", "").split(" L")]
    return pts, float(p.get("stroke-width")), p.get("stroke")


def hexagono_do_lockup(rng):
    """O hexagono exatamente como sai no lockup do HoryTools.

    Precisa vir depois de gastar o rng com HORY e TOOLS, na mesma ordem
    do build() do gerador do HoryTools: assim o ruido cai nos mesmos
    lugares e a marca fica na mesma coordenada do lockup original.
    """
    HT.glyphs("TOOLS", {"T": (HT.G_T(), 0.330), "O": (HT.G_O(0.375), 0.375),
                        "L": (HT.G_L(), 0.300), "S": (HT.G_S(), 0.330)},
              rng, CAP * 0.5, 0.105, STROKE * CAP * 0.5, CAP * 0.5 * 0.011)
    paths, mw, mh = HT.mark_paths_for("nut", rng, CAP * 1.40)
    paths = HT.translate(paths, 0.0, 0.425 * CAP - mh / 2)
    return paths[0], mw


def star_shapes(rng, cx, cy, r):
    st, closed = HT.wobble(sparkle(cx, cy, r), rng, r * 0.007, True, step=3.0)
    return {"pts": st, "closed": closed, "w": r * 0.026, "op": 1.0,
            "fill": KHAKI, "stroke": KHAKI}


def hex_shapes(pts, stroke_w, color):
    return {"pts": pts, "closed": True, "w": stroke_w, "op": 1.0,
            "fill": None, "stroke": color}


# ---------------------------------------------------------------- saida
def emit(name, shapes, label, square=None, pad=10.0):
    xs = [x for s in shapes for x, _ in s["pts"]]
    ys = [y for s in shapes for _, y in s["pts"]]
    extra = max(s["w"] for s in shapes) / 2 + pad
    minx, miny = min(xs) - extra, min(ys) - extra
    w = (max(xs) - min(xs)) + 2 * extra
    h = (max(ys) - min(ys)) + 2 * extra
    if square:
        minx -= (square - w) / 2
        miny -= (square - h) / 2
        w = h = square
    body = []
    for s in shapes:
        d = "M" + " L".join(f"{x - minx:.1f} {y - miny:.1f}" for x, y in s["pts"])
        if s.get("closed"):
            d += " Z"
        attrs = [f'd="{d}"']
        attrs.append(f'fill="{s["fill"]}"' if s.get("fill") else 'fill="none"')
        if s.get("stroke"):
            attrs.append(f'stroke="{s["stroke"]}" stroke-width="{s["w"]:.1f}" '
                         'stroke-linejoin="round" stroke-linecap="round"')
        if s.get("op", 1.0) < 1:
            attrs.append(f'stroke-opacity="{s["op"]:.2f}"')
        body.append("<path " + " ".join(attrs) + "/>")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
           f'width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{label}">\n'
           + "\n".join(body) + "\n</svg>\n")
    with open(OUT + name, "w") as f:
        f.write(svg)
    print(f"{name}: {w:.0f}x{h:.0f}, {len(shapes)} formas, {len(svg) / 1024:.1f} KB")
    return minx, miny


def main():
    pts, stroke_w, color = hexagono_horytools()
    hxs = [x for x, _ in pts]
    hys = [y for _, y in pts]
    hcx = (min(hxs) + max(hxs)) / 2
    hcy = (min(hys) + max(hys)) / 2

    # --- marca sozinha: hexagono + estrela centrada
    star_r = 100.0
    rng = random.Random(SEED)
    hex_solo = hex_shapes(pts, stroke_w, color)
    star_solo = star_shapes(rng, hcx, hcy, star_r)
    emit("HoryNotes-Logo.svg", [hex_solo, star_solo], "HoryNotes")

    icon = [hex_solo, star_solo]
    xs = [x for s in icon for x, _ in s["pts"]]
    ys = [y for s in icon for _, y in s["pts"]]
    extra = max(s["w"] for s in icon) / 2
    ccx, ccy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    side = max(max(xs) - min(xs) + 2 * extra, max(ys) - min(ys) + 2 * extra) * 1.16
    icon = [dict(s, pts=[(x + side / 2 - ccx, y + side / 2 - ccy) for x, y in s["pts"]])
            for s in icon]
    emit("HoryNotes-Icon.svg", icon, "HoryNotes", square=side)

    # --- lockup: mesma montagem do HoryTools, com NOTES no lugar de TWEAKS
    rng = random.Random(SEED)
    MAIN = {"H": (HT.G_H(), 0.262), "O": (HT.G_O(), 0.372),
            "R": (HT.G_R(), 0.306), "Y": (HT.G_Y(), 0.355)}
    main_paths, main_w = HT.glyphs("HORY", MAIN, rng, CAP, 0.090, STROKE * CAP, CAP * 0.0075)
    small_cap = CAP * 0.5

    # a marca vem do mesmo rng, logo depois do HORY: identica a do HoryTools
    hex_paths, mark_w = hexagono_do_lockup(rng)
    mx = [x for x, _ in hex_paths["pts"]]
    my = [y for _, y in hex_paths["pts"]]
    mcx, mcy = (min(mx) + max(mx)) / 2, (min(my) + max(my)) / 2
    hex_mk = dict(hex_paths, fill=None, stroke=color)

    # a estrela e o NOTES saem de rngs proprios, so para nao mexer no resto
    star_mk = star_shapes(random.Random(SEED + 1), mcx, mcy, star_r)
    small_paths, small_w = HT.glyphs("NOTES", SMALL, random.Random(SEED + 2), small_cap,
                                     0.105, STROKE * small_cap, small_cap * 0.011)
    small_paths = HT.translate(small_paths, main_w + 0.130 * CAP, 0.415 * CAP - small_cap / 2)

    text_dx = mark_w + 0.130 * CAP
    wordmark = [dict(q, stroke=color) for q in main_paths + small_paths]
    lockup = [hex_mk, star_mk] + HT.translate(wordmark, text_dx, 0.0)
    emit("HoryNotes-Lockup.svg", lockup, "HoryNotes")


if __name__ == "__main__":
    main()
