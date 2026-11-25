"""Episode: What is K-means clustering?  (narrated, ~45 s, vertical, 3D)

Render:  ./make.sh kmeans silent    (no audio, no credits, 720p)
         ./make.sh kmeans           (ElevenLabs, 1080x1920)
"""
import sys
from pathlib import Path

import numpy as np
from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reelearn.scene import EpisodeScene  # noqa: E402
from reelearn.style import *  # noqa: E402,F403

# ---------------------------------------------------------------- data (3 features → 3D)
RNG = np.random.default_rng(11)
BLOBS = [(-2.0, 1.2, -0.8), (1.9, 1.0, 0.9), (0.0, -1.9, 0.4)]
K = 3
points = np.vstack([RNG.normal(loc=c, scale=0.55, size=(22, 3)) for c in BLOBS])
points -= (points.min(0) + points.max(0)) / 2          # center the cloud on the origin
# Two centroids crammed together near the middle, one far off: a bad start.
INIT = np.array([[-0.5, 0.6, 0.2], [0.4, 0.8, 0.0], [2.2, -2.0, -1.2]])

FLOOR_Z = -2.2
CAMERA = dict(phi=68 * DEGREES, theta=-55 * DEGREES, zoom=1.0,
              frame_center=OUT * 0.4)  # look slightly above the cloud so it sits just below center
ORBIT_RATE = 0.14  # rad/s: a slow orbit sells the depth


def run_kmeans(X, C, max_iter=10):
    """List of (centroids, labels) per round, ending when labels stop changing."""
    history, labels = [], None
    for _ in range(max_iter):
        new = np.linalg.norm(X[:, None] - C[None], axis=2).argmin(axis=1)
        history.append((C.copy(), new))
        if labels is not None and np.array_equal(new, labels):
            break
        labels = new
        C = np.array([X[labels == k].mean(0) if (labels == k).any() else C[k] for k in range(len(C))])
    return history


HISTORY = run_kmeans(points, INIT)
assert all((HISTORY[-1][1] == k).any() for k in range(K)), "a cluster ended empty: pick another INIT"


def point_dot(p):
    return Dot3D(p, radius=0.085, color=FG, resolution=(6, 6))


def centroid(p, color):
    core = Sphere(center=p, radius=0.2, resolution=(12, 12)).set_color(color)
    halo = Sphere(center=p, radius=0.38, resolution=(12, 12)).set_color(color).set_opacity(0.18)
    return VGroup(core, halo)


def floor():
    grid = NumberPlane(
        x_range=[-4, 4, 1], y_range=[-4, 4, 1],
        background_line_style={"stroke_color": FAINT, "stroke_width": 1.5, "stroke_opacity": 0.7},
        axis_config={"stroke_color": FAINT, "stroke_width": 2},
    )
    return grid.shift(OUT * FLOOR_Z)


# ---------------------------------------------------------------- scene
class KMeans(EpisodeScene):
    def construct(self):
        n = len(points)
        self.set_camera_orientation(**CAMERA)
        ground = floor()
        dots = VGroup(*[point_dot(p) for p in points])
        self.add(ground, dots)                      # on screen from frame 0
        self.begin_ambient_camera_rotation(rate=ORBIT_RATE)

        # 1. hook
        with self.narrate("Here's a pile of data with *no labels.* "
                          "How does a computer find the *groups* on its own?") as t:
            self.play(LaggedStart(*[Indicate(d, scale_factor=1.8, color=EMPH) for d in dots], lag_ratio=0.02),
                      run_time=min(2.2, t.get_remaining_duration()))

        # 2. pick K, drop centroids
        with self.narrate("This is *K-means.* First, you pick *K,* the number of groups. Let's use *three.*"):
            pass

        C0, labels0 = HISTORY[0]
        cents = VGroup(*[centroid(C0[k], PALETTE[k]) for k in range(K)])
        with self.narrate("Then drop three *centroids* at random. Think of them as group centers.") as t:
            self.play(LaggedStart(*[GrowFromCenter(c) for c in cents], lag_ratio=0.3),
                      run_time=min(1.5, t.get_remaining_duration()))

        # 3. assign, shown slowly once
        with self.narrate("Step one: *assign.* Every point joins whichever centroid is *closest.*") as t:
            self.set_label("Round 1 · Assign")
            i = int(np.argmin(np.linalg.norm(points - np.array([0.8, -0.6, 0.2]), axis=1)))
            demo = dots[i]
            lines = VGroup(*[DashedLine(points[i], C0[k], color=PALETTE[k], stroke_width=5, dash_length=0.14)
                             for k in range(K)])
            win = labels0[i]
            budget = t.get_remaining_duration()
            self.play(demo.animate.scale(2), LaggedStart(*[Create(l) for l in lines], lag_ratio=0.3),
                      run_time=budget * 0.25)
            self.play(*[l.animate.set_opacity(0.12) for k, l in enumerate(lines) if k != win],
                      lines[win].animate.set_stroke(width=8), demo.animate.set_color(PALETTE[win]),
                      run_time=budget * 0.2)
            self.play(FadeOut(lines), demo.animate.scale(0.5), run_time=budget * 0.1)
            self.play(LaggedStart(*[d.animate.set_color(PALETTE[labels0[j]]) for j, d in enumerate(dots)],
                                  lag_ratio=0.015), run_time=budget * 0.35)

        # 4. update, shown slowly once
        C1, _ = HISTORY[1]
        with self.narrate("Step two: *update.* Each centroid moves to the *average* of its points.") as t:
            self.set_label("Round 1 · Update", color=PALETTE[1], stroke=PALETTE[1])
            budget = t.get_remaining_duration()
            spokes = VGroup(*[Line(points[j], C0[labels0[j]], color=PALETTE[labels0[j]],
                                   stroke_width=2, stroke_opacity=0.5) for j in range(n)])
            self.play(Create(spokes), run_time=budget * 0.25)
            self.play(*[cents[k].animate.move_to(C1[k]) for k in range(K)],
                      *[spokes[j].animate.put_start_and_end_on(points[j], C1[labels0[j]]) for j in range(n)],
                      run_time=budget * 0.5)
            self.play(FadeOut(spokes), run_time=budget * 0.15)

        # 5. repeat quickly
        with self.narrate("Then *repeat.* Assign, update. Assign, update.") as t:
            steps = len(HISTORY) - 1
            per = t.get_remaining_duration() / max(1, 2 * steps - 1)
            for r in range(1, len(HISTORY)):
                C, labels = HISTORY[r]
                self.play(*self.label_anims(f"Round {r + 1} · Assign"),
                          *[d.animate.set_color(PALETTE[labels[j]]) for j, d in enumerate(dots)],
                          run_time=per)
                if r + 1 < len(HISTORY):
                    Cn, _ = HISTORY[r + 1]
                    self.play(*self.label_anims(f"Round {r + 1} · Update", color=PALETTE[1], stroke=PALETTE[1]),
                              *[cents[k].animate.move_to(Cn[k]) for k in range(K)],
                              run_time=per)

        # 6. converged: a translucent bubble around each cluster
        Cf, final = HISTORY[-1]
        bubbles = VGroup(*[
            Sphere(center=Cf[k], radius=np.percentile(np.linalg.norm(points[final == k] - Cf[k], axis=1), 80) + 0.15,
                   resolution=(16, 16)).set_color(PALETTE[k]).set_opacity(0.13)
            for k in range(K)
        ])
        with self.narrate("When no point switches groups, it's *converged.* Those are your *clusters.*") as t:
            self.set_label("Converged", color=PALETTE[1], stroke=PALETTE[1])
            self.play(LaggedStart(*[FadeIn(b, scale=0.6) for b in bubbles], lag_ratio=0.25),
                      run_time=min(1.6, t.get_remaining_duration()))

        # 7. recap loop (2D overlay under the shrunken 3D scene)
        a = badge("Assign", size=40, color=EMPH, stroke=EMPH)
        u = badge("Update", size=40, color=PALETTE[1], stroke=PALETTE[1])
        VGroup(a, u).arrange(RIGHT, buff=1.4).move_to([SAFE_CENTER_X, -3.3, 0])
        top_arc = CurvedArrow(a.get_top() + UP * 0.1, u.get_top() + UP * 0.1, angle=-PI / 2.2, color=MUTED)
        bot_arc = CurvedArrow(u.get_bottom() + DOWN * 0.1, a.get_bottom() + DOWN * 0.1, angle=-PI / 2.2, color=MUTED)
        self.overlay(a, u, top_arc, bot_arc)
        for m in (a, u, top_arc, bot_arc):
            self.remove(m)  # registered as overlays; revealed by the animations below
        with self.narrate("That's the whole algorithm. Two steps, on a *loop,* until nothing moves.") as t:
            self.play(*self.label_anims(None), FadeOut(ground),
                      VGroup(dots, cents, bubbles).animate.scale(0.62, about_point=ORIGIN).shift(OUT * 1.6),
                      run_time=0.8)
            self.play(FadeIn(a, shift=UP * 0.2), FadeIn(u, shift=UP * 0.2), run_time=0.4)
            self.play(Create(top_arc), Create(bot_arc), run_time=min(0.9, t.get_remaining_duration()))

        with self.narrate("One catch: *you* choose K, and a *bad start* can lead to a worse answer."):
            pass

        # 8. outro
        with self.narrate("Follow for more machine learning, explained in *under a minute.*"):
            pass
        self.wait(0.5)
