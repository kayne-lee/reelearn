"""Episode: e-means, Meta's faster K-means.  (narrated, ~45 s, vertical, 3D)

Paper: "e-means: outperforming k-means (in one-tenth the epochs)", Meta FAIR, arXiv:2611.09501 (Nov 2026),
shipped in Faiss 1.16.0. The headline numbers in the narration (25 Lloyd epochs beaten in ~1.4-2.6 epochs,
10-45x GPU speedup, 10B embeddings into ~16M clusters) are the paper's. The animation itself is a real
run of both algorithms on the toy cloud below.

Render:  ./make.sh e_means silent    (no audio, no credits, 720p)
         ./make.sh e_means           (ElevenLabs, 1080x1920)
"""
import sys
from pathlib import Path

import numpy as np
from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reelearn.scene import EpisodeScene  # noqa: E402
from reelearn.style import *  # noqa: E402,F403

# ---------------------------------------------------------------- data (3 features → 3D)
RNG = np.random.default_rng(5)
BLOBS = [(-2.0, 1.3, -0.6), (1.9, 1.4, 0.8), (0.1, -1.9, 0.5), (2.0, -1.2, -0.9), (-1.9, -1.0, 1.0)]
K = len(BLOBS)
points = np.vstack([RNG.normal(loc=c, scale=0.42, size=(30, 3)) for c in BLOBS])
points -= (points.min(0) + points.max(0)) / 2
N = len(points)


def kmeans_pp(seed):
    """Standard k-means++ seeding (both algorithms start from the same centroids)."""
    r = np.random.default_rng(seed)
    C = [points[r.integers(N)]]
    for _ in range(K - 1):
        d = np.min(np.linalg.norm(points[:, None] - np.array(C)[None], axis=2), axis=1) ** 2
        C.append(points[r.choice(N, p=d / d.sum())])
    return np.array(C)


INIT = kmeans_pp(8)


def nearest(X, C):
    return np.linalg.norm(X[:, None] - C[None], axis=2).argmin(1)


def loss(C):
    return np.mean(np.min(np.linalg.norm(points[:, None] - C[None], axis=2), axis=1) ** 2)


def lloyd(C, epochs):
    """Classic K-means: one centroid update per full pass over the data."""
    hist = [C.copy()]
    for _ in range(epochs):
        lab = nearest(points, C)
        C = np.array([points[lab == k].mean(0) if (lab == k).any() else C[k] for k in range(K)])
        hist.append(C.copy())
    return hist


BATCH = 15                   # 10 batches = 1 pass over the data
EPOCHS_E = 3
ALPHA0 = 0.35


def e_means(C, seed=1):
    """e-means: after every mini-batch, centroids move toward a running (exponential moving) average.
    S_j <- (1-a) S_j + a s_j,  N_j <- (1-a) N_j + a n_j,  centroid_j = S_j / N_j,
    with the step a on a cosine schedule from ALPHA0 down to 0.1 * ALPHA0."""
    rng = np.random.default_rng(seed)
    steps = EPOCHS_E * N // BATCH
    Nj = np.full(K, BATCH / K)
    Sj = C * Nj[:, None]
    hist, batches = [C.copy()], []
    for t in range(steps):
        a = 0.1 * ALPHA0 + 0.9 * ALPHA0 * 0.5 * (1 + np.cos(np.pi * t / steps))
        idx = rng.choice(N, BATCH, replace=False)
        lab = nearest(points[idx], C)
        s = np.array([points[idx][lab == k].sum(0) for k in range(K)])
        n = np.bincount(lab, minlength=K)
        Sj = (1 - a) * Sj + a * s
        Nj = (1 - a) * Nj + a * n
        C = Sj / Nj[:, None]
        hist.append(C.copy())
        batches.append(idx)
    return hist, batches


L_HIST = lloyd(INIT, 25)
E_HIST, E_BATCHES = e_means(INIT)
FINAL = nearest(points, E_HIST[-1])
# the toy run should land where 25 full passes of K-means land (the paper's claim, in miniature)
assert loss(E_HIST[-1]) < 1.02 * loss(L_HIST[-1]), (loss(E_HIST[-1]), loss(L_HIST[-1]))
assert loss(E_HIST[N // BATCH]) < loss(L_HIST[1])      # after one pass, e-means is already ahead
assert sorted(np.bincount(FINAL)) == [29, 30, 30, 30, 31]

CAMERA = dict(phi=68 * DEGREES, theta=-55 * DEGREES, zoom=1.0, frame_center=OUT * 0.4)
ORBIT_RATE = 0.12
BATCH_GLOW = EMPH
ORANGE = PALETTE[3]
TEAL = PALETTE[1]


def point_dot(p):
    return Dot3D(p, radius=0.075, color=FG, resolution=(5, 5))


def centroid(p, color):
    core = Sphere(center=p, radius=0.18, resolution=(10, 10)).set_color(color)
    halo = Sphere(center=p, radius=0.34, resolution=(10, 10)).set_color(color).set_opacity(0.18)
    return VGroup(core, halo)


def floor():
    grid = NumberPlane(x_range=[-4, 4, 1], y_range=[-4, 4, 1],
                       background_line_style={"stroke_color": FAINT, "stroke_width": 1.5, "stroke_opacity": 0.7},
                       axis_config={"stroke_color": FAINT, "stroke_width": 2})
    return grid.shift(OUT * -2.0)


def bar_row(name, passes, color, scale=0.17):
    title = T(name, size=34, color=color, weight="MEDIUM")
    bar = Rectangle(width=max(passes * scale, 0.12), height=0.34, stroke_width=0, fill_color=color, fill_opacity=0.9)
    value = T(f"{passes} Passes" if passes > 2 else "~2 Passes", size=30, color=FG, weight="MEDIUM")
    title.next_to(ORIGIN, RIGHT, buff=0).align_to(LEFT * 2.5 + 0 * UP, LEFT)
    bar.next_to(title, DOWN, buff=0.12).align_to(title, LEFT)
    value.next_to(bar, RIGHT, buff=0.2)
    return VGroup(title, bar, value)


# ---------------------------------------------------------------- scene
class EMeans(EpisodeScene):
    def construct(self):
        self.set_camera_orientation(**CAMERA)
        ground = floor()
        dots = VGroup(*[point_dot(p) for p in points])
        cents = VGroup(*[centroid(INIT[k], PALETTE[k]) for k in range(K)])
        self.add(ground, dots, cents)               # on screen from frame 0
        self.begin_ambient_camera_rotation(rate=ORBIT_RATE)

        def run_batches(start, stop, per):
            """Animate e-means batches [start, stop): the batch lights up, the centroids nudge."""
            prev = []
            for b in range(start, stop):
                idx = E_BATCHES[b]
                C = E_HIST[b + 1]
                self.play(*[dots[j].animate.set_color(FG) for j in prev if j not in idx],
                          *[dots[j].animate.set_color(BATCH_GLOW) for j in idx],
                          *[cents[k].animate.move_to(C[k]) for k in range(K)], run_time=per)
                prev = list(idx)
            return prev

        def reset(run_time=0.5):
            self.play(*[d.animate.set_color(FG) for d in dots],
                      *[cents[k].animate.move_to(INIT[k]) for k in range(K)], run_time=run_time)

        # 1. hook: e-means already racing from frame 0
        with self.narrate("Meta just made K-means up to *ten times* faster. The trick is surprisingly simple.") as t:
            self.set_label("e-means", color=EMPH, stroke=EMPH, run_time=0.2)
            n_hook = 14
            last = run_batches(0, n_hook, max(0.1, (t.get_remaining_duration() - 0.6) / n_hook))
        reset(0.4)

        # 2. Lloyd: one full sweep per move
        with self.narrate("Classic K-means checks *every single point* before moving the centroids *once.*") as t:
            self.set_label("K-means · Pass 1", color=TEAL, stroke=TEAL, run_time=0.2)
            budget = t.get_remaining_duration()
            self.play(LaggedStart(*[d.animate.set_color(TEAL) for d in dots], lag_ratio=0.006),
                      run_time=budget * 0.55)
            self.play(*[cents[k].animate.move_to(L_HIST[1][k]) for k in range(K)],
                      *[d.animate.set_color(FG) for d in dots], run_time=min(0.8, t.get_remaining_duration()))

        # 3. that's slow at scale
        with self.narrate("With *billions* of points, one pass is slow. The usual setup runs *twenty-five.*") as t:
            per = t.get_remaining_duration() * 0.6 / 4
            for e in range(2, 6):
                self.play(*[cents[k].animate.move_to(L_HIST[e][k]) for k in range(K)],
                          *self.label_anims(f"K-means · Pass {e}", color=TEAL, stroke=TEAL), run_time=per)
            self.play(*self.label_anims("K-means · 25 Passes", color=TEAL, stroke=TEAL), run_time=0.3)
        reset(0.4)

        # 4-5. e-means: small batches, running average
        with self.narrate("*e-means* moves the centroids after every *small batch* instead.") as t:
            self.set_label("e-means · Small Batches", color=EMPH, stroke=EMPH, run_time=0.2)
            n4 = 8
            last = run_batches(0, n4, t.get_remaining_duration() / n4)

        with self.narrate("Each batch gives a small *nudge,* and older batches *fade out,* like a running average.") as t:
            self.set_label("Running Average", color=EMPH, stroke=EMPH, run_time=0.2)
            rest = len(E_BATCHES) - n4
            per = max(1 / 15, (t.get_remaining_duration() - 0.8) / rest)
            last = run_batches(n4, len(E_BATCHES), per)
            self.play(*[d.animate.set_color(PALETTE[FINAL[j]]) for j, d in enumerate(dots)],
                      *self.label_anims(f"e-means · {EPOCHS_E} Passes", color=EMPH, stroke=EMPH),
                      run_time=min(0.6, max(0.2, t.get_remaining_duration())))

        # 6. settings are automatic
        ins = VGroup(*[badge(s, size=28, color=MUTED, stroke=FAINT) for s in ("Data Size", "K", "Time Budget")]
                     ).arrange(RIGHT, buff=0.25)
        outs = VGroup(*[badge(s, size=30, color=EMPH, stroke=EMPH) for s in ("Batch Size", "Step Size")]
                      ).arrange(RIGHT, buff=0.3)
        arrow = Arrow(UP * 0.35, DOWN * 0.35, color=MUTED, stroke_width=5, buff=0, max_tip_length_to_length_ratio=0.4)
        chips = VGroup(ins, arrow, outs).arrange(DOWN, buff=0.18).move_to([SAFE_CENTER_X, -3.3, 0])
        self.overlay(chips)
        self.remove(chips)
        with self.narrate("Batch size and step size are set *automatically* from data size, K, and your time budget.") as t:
            self.play(*self.label_anims(None), FadeOut(ground),
                      VGroup(dots, cents).animate.scale(0.62, about_point=ORIGIN).shift(OUT * 1.6), run_time=0.8)
            self.play(FadeIn(ins, shift=UP * 0.2), run_time=0.4)
            self.play(GrowArrow(arrow), FadeIn(outs, shift=DOWN * 0.2),
                      run_time=min(0.8, max(0.2, t.get_remaining_duration())))

        # 7. the paper's headline result
        rows = VGroup(bar_row("K-means", 25, TEAL), bar_row("e-means", 2, EMPH)).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        rows.move_to([SAFE_CENTER_X, -3.0, 0])
        self.overlay(rows)
        self.remove(rows)
        with self.narrate("The result: it beats *twenty-five* passes of K-means in about *two.*") as t:
            self.play(FadeOut(chips), run_time=0.3)
            self.play(FadeIn(rows[0][0]), GrowFromEdge(rows[0][1], LEFT), FadeIn(rows[0][2]), run_time=0.7)
            self.wait(max(0, t.get_remaining_duration() * 0.35))
            self.play(FadeIn(rows[1][0]), GrowFromEdge(rows[1][1], LEFT), FadeIn(rows[1][2]),
                      run_time=min(0.5, max(0.2, t.get_remaining_duration())))
            self.set_label("Meta FAIR · 2026 Paper", color=MUTED, stroke=FAINT)

        # 8. GPU speed
        big = T("10–45×", size=110, color=EMPH).move_to([SAFE_CENTER_X, -2.5, 0])
        sub = T("Faster on GPUs", size=36, color=MUTED, weight="MEDIUM").next_to(big, DOWN, buff=0.2)
        speed = VGroup(big, sub)
        self.overlay(speed)
        self.remove(speed)
        with self.narrate("On GPUs, that's *ten to forty-five times* faster.") as t:
            self.play(FadeOut(rows), FadeIn(speed, scale=0.8), run_time=min(0.6, t.get_remaining_duration()))

        # 9. scale
        top = T("10 Billion", size=72, color=FG)
        mid = T("Embeddings ↓", size=30, color=MUTED, weight="MEDIUM")
        bot = T("16 Million Clusters", size=50, color=EMPH)
        scale_card = VGroup(top, mid, bot).arrange(DOWN, buff=0.15).move_to([SAFE_CENTER_X, -2.7, 0])
        self.overlay(scale_card)
        self.remove(scale_card)
        with self.narrate("Meta used it to sort *ten billion* embeddings into *sixteen million* clusters.") as t:
            budget = t.get_remaining_duration()
            self.play(FadeOut(speed), FadeIn(top, shift=UP * 0.2), FadeIn(mid), run_time=0.5)
            self.wait(max(0, budget * 0.4))
            self.play(FadeIn(bot, shift=UP * 0.2), run_time=min(0.5, max(0.2, t.get_remaining_duration())))

        # 10. where to get it
        faiss = badge("Faiss 1.16", size=56, color=EMPH, stroke=EMPH).move_to([SAFE_CENTER_X, -2.7, 0])
        self.overlay(faiss)
        self.remove(faiss)
        with self.narrate("It's already in Meta's *Faiss* library.") as t:
            self.play(FadeOut(scale_card), FadeIn(faiss, scale=0.8), *self.label_anims(None),
                      run_time=min(0.6, t.get_remaining_duration()))

        # 11. outro
        with self.narrate("Follow for more machine learning, explained in *under a minute.*"):
            pass
        self.wait(0.5)
