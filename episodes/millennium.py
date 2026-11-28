"""Episode: The Millennium Prize Problems, and the AI race to claim them.  (narrated, ~80 s, vertical, 3D)

Facts as of late November 2026:
- Clay Mathematics Institute, 2000: seven problems, $1M each.
- Poincaré: solved by Perelman (2002-03), prize awarded 2010, he declined it.
- Navier-Stokes: OpenAI posted a claimed proof (Sept 2026), not independently verified yet.
- Riemann: Anthropic mathematician Levent Alpöge posted a Lean-checked proof made with Claude (Nov 20, 2026).
  Clay only pays at least two years after publication and general acceptance, so no prize yet.
- Hodge, Yang-Mills (mass gap), Birch and Swinnerton-Dyer, P vs NP: open.

Every problem gets its own small visual, computed for real:
  Poincaré       loop shrinking on a sphere vs. stuck on a torus (the 2D picture of the idea)
  P vs NP        a graph 3-coloring: checking is one pass, brute-force search walks all 3^8 options
  Hodge          loops on a torus, and a (1,1) loop built from the two basic ones
  Yang-Mills     quarks on gluon strings, then lattice-QCD glueball levels (Morningstar & Peardon 1999)
  BSD            rational points on y^2 = x^3 - x + 1, with real chord addition
  Navier-Stokes  particles advected by a tightening Lamb-Oseen vortex
  Riemann        the prime-counting staircase vs. Li(x), then Hardy's Z(t) along the critical line,
                 crossing zero at the real zeta zeros

Render:  ./make.sh millennium silent    (no audio, no credits, 720p)
         ./make.sh millennium           (ElevenLabs, 1080x1920)
"""
import itertools
import sys
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reelearn.scene import EpisodeScene  # noqa: E402
from reelearn.style import *  # noqa: E402,F403

OPEN, SOLVED, CLAIMED, ALARM = PALETTE[2], PALETTE[1], EMPH, PALETTE[0]

# ================================================================ hub: the seven problems
PROBLEMS = ["Poincaré", "P vs NP", "Hodge", "Yang–Mills", "Birch &\nSwinnerton-Dyer", "Navier–Stokes", "Riemann"]
POINCARE, PNP, HODGE, YM, BSD, NS, RH = range(7)
FINAL_STATUS = {POINCARE: SOLVED, NS: CLAIMED, RH: CLAIMED}

HUB_PHI, MINI_PHI = 74 * DEGREES, 60 * DEGREES
C = np.array([0.0, 0.0, 1.25])           # 3D view target = screen center; minis are built around it
CAMERA = dict(phi=HUB_PHI, theta=-90 * DEGREES, zoom=1.0, frame_center=C)
X_COL, Z_STEP, HUB_LIFT = 1.45, 0.92, 1.3
VIS_Y = -0.2                             # center of 2D overlay visuals


def orb_pos(i):
    """Zigzag down two columns, alternating depth, so the camera sway shows parallax."""
    side = -1 if i % 2 == 0 else 1
    return np.array([side * X_COL, side * 0.6, (3 - i) * Z_STEP + HUB_LIFT])


def orb(i, color=OPEN):
    p = orb_pos(i)
    core = Sphere(center=p, radius=0.26, resolution=(12, 12)).set_color(color)
    halo = Sphere(center=p, radius=0.44, resolution=(12, 12)).set_color(color).set_opacity(0.16)
    return VGroup(core, halo)


def name_label(i, color=FG):
    label = T(PROBLEMS[i], size=28, color=color, weight="MEDIUM", line_spacing=0.8).move_to(orb_pos(i))
    return label.shift(IN * (0.45 + label.height / 2))


def floor():
    grid = NumberPlane(
        x_range=[-4, 4, 1], y_range=[-4, 4, 1],
        background_line_style={"stroke_color": FAINT, "stroke_width": 1.5, "stroke_opacity": 0.6},
        axis_config={"stroke_color": FAINT, "stroke_width": 2},
    )
    return grid.shift(IN * 4.0)


# ================================================================ Poincaré / Hodge: sphere and torus
R_SPH = 2.0
TOR_M, TOR_m = 1.8, 0.72   # torus major / minor radius


def glassy(surface, color):
    return surface.set_fill(color, opacity=0.22).set_stroke(color, width=0.6, opacity=0.45)


def sphere_loop(a, color=EMPH):
    """Circle of latitude at polar angle a (a -> 0 shrinks it to the north pole)."""
    return ParametricFunction(
        lambda u: C + R_SPH * np.array([np.sin(a) * np.cos(u), np.sin(a) * np.sin(u), np.cos(a)]),
        t_range=[0, TAU], color=color, stroke_width=7)


def torus_top_loop(r, color=EMPH):
    """Horizontal circle of radius r lying on the torus's upper surface (only exists for |r - M| <= m)."""
    h = np.sqrt(max(TOR_m ** 2 - (r - TOR_M) ** 2, 0)) + 0.02
    return ParametricFunction(lambda u: C + np.array([r * np.cos(u), r * np.sin(u), h]),
                              t_range=[0, TAU], color=color, stroke_width=7)


def torus_curve(p, q, color, phase=0.0):
    """(p, q) loop on the torus: p times around the hole, q times around the tube."""
    def f(s):
        u, v = p * s, q * s + phase
        rr = TOR_M + (TOR_m + 0.02) * np.cos(v)
        return C + np.array([rr * np.cos(u), rr * np.sin(u), (TOR_m + 0.02) * np.sin(v)])
    return ParametricFunction(f, t_range=[0, TAU], color=color, stroke_width=7)


# ================================================================ P vs NP: 3-coloring, checked vs searched
GRAPH_NODES = [np.array(v, float) * 1.1 for v in itertools.product((-1, 1), repeat=3)]   # cube corners
GRAPH_NODES = [v * 1.4 for v in GRAPH_NODES]
GRAPH_EDGES = [(i, j) for i in range(8) for j in range(i + 1, 8)
               if np.sum(np.abs(GRAPH_NODES[i] - GRAPH_NODES[j]) > 0) == 1]              # cube edges
GRAPH_EDGES += [(0, 3), (4, 7), (0, 5)]                                                   # face diagonals
COLORINGS = list(itertools.product(range(3), repeat=8))                                   # 3^8 = 6,561
VALID = [c for c in COLORINGS if all(c[i] != c[j] for i, j in GRAPH_EDGES)]
assert len(COLORINGS) == 6561 and VALID, "graph must be 3-colorable"
ANSWER = VALID[len(VALID) // 2]
NODE_COLORS = [PALETTE[0], PALETTE[1], PALETTE[4]]
_mant, _exp = f"{3 ** 100:.1e}".split("e+")
OPTIONS_100 = f"{_mant} × 10{str(int(_exp)).translate(str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹'))}"
assert OPTIONS_100 == "5.2 × 10⁴⁷"

# ================================================================ Yang-Mills: lattice glueball spectrum (GeV)
GLUEBALLS = [("0⁺⁺", 1.73), ("2⁺⁺", 2.40), ("0⁻⁺", 2.59)]   # Morningstar & Peardon, PRD 60, 034509 (1999)


# ================================================================ BSD: rational points on y^2 = x^3 - x + 1
A_EC, B_EC = -1, 1


def ec_add(P, Q):
    """Chord-and-tangent addition with exact fractions. None is the point at infinity."""
    if P is None:
        return Q
    if Q is None:
        return P
    (x1, y1), (x2, y2) = P, Q
    if x1 == x2 and y1 == -y2:
        return None
    lam = (3 * x1 * x1 + A_EC) / (2 * y1) if P == Q else (y2 - y1) / (x2 - x1)
    x3 = lam * lam - x1 - x2
    return (x3, lam * (x1 - x3) - y1)


def on_curve(P):
    x, y = P
    return y * y == x ** 3 + A_EC * x + B_EC


CHORD_P, CHORD_Q = (F(-1), F(1)), (F(0), F(1))
CHORD_SUM = ec_add(CHORD_P, CHORD_Q)
assert CHORD_SUM == (F(1), F(-1))             # third hit is (1, 1); reflecting gives (1, -1)
X_LO, X_HI = -1.55, 2.0
_seed = [CHORD_P, CHORD_Q, (F(1), F(1))]
_pts = set()
for P in _seed:
    for Q in _seed + [(p[0], -p[1]) for p in _seed]:
        S = ec_add(P, Q)
        for R in (S, ec_add(S, P) if S else None):
            if R is not None and X_LO <= R[0] <= X_HI and R[0].denominator <= 64:
                assert on_curve(R)
                _pts.add(R)
EXTRA_POINTS = sorted(p for p in _pts if p not in (CHORD_P, CHORD_Q, CHORD_SUM, (F(1), F(1))))
EC_SCALE = 1.15
EC_SHIFT = np.array([-(X_LO + X_HI) / 2 * EC_SCALE, VIS_Y, 0])


def ec_xy(x, y):
    return np.array([x * EC_SCALE, y * EC_SCALE, 0]) + EC_SHIFT


def ec_curve():
    root = np.roots([1, 0, A_EC, B_EC])
    x0 = float(root[np.isreal(root)].real.max())
    xs = x0 + (X_HI - x0) * np.linspace(0, 1, 160) ** 2        # dense near the vertical tangent
    ys = np.sqrt(np.maximum(xs ** 3 + A_EC * xs + B_EC, 0))
    upper = [ec_xy(x, y) for x, y in zip(xs, ys)]
    lower = [ec_xy(x, -y) for x, y in zip(xs, ys)]
    return VMobject(color=PALETTE[4], stroke_width=6).set_points_smoothly(lower[::-1] + upper[1:])


def ec_axes():
    return VGroup(
        Line(ec_xy(X_LO - 0.1, 0), ec_xy(X_HI + 0.1, 0), color=FAINT, stroke_width=2),
        Line(ec_xy(0, -2.7), ec_xy(0, 2.7), color=FAINT, stroke_width=2),
    )


# ================================================================ Navier-Stokes: Lamb-Oseen vortex
VORTEX_RNG = np.random.default_rng(7)
N_PARTICLES = 320
V_Z = VORTEX_RNG.uniform(-1.9, 1.9, N_PARTICLES)
FUNNEL = 0.3 + 0.7 * (V_Z + 1.9) / 3.8                     # tornado: narrow at the bottom
V_R = np.sqrt(VORTEX_RNG.uniform(0.02, 1.0, N_PARTICLES)) * 2.2 * FUNNEL
V_TH = VORTEX_RNG.uniform(0, TAU, N_PARTICLES)
GAMMA = 6.0


def lamb_oseen_speed(r, rc):
    """Swirl speed of a Lamb-Oseen vortex (an exact Navier-Stokes solution) with core radius rc."""
    return GAMMA / (TAU * r) * (1 - np.exp(-(r / rc) ** 2))


# ================================================================ Riemann: the primes, then Z(t) on the critical line
X_PRIMES = 100
PRIMES = [n for n in range(2, X_PRIMES + 1) if all(n % d for d in range(2, int(n ** 0.5) + 1))]
assert len(PRIMES) == 25


def offset_li(x):
    """Li(x) = integral from 2 to x of dt / ln t: Gauss's smooth estimate of how many primes are <= x."""
    t = np.linspace(2, x, 2000)
    return np.trapezoid(1 / np.log(t), t) if x > 2 else 0.0


PLOT_W, PLOT_H, PLOT_YMAX = 5.6, 5.4, 30
PLOT_ORIGIN = np.array([-PLOT_W / 2, VIS_Y - PLOT_H / 2, 0])


def prime_xy(x, y):
    return PLOT_ORIGIN + np.array([x / X_PRIMES * PLOT_W, y / PLOT_YMAX * PLOT_H, 0])


def prime_plot():
    """pi(x), the real prime-counting staircase up to 100, next to the smooth Li(x) estimate."""
    axes = VGroup(Line(prime_xy(0, 0), prime_xy(X_PRIMES, 0), color=FAINT, stroke_width=2),
                  Line(prime_xy(0, 0), prime_xy(0, PLOT_YMAX), color=FAINT, stroke_width=2))
    corners, count = [prime_xy(0, 0)], 0
    for p in PRIMES + [X_PRIMES]:
        corners.append(prime_xy(p, count))
        if p in PRIMES:
            count += 1
            corners.append(prime_xy(p, count))
    stairs = VMobject(color=PALETTE[1], stroke_width=5).set_points_as_corners(corners)
    xs = np.linspace(2, X_PRIMES, 120)
    smooth = VMobject(color=EMPH, stroke_width=4).set_points_smoothly([prime_xy(x, offset_li(x)) for x in xs])
    smooth = DashedVMobject(smooth, num_dashes=40)
    tags = VGroup(T("Primes", size=26, color=PALETTE[1], weight="MEDIUM").next_to(prime_xy(X_PRIMES, len(PRIMES)), DOWN, buff=0.15),
                  T("Estimate", size=26, color=EMPH, weight="MEDIUM").next_to(prime_xy(X_PRIMES * 0.78, offset_li(78)), UL, buff=0.1))
    tags[0].align_to(prime_xy(X_PRIMES, 0), RIGHT)
    ticks = VGroup(*[Line(prime_xy(p, 0) + DOWN * 0.08, prime_xy(p, 0) + UP * 0.08, color=PALETTE[1], stroke_width=3)
                     for p in PRIMES])
    return axes, ticks, stairs, smooth, tags


# ================================================================ Riemann: Z(t) on the critical line
def riemann_siegel_z(t):
    """Hardy's Z(t): real-valued, with |Z(t)| = |zeta(1/2 + it)|. Riemann-Siegel formula plus first correction."""
    t = np.asarray(t, float)
    theta = t / 2 * np.log(t / TAU) - t / 2 - np.pi / 8 + 1 / (48 * t) + 7 / (5760 * t ** 3)
    a = np.sqrt(t / TAU)
    n_terms, p = np.floor(a).astype(int), a - np.floor(a)
    z = sum(np.where(n <= n_terms, np.cos(theta - t * np.log(n)) / np.sqrt(n), 0.0)
            for n in range(1, int(n_terms.max()) + 1)) * 2
    return z + (-1.0) ** (n_terms - 1) * (TAU / t) ** 0.25 * np.cos(TAU * (p * p - p - 1 / 16)) / np.cos(TAU * p)


T_MIN, T_MAX = 7.0, 50.0
Z_T = np.linspace(T_MIN, T_MAX, 4001)
Z_VAL = riemann_siegel_z(Z_T)
_tf = np.linspace(10, T_MAX, 40001)
_zf = riemann_siegel_z(_tf)
ZEROS = _tf[np.where(np.sign(_zf[:-1]) != np.sign(_zf[1:]))[0]]
assert abs(ZEROS[0] - 14.1347) < 0.01 and len(ZEROS) == 10, "zeta zeros off"
STRIP_Y0, STRIP_Y1 = -3.5, 2.9


def strip_y(t):
    return STRIP_Y0 + (STRIP_Y1 - STRIP_Y0) * t / T_MAX


def critical_strip():
    """2D overlay: the critical strip 0 < Re(s) < 1, the line Re = 1/2, Z(t) as a wave along it, and its zeros."""
    strip = Rectangle(width=3.2, height=STRIP_Y1 - STRIP_Y0, stroke_width=0, fill_color=OPEN, fill_opacity=0.12)
    strip.move_to([SAFE_CENTER_X, (STRIP_Y0 + STRIP_Y1) / 2, 0])
    edges = VGroup(*[DashedLine([x, STRIP_Y0, 0], [x, STRIP_Y1, 0], color=FAINT, stroke_width=2) for x in (-1.6, 1.6)])
    line = Line([0, STRIP_Y0, 0], [0, STRIP_Y1, 0], color=EMPH, stroke_width=4)
    tag = T("Re = ½", size=26, color=EMPH, weight="MEDIUM").next_to(line, UP, buff=0.15)
    k = 1.35 / np.abs(Z_VAL).max()
    wave = VMobject(color=PALETTE[1], stroke_width=5).set_points_smoothly(
        [np.array([k * z, strip_y(t), 0]) for t, z in zip(Z_T[::8], Z_VAL[::8])])
    zeros = VGroup(*[Dot([0, strip_y(t), 0], radius=0.11, color=FG) for t in ZEROS])
    return VGroup(strip, edges, line, tag), wave, zeros


# ================================================================ scene
class Millennium(EpisodeScene):
    def construct(self):
        self.set_camera_orientation(**CAMERA)
        orbs = VGroup(*[orb(i) for i in range(7)])
        names = VGroup(*[name_label(i) for i in range(7)])
        ground = floor()
        self.add(ground, orbs)                        # on screen from frame 0
        self.billboard(*names)
        self.begin_camera_sway(amplitude=9 * DEGREES, period=14)

        colors = [OPEN] * 7

        def hub_style(lit=range(7), dim=0.25, names_on=True):
            """One animation per core, halo and name: color each orb by status, dim all but `lit`."""
            anims = []
            for i in range(7):
                on = i in lit
                anims += [orbs[i][0].animate.set_color(colors[i]).set_opacity(1 if on else dim),
                          orbs[i][1].animate.set_color(colors[i]).set_opacity(0.16 if on else dim / 5),
                          names[i].animate.set_opacity((1 if on else 0.3) if names_on else 0)]
            return anims

        def handoff(*old, phi=None):
            """Between problems: clear the old visual and badge (and tilt the camera) before the next line starts."""
            anims = [FadeOut(m) for m in old] + self.label_anims(None)
            if phi is not None:
                anims.append(self.camera.phi_tracker.animate.set_value(phi))
            self.play(*anims, run_time=0.7)
            self.wait(0.25)

        def pinned(*mobs):
            """Register 2D overlays without showing them yet."""
            self.overlay(*mobs)
            for m in mobs:
                self.remove(m)
            return mobs[0] if len(mobs) == 1 else mobs

        # ------------------------------------------------------------ 1. hook
        with self.narrate("Seven math problems. *One million dollars* each. "
                          "And AI may have just cracked *one.*") as t:
            budget = t.get_remaining_duration()
            self.play(*self.label_anims("$1,000,000 Each", color=EMPH, stroke=EMPH),
                      LaggedStart(*[Indicate(o, color=EMPH, scale_factor=1.4) for o in orbs], lag_ratio=0.12),
                      run_time=min(1.6, budget * 0.4))
            self.wait(max(0, t.get_remaining_duration() - 1.4))
            colors[RH] = CLAIMED
            self.play(*hub_style(lit=[RH]), Flash(orbs[RH], color=EMPH, flash_radius=0.6),
                      *self.label_anims("Clay Millennium Prize · 2000"), run_time=0.8)
        colors[RH] = OPEN
        handoff(orbs, names, ground, phi=MINI_PHI)

        # ------------------------------------------------------------ 2. Poincaré: loops on a sphere vs a torus
        ball = glassy(Sphere(center=C, radius=R_SPH, resolution=(18, 32)), PALETTE[4])
        a = ValueTracker(PI / 2)
        loop = always_redraw(lambda: sphere_loop(a.get_value()))
        with self.narrate("*Poincaré:* if every loop shrinks to a point, it's a *sphere.* "
                          "It pins down the *shape of space.* Perelman solved it, and *refused* the million.") as t:
            budget = t.get_remaining_duration()
            self.play(FadeIn(ball, scale=0.85), *self.label_anims("Poincaré", color=SOLVED, stroke=SOLVED), run_time=0.7)
            self.play(Create(loop), run_time=0.4)
            self.play(a.animate.set_value(0.02), run_time=budget * 0.18, rate_func=smooth)
            pole = Dot3D(C + OUT * R_SPH, radius=0.09, color=EMPH)
            self.remove(loop)
            self.add(pole)
            self.play(Flash(pole, color=EMPH, flash_radius=0.35), run_time=0.4)

            donut = glassy(Torus(major_radius=TOR_M, minor_radius=TOR_m, resolution=(14, 32)).move_to(C), PALETTE[2])
            r = ValueTracker(TOR_M)
            stuck = always_redraw(lambda: torus_top_loop(r.get_value()))
            self.play(FadeOut(ball), FadeOut(pole), FadeIn(donut), run_time=0.7)
            self.play(Create(stuck), run_time=0.3)
            self.play(r.animate.set_value(TOR_M - TOR_m * 0.97), run_time=budget * 0.12,
                      *self.label_anims("Shape Of Space", color=SOLVED, stroke=SOLVED))
            stuck.clear_updaters()
            self.play(stuck.animate.set_color(ALARM), Wiggle(stuck, scale_value=1.05), run_time=0.6)
            self.wait(max(0, t.get_remaining_duration() - 1.0))
            self.play(*self.label_anims("Solved · Prize Declined", color=SOLVED, stroke=SOLVED),
                      FadeOut(stuck), donut.animate.set_fill(SOLVED, opacity=0.22).set_stroke(SOLVED, opacity=0.45),
                      run_time=0.6)

        handoff(donut, phi=68 * DEGREES)

        # ------------------------------------------------------------ 3. P vs NP: check vs search
        nodes = VGroup(*[Dot3D(C + p, radius=0.22, color=FG, resolution=(8, 8)) for p in GRAPH_NODES])
        edges = VGroup(*[Line(C + GRAPH_NODES[i], C + GRAPH_NODES[j], color=MUTED, stroke_width=3)
                         for i, j in GRAPH_EDGES])
        graph = VGroup(edges, nodes)

        def paint(coloring):
            return [nodes[k].animate.set_color(NODE_COLORS[c]) for k, c in enumerate(coloring)]

        with self.narrate("*P versus NP:* checking an answer is *fast.*") as t:
            self.play(FadeIn(graph, scale=0.8), *paint(ANSWER),
                      *self.label_anims("Check: No Same-Color Neighbors"), run_time=0.7)
            self.play(LaggedStart(*[e.animate.set_stroke(SOLVED, width=5) for e in edges], lag_ratio=0.12),
                      run_time=max(0.6, t.get_remaining_duration() - 0.3))
            self.play(*self.label_anims("Checked ✓", color=SOLVED, stroke=SOLVED), run_time=0.3)

        with self.narrate("But *finding* one can take *forever.*") as t:
            self.play(*[e.animate.set_stroke(MUTED, width=3) for e in edges],
                      *[n.animate.set_color(FG) for n in nodes], run_time=0.3)
            steps = [int(k) for k in np.linspace(0, len(COLORINGS) - 1, 9)]
            per = max(0.15, (t.get_remaining_duration() - 0.6) / len(steps))
            for k in steps:
                self.play(*paint(COLORINGS[k]), *self.label_anims(f"Tried {k + 1:,} of {len(COLORINGS):,}",
                                                                   color=ALARM, stroke=ALARM), run_time=per)
            self.play(*paint(ANSWER), *self.label_anims(f"100 Nodes: {OPTIONS_100} Options", color=ALARM,
                                                        stroke=ALARM), run_time=0.5)

        with self.narrate("If finding is secretly fast too, most *encryption* breaks.") as t:
            budget = t.get_remaining_duration()
            self.wait(budget * 0.45)
            self.play(*[e.animate.set_stroke(ALARM, width=5) for e in edges],
                      Wiggle(graph, scale_value=1.08, rotation_angle=0.04 * TAU),
                      *self.label_anims("Open · Encryption Depends On It", color=OPEN, stroke=OPEN), run_time=0.8)

        handoff(graph, phi=MINI_PHI)

        # ------------------------------------------------------------ 4. Hodge: loops built from simple pieces
        donut = glassy(Torus(major_radius=TOR_M, minor_radius=TOR_m, resolution=(14, 32)).move_to(C), PALETTE[2])
        around_hole, around_tube = torus_curve(1, 0, PALETTE[0], phase=PI / 2), torus_curve(0, 1, PALETTE[1])
        mixed = torus_curve(1, 1, EMPH)
        with self.narrate("*Hodge:* can every shape's hidden structure be built from *simple equations?* "
                          "It's a bridge between *algebra* and *geometry.*") as t:
            budget = t.get_remaining_duration()
            self.play(FadeIn(donut, scale=0.85), *self.label_anims("Hodge · Open", color=OPEN, stroke=OPEN), run_time=0.7)
            self.play(Create(around_hole), run_time=budget * 0.14)
            self.play(Create(around_tube), run_time=budget * 0.14)
            self.play(Create(mixed), around_hole.animate.set_stroke(opacity=0.35),
                      around_tube.animate.set_stroke(opacity=0.35), run_time=budget * 0.2)
            self.play(Rotate(VGroup(donut, around_hole, around_tube, mixed), angle=PI / 3, axis=RIGHT, about_point=C),
                      run_time=max(0.5, t.get_remaining_duration()))

        handoff(donut, around_hole, around_tube, mixed, phi=HUB_PHI)

        # ------------------------------------------------------------ 5. Yang-Mills: quarks on strings, then the gap
        qpos = [C + 1.6 * np.array([np.sin(k * TAU / 3), 0, np.cos(k * TAU / 3)]) for k in range(3)]
        quarks = VGroup(*[Sphere(center=p, radius=0.34, resolution=(12, 12)).set_color(PALETTE[c])
                          for p, c in zip(qpos, (0, 1, 4))])
        phase = ValueTracker(0)

        def gluon(p, q):
            d = q - p
            n = np.cross(d, UP)
            n = n / np.linalg.norm(n)
            return ParametricFunction(lambda s: p + d * s + n * 0.13 * np.sin(14 * PI * s - phase.get_value()),
                                      t_range=[0, 1], color=EMPH, stroke_width=4)

        strings = always_redraw(lambda: VGroup(*[gluon(qpos[i], qpos[(i + 1) % 3]) for i in range(3)]))
        e_scale, e_base = 1.45, -3.4
        ladder = VGroup()
        vac = Line([-1.3, e_base, 0], [1.3, e_base, 0], color=MUTED, stroke_width=5)
        ladder.add(vac, T("0", size=26, color=MUTED, weight="MEDIUM").next_to(vac, LEFT, buff=0.2))
        for k, (_, e) in enumerate(GLUEBALLS):
            y = e_base + e * e_scale
            ln = Line([-1.3, y, 0], [1.3, y, 0], color=PALETTE[1], stroke_width=5)
            tag = T(f"{e:.2f} GeV", size=24, color=MUTED, weight="MEDIUM")
            ladder.add(ln, tag.next_to(ln, LEFT if k == 1 else RIGHT, buff=0.2))   # 2.40/2.59 sit close: split sides
        gap_y1 = e_base + GLUEBALLS[0][1] * e_scale
        gap = Rectangle(width=2.6, height=gap_y1 - e_base - 0.1, stroke_width=0, fill_color=EMPH, fill_opacity=0.18)
        gap.move_to([0, (e_base + gap_y1) / 2, 0])
        gap_t = T("Mass Gap", size=30, color=EMPH).move_to(gap)
        pinned(ladder, gap, gap_t)
        with self.narrate("*Yang–Mills:* the math behind *particle physics.* "
                          "Prove it works, and that its force has a *mass gap.*") as t:
            budget = t.get_remaining_duration()
            self.play(FadeIn(quarks, scale=0.85), *self.label_anims("Yang–Mills · Open", color=OPEN, stroke=OPEN),
                      run_time=0.7)
            self.add(strings)
            self.play(phase.animate.set_value(6 * PI), run_time=budget * 0.4, rate_func=linear)
            strings.clear_updaters()
            self.play(FadeOut(quarks), FadeOut(strings), run_time=0.4)
            self.play(FadeIn(ladder, shift=UP * 0.3), run_time=0.5)
            self.play(FadeIn(gap), FadeIn(gap_t, scale=1.2), run_time=max(0.4, t.get_remaining_duration()))

        handoff(ladder, gap, gap_t)

        # ------------------------------------------------------------ 6. BSD: rational points and chord addition
        curve, axes = ec_curve(), ec_axes()
        p_dot = Dot(ec_xy(*map(float, CHORD_P)), radius=0.12, color=EMPH)
        q_dot = Dot(ec_xy(*map(float, CHORD_Q)), radius=0.12, color=EMPH)
        hit = ec_xy(float(CHORD_SUM[0]), float(-CHORD_SUM[1]))
        chord = Line(ec_xy(X_LO, 1) + LEFT * 0.1, ec_xy(X_HI, 1), color=EMPH, stroke_width=3)
        hit_dot = Dot(hit, radius=0.12, color=EMPH)
        sum_dot = Dot(ec_xy(float(CHORD_SUM[0]), float(CHORD_SUM[1])), radius=0.14, color=PALETTE[1])
        mirror = DashedLine(hit, sum_dot.get_center(), color=PALETTE[1], stroke_width=3)
        extra = VGroup(*[Dot(ec_xy(float(x), float(y)), radius=0.09, color=FG) for x, y in EXTRA_POINTS])
        eq = T("y² = x³ − x + 1", size=30, color=MUTED, weight="MEDIUM").move_to([SAFE_CENTER_X, 3.05, 0])
        ec_parts = (curve, axes, p_dot, q_dot, chord, hit_dot, sum_dot, mirror, extra, eq)
        pinned(*ec_parts)
        with self.narrate("*Birch and Swinnerton-Dyer:* how many *fraction* points sit on curves like this? "
                          "Curves like these help *secure* the internet.") as t:
            budget = t.get_remaining_duration()
            self.play(FadeIn(axes), Create(curve), FadeIn(eq),
                      *self.label_anims("Birch & Swinnerton-Dyer · Open", color=OPEN, stroke=OPEN),
                      run_time=budget * 0.22)
            self.play(FadeIn(p_dot, scale=2), FadeIn(q_dot, scale=2), run_time=budget * 0.1)
            self.play(Create(chord), run_time=budget * 0.12)
            self.play(FadeIn(hit_dot, scale=2), run_time=budget * 0.08)
            self.play(Create(mirror), FadeIn(sum_dot, scale=2.5), run_time=budget * 0.12)
            self.play(LaggedStart(*[FadeIn(d, scale=2) for d in extra], lag_ratio=0.2),
                      run_time=max(0.4, t.get_remaining_duration() - 0.6))
            self.play(curve.animate.set_stroke(EMPH), *self.label_anims("Open · Used In Cryptography", color=OPEN,
                                                                        stroke=OPEN), run_time=0.6)

        handoff(*ec_parts, phi=50 * DEGREES)

        # ------------------------------------------------------------ 7. Navier-Stokes: a tightening vortex
        rc = ValueTracker(0.9)
        th = V_TH.copy()
        swirl = VGroup(*[Dot(C, radius=0.065, color=PALETTE[4]) for _ in range(N_PARTICLES)])
        cold, hot = ManimColor(PALETTE[4]), ManimColor(ALARM)
        vmax0 = lamb_oseen_speed(1.12 * 0.9, 0.9)                          # peak speed at the start: color scale

        def advect(group, dt):
            core = rc.get_value() * FUNNEL
            speed = lamb_oseen_speed(V_R, core)
            th[:] += speed / V_R * dt
            for k, d in enumerate(group):
                d.move_to(C + np.array([V_R[k] * np.cos(th[k]), V_R[k] * np.sin(th[k]), V_Z[k]]))
                d.set_color(interpolate_color(cold, hot, min(1.0, speed[k] / (2.2 * vmax0))))

        advect(swirl, 0)
        with self.narrate("*Navier–Stokes* describes every *flow,* from weather to blood. "
                          "Can a swirl ever spin *infinitely fast?*") as t:
            self.play(FadeIn(swirl), *self.label_anims("Navier–Stokes"), run_time=0.7)
            swirl.add_updater(advect)
            self.play(rc.animate.set_value(0.22), run_time=t.get_remaining_duration(),
                      rate_func=rate_functions.ease_in_quad)

        with self.narrate("OpenAI claims a proof. It's still *being checked.*") as t:
            self.play(*self.label_anims("Claimed · Not Yet Verified", color=CLAIMED, stroke=CLAIMED), run_time=0.5)
        handoff(swirl)
        swirl.clear_updaters()

        # ------------------------------------------------------------ 8. Riemann: Z(t) and its zeros on one line
        p_axes, p_ticks, p_stairs, p_smooth, p_tags = prime_plot()
        pinned(p_axes, p_ticks, p_stairs, p_smooth, p_tags)
        with self.narrate("And the big one: the *Riemann hypothesis,* the hidden pattern of the *primes.*") as t:
            budget = t.get_remaining_duration()
            self.play(FadeIn(p_axes), *self.label_anims("Riemann · Primes Up To 100", color=EMPH, stroke=EMPH),
                      run_time=0.5)
            self.play(LaggedStart(*[FadeIn(k, shift=UP * 0.1) for k in p_ticks], lag_ratio=0.1),
                      Create(p_stairs), run_time=budget * 0.45, rate_func=linear)
            self.play(Create(p_smooth), FadeIn(p_tags), run_time=max(0.5, t.get_remaining_duration()))

        frame, wave, zeros = critical_strip()
        pinned(frame, wave, zeros)
        with self.narrate("Its zeros steer the primes, and they all seem to sit on *one line.*") as t:
            budget = t.get_remaining_duration()
            self.play(*[FadeOut(m) for m in (p_axes, p_ticks, p_stairs, p_smooth, p_tags)], run_time=0.5)
            self.play(FadeIn(frame), *self.label_anims("Riemann Hypothesis", color=EMPH, stroke=EMPH), run_time=0.5)
            self.play(Create(wave), run_time=budget * 0.4, rate_func=linear)
            self.play(LaggedStart(*[FadeIn(z, scale=2.5) for z in zeros], lag_ratio=0.15),
                      run_time=max(0.5, t.get_remaining_duration()))

        with self.narrate("This month, a mathematician at *Anthropic* posted a proof built with *Claude,* "
                          "checked by computer in *Lean.*") as t:
            budget = t.get_remaining_duration()
            self.wait(budget * 0.4)
            self.play(wave.animate.set_stroke(opacity=0.3),
                      LaggedStart(*[z.animate.set_color(EMPH).scale(1.3) for z in zeros], lag_ratio=0.08),
                      *self.label_anims("Claimed · Lean-Checked", color=CLAIMED, stroke=CLAIMED), run_time=1.0)

        handoff(frame, wave, zeros, phi=HUB_PHI)

        # ------------------------------------------------------------ 9. scoreboard: the race and the payout
        for i, c in FINAL_STATUS.items():
            colors[i] = c
        for i in range(7):
            orbs[i][0].set_color(colors[i]).set_opacity(1)
            orbs[i][1].set_color(colors[i]).set_opacity(0.16)
            names[i].set_opacity(1)
        open_ones = [PNP, HODGE, YM, BSD]
        with self.narrate("Google DeepMind and *Harmonic* are racing for the rest.") as t:
            self.play(FadeIn(ground), FadeIn(orbs), FadeIn(names),
                      *self.label_anims("4 Still Open", color=OPEN, stroke=OPEN), run_time=0.7)
            self.play(LaggedStart(*[Indicate(orbs[i], color=OPEN, scale_factor=1.4) for i in open_ones],
                                  lag_ratio=0.2), run_time=min(1.6, t.get_remaining_duration()))

        with self.narrate("But no checks yet: Clay waits at least *two years* before paying.") as t:
            self.play(*hub_style(lit=[NS, RH]), *self.label_anims("Prize Pending", color=EMPH, stroke=EMPH),
                      run_time=0.5)
            self.play(*[Indicate(orbs[i], color=EMPH, scale_factor=1.3) for i in (NS, RH)],
                      run_time=min(1.0, t.get_remaining_duration()))

        # ------------------------------------------------------------ 10. outro
        with self.narrate("Follow for more math, made *simple.*"):
            self.play(*hub_style(), *self.label_anims(None), run_time=0.5)
        self.wait(0.5)
