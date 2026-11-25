"""Episode: EM (Gaussian mixtures) and why it beats K-means.  (narrated, ~55 s, vertical, 3D)

Render:  ./make.sh em silent    (no audio, no credits, 720p)
         ./make.sh em           (ElevenLabs, 1080x1920)
"""
import sys
from itertools import permutations
from pathlib import Path

import numpy as np
from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reelearn.scene import EpisodeScene  # noqa: E402
from reelearn.style import *  # noqa: E402,F403

# ---------------------------------------------------------------- data: two long parallel clusters + one small round one
R = np.random.default_rng(8)


def blob(c, sx, sy, ang, n):
    z = R.normal(size=(n, 2)) * [sx, sy]
    a = np.radians(ang)
    rot = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return z @ rot.T + c


X = np.vstack([blob((-1.0, 0.9), 1.55, 0.22, 35, 40),
               blob((1.0, -0.6), 1.55, 0.22, 35, 40),
               blob((1.9, 2.2), 0.3, 0.3, 0, 18)])
TRUTH = np.array([0] * 40 + [1] * 40 + [2] * 18)
X = (X - (X.min(0) + X.max(0)) / 2) * 0.72              # center and fit the frame
K = 3
INIT = np.array([[-1.1, 0.0], [1.1, 0.15], [1.1, 1.7]])


def kmeans(X, C, iters=50):
    for _ in range(iters):
        lab = np.linalg.norm(X[:, None] - C[None], axis=2).argmin(1)
        C = np.array([X[lab == k].mean(0) for k in range(len(C))])
    return C, lab


def gauss(X, m, S):
    d = X - m
    inv = np.linalg.inv(S)
    return np.exp(-0.5 * np.einsum("ni,ij,nj->n", d, inv, d)) / (2 * np.pi * np.sqrt(np.linalg.det(S)))


def em(X, M, iters=40):
    """Gaussian-mixture EM. Returns per-iteration (means, covariances, weights, responsibilities)."""
    S = np.array([np.eye(2) * 0.35] * len(M))
    pi = np.ones(len(M)) / len(M)
    hist = []
    for _ in range(iters):
        p = np.stack([pi[k] * gauss(X, M[k], S[k]) for k in range(len(M))], 1)
        r = p / p.sum(1, keepdims=True)                                  # E-step
        hist.append((M.copy(), S.copy(), pi.copy(), r))
        nk = r.sum(0)                                                    # M-step
        M = (r.T @ X) / nk[:, None]
        S = np.array([((r[:, k, None] * (X - M[k])).T @ (X - M[k])) / nk[k] + np.eye(2) * 1e-3 for k in range(len(M))])
        pi = nk / len(X)
    return hist


def accuracy(lab):
    return max(np.mean(np.array([p[v] for v in lab]) == TRUTH) for p in permutations(range(K)))


KM_C, KM_LAB = kmeans(X, INIT.copy())
HIST = em(X, INIT.copy())
EM_LAB = HIST[-1][3].argmax(1)
assert accuracy(KM_LAB) < 0.8 and accuracy(EM_LAB) > 0.95, (accuracy(KM_LAB), accuracy(EM_LAB))

# ---------------------------------------------------------------- visuals
CAMERA = dict(phi=44 * DEGREES, theta=-90 * DEGREES, zoom=1.15, frame_center=OUT * 0.2)
COLORS = [ManimColor(c) for c in PALETTE[:K]]


def p3(xy, z=0.0):
    return np.array([xy[0], xy[1], z])


def blend(weights):
    rgb = sum(w * c.to_rgb() for w, c in zip(weights, COLORS))
    return ManimColor(np.clip(rgb, 0, 1))


def ellipse(m, S, color, n_sigma=2.0):
    vals, vecs = np.linalg.eigh(S)
    axes = vecs * (n_sigma * np.sqrt(np.maximum(vals, 1e-6)))
    return ParametricFunction(lambda t: p3(m + axes @ np.array([np.cos(t), np.sin(t)]), 0.02),
                              t_range=[0, TAU], color=color, stroke_width=5)


def hill_height(m, S, w, xy, scale):
    # ^0.6 compresses the range so a tight cluster doesn't dwarf the stretched ones
    return scale * (w * gauss(np.atleast_2d(xy), m, S)[0]) ** 0.6


def hill(m, S, w, color, scale, n_sigma=2.6):
    """Probability hill on an elliptical footprint (fades to the floor at its rim)."""
    vals, vecs = np.linalg.eigh(S)
    axes = vecs * np.sqrt(np.maximum(vals, 1e-6))

    def point(u, v):  # u: radius in sigmas, v: angle
        xy = m + axes @ np.array([u * np.cos(v), u * np.sin(v)])
        return p3(xy, hill_height(m, S, w, xy, scale))

    return Surface(point, u_range=[0, n_sigma], v_range=[0, TAU], resolution=(12, 28),
                   fill_color=color, fill_opacity=0.6, stroke_color=color, stroke_width=0.5, stroke_opacity=0.7,
                   checkerboard_colors=False)


class EM(EpisodeScene):
    def construct(self):
        n = len(X)
        self.set_camera_orientation(**CAMERA)
        grid = NumberPlane(x_range=[-4, 4, 1], y_range=[-4, 4, 1],
                           background_line_style={"stroke_color": FAINT, "stroke_width": 1.5, "stroke_opacity": 0.6},
                           axis_config={"stroke_color": FAINT, "stroke_width": 2})
        dots = VGroup(*[Dot3D(p3(x), radius=0.075, color=FG, resolution=(6, 6)) for x in X])
        self.add(grid, dots)
        self.begin_camera_sway(amplitude=8 * DEGREES, period=16)

        # 1-2. K-means' blind spot
        with self.narrate("K-means has a *blind spot.* It thinks every cluster is a *round ball.*") as t:
            self.set_label("K-means", color=PALETTE[0], stroke=PALETTE[0])
            rings = VGroup(*[Circle(radius=np.percentile(np.linalg.norm(X[KM_LAB == k] - KM_C[k], axis=1), 85),
                                    color=COLORS[k], stroke_width=5).move_to(p3(KM_C[k], 0.02)) for k in range(K)])
            self.play(*[d.animate.set_color(COLORS[KM_LAB[j]]) for j, d in enumerate(dots)],
                      run_time=min(1.2, t.get_remaining_duration()))
            self.play(LaggedStart(*[Create(r) for r in rings], lag_ratio=0.25),
                      run_time=min(1.2, t.get_remaining_duration()))

        with self.narrate("Give it *stretched* groups like these, and it slices them in the *wrong places.*") as t:
            wrong = [j for j in range(n) if KM_LAB[j] != TRUTH[j]]  # cluster ids line up with INIT order
            self.play(LaggedStart(*[Indicate(dots[j], scale_factor=2.2, color=WHITE) for j in wrong], lag_ratio=0.03),
                      *self.label_anims(f"K-means: {accuracy(KM_LAB):.0%} right", color=PALETTE[0], stroke=PALETTE[0]),
                      run_time=min(2.0, t.get_remaining_duration()))

        # 3-4. enter EM: blobs with shape
        M0, S0, _, R0 = HIST[0]
        ells = VGroup(*[ellipse(M0[k], S0[k], COLORS[k]) for k in range(K)])
        with self.narrate("Enter *EM,* short for Expectation-Maximization.") as t:
            self.play(FadeOut(rings), *[d.animate.set_color(FG) for d in dots],
                      *self.label_anims("EM", color=EMPH, stroke=EMPH), run_time=min(1.0, t.get_remaining_duration()))

        with self.narrate("Each cluster becomes a *blob* with a center, a *shape,* and a size.") as t:
            self.play(LaggedStart(*[Create(e) for e in ells], lag_ratio=0.25),
                      run_time=min(1.5, t.get_remaining_duration()))

        # 5. E-step: soft blends
        with self.narrate("Step one, *expectation:* every point gets a *probability* for each blob. "
                          "Not a hard choice, a *blend.*") as t:
            self.set_label("Step 1 · Expectation", color=EMPH, stroke=EMPH)
            self.play(LaggedStart(*[d.animate.set_color(blend(R0[j])) for j, d in enumerate(dots)], lag_ratio=0.01),
                      run_time=min(2.0, t.get_remaining_duration()))

        # 6. M-step: blobs reshape
        M1, S1, _, R1 = HIST[1]
        with self.narrate("Step two, *maximization:* each blob *stretches* and moves to fit the points that belong to it.") as t:
            self.set_label("Step 2 · Maximization", color=PALETTE[1], stroke=PALETTE[1])
            self.play(*[Transform(ells[k], ellipse(M1[k], S1[k], COLORS[k])) for k in range(K)],
                      run_time=min(2.0, t.get_remaining_duration()))

        # 7. repeat until locked on
        steps = [2, 3, 5, 8, 12, 18, 26, len(HIST) - 1]
        with self.narrate("Repeat, and the blobs lock onto the *real* shapes.") as t:
            per = t.get_remaining_duration() / len(steps)
            for i in steps:
                M, S, _, Rr = HIST[i]
                self.play(*[Transform(ells[k], ellipse(M[k], S[k], COLORS[k])) for k in range(K)],
                          *[d.animate.set_color(blend(Rr[j])) for j, d in enumerate(dots)],
                          *self.label_anims(f"Round {i}", color=EMPH, stroke=EMPH), run_time=per)
            self.set_label(f"EM: {accuracy(EM_LAB):.0%} right", color=PALETTE[1], stroke=PALETTE[1])

        # 8. probability hills
        Mf, Sf, pif, _ = HIST[-1]
        peak = max(hill_height(Mf[k], Sf[k], pif[k], Mf[k], 1.0) for k in range(K))
        hills = [hill(Mf[k], Sf[k], pif[k], COLORS[k], scale=1.8 / peak) for k in range(K)]
        flats = [h.copy().stretch(0.01, 2, about_point=ORIGIN) for h in hills]
        with self.narrate("Stack those blobs up, and you get a *map of probability.*") as t:
            self.stop_ambient_camera_rotation()
            self.play(*self.label_anims(None), FadeOut(ells), run_time=0.4)
            self.add(*flats)
            self.play(*[Transform(f, h) for f, h in zip(flats, hills)],
                      self.camera.phi_tracker.animate.set_value(64 * DEGREES),
                      run_time=min(2.2, t.get_remaining_duration()))
        self.begin_ambient_camera_rotation(rate=0.18)

        # 9-10. why it's better, and the catch
        with self.narrate("So EM handles *stretched* clusters, different sizes, and tells you how *confident* it is."):
            pass
        with self.narrate("The catch: it's *slower,* and you still pick *K.*"):
            pass

        # 11. outro (same line as K-means: already voiced, free)
        with self.narrate("Follow for more machine learning, explained in *under a minute.*"):
            pass
        self.wait(0.5)
