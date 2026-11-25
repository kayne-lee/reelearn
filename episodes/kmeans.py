"""Episode: What is K-means clustering?  (narrated, ~45 s, vertical)

Render:  ./make.sh kmeans draft     (free voice, check layout)
         ./make.sh kmeans           (ElevenLabs, 1080x1920)
"""
import sys
from pathlib import Path

import numpy as np
from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reelearn.scene import EpisodeScene  # noqa: E402
from reelearn.style import *  # noqa: E402,F403

# ---------------------------------------------------------------- data
RNG = np.random.default_rng(7)
BLOBS = [(-1.9, 1.6), (1.5, 2.0), (-0.1, -1.6)]
K = 3
points = np.vstack([RNG.normal(loc=c, scale=0.55, size=(22, 2)) for c in BLOBS])
# Two centroids crammed in the middle: a bad start, converges in 4 rounds.
INIT = np.array([[-0.5, 0.4], [0.4, 0.6], [2.6, -2.4]])
# Center the point cloud on the visual anchor.
OFFSET = np.array([SAFE_CENTER_X, VISUAL_Y]) - (points.min(0) + points.max(0)) / 2


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


def to_scene(xy):
    p = np.asarray(xy) + OFFSET
    return np.array([p[0], p[1], 0])


def centroid_marker(color):
    return Star(n=5, outer_radius=0.32, inner_radius=0.14,
                fill_color=color, fill_opacity=1, stroke_color=WHITE, stroke_width=4)


# ---------------------------------------------------------------- scene
class KMeans(EpisodeScene):
    def construct(self):
        n = len(points)
        dots = VGroup(*[Dot(to_scene(p), radius=0.09, color=FG) for p in points])
        self.add(dots)  # visible from frame 0: the hook needs something on screen

        # 1. hook
        with self.narrate("Here's a pile of data with *no labels.* "
                          "How does a computer find the *groups* on its own?") as t:
            self.play(LaggedStart(*[Indicate(d, scale_factor=1.6, color=FG) for d in dots], lag_ratio=0.02),
                      run_time=min(2.0, t.get_remaining_duration()))

        # 2. pick K, drop centroids
        with self.narrate("This is *K-means.* First, you pick *K,* the number of groups. Let's use *three.*"):
            pass

        C0, labels0 = HISTORY[0]
        stars = VGroup(*[centroid_marker(PALETTE[k]).move_to(to_scene(C0[k])) for k in range(K)])
        with self.narrate("Then drop three *centroids* at random. Think of them as group centers.") as t:
            self.play(LaggedStart(*[DrawBorderThenFill(s) for s in stars], lag_ratio=0.3),
                      run_time=min(1.5, t.get_remaining_duration()))

        # 3. assign, shown slowly once
        with self.narrate("Step one: *assign.* Every point joins whichever centroid is *closest.*") as t:
            self.set_label("Round 1 · Assign")
            i = int(np.argmin(np.linalg.norm(points - np.array([0.6, -1.2]), axis=1)))
            demo = dots[i]
            lines = VGroup(*[DashedLine(demo.get_center(), stars[k].get_center(), color=PALETTE[k],
                                        stroke_width=6, dash_length=0.14) for k in range(K)])
            win = labels0[i]
            budget = t.get_remaining_duration()
            self.play(demo.animate.scale(1.8), LaggedStart(*[Create(l) for l in lines], lag_ratio=0.3),
                      run_time=budget * 0.25)
            self.play(*[l.animate.set_opacity(0.15) for k, l in enumerate(lines) if k != win],
                      lines[win].animate.set_stroke(width=9), demo.animate.set_color(PALETTE[win]),
                      run_time=budget * 0.2)
            self.play(FadeOut(lines), demo.animate.scale(1 / 1.8), run_time=budget * 0.1)
            self.play(LaggedStart(*[d.animate.set_color(PALETTE[labels0[j]]) for j, d in enumerate(dots)],
                                  lag_ratio=0.015), run_time=budget * 0.35)

        # 4. update, shown slowly once
        C1, _ = HISTORY[1]
        with self.narrate("Step two: *update.* Each centroid moves to the *average* of its points.") as t:
            self.set_label("Round 1 · Update")
            budget = t.get_remaining_duration()
            spokes = VGroup(*[Line(dots[j].get_center(), stars[labels0[j]].get_center(),
                                   color=PALETTE[labels0[j]], stroke_width=2, stroke_opacity=0.45)
                              for j in range(n)])
            self.play(Create(spokes), run_time=budget * 0.25)
            self.play(*[stars[k].animate.move_to(to_scene(C1[k])) for k in range(K)],
                      *[spokes[j].animate.put_start_and_end_on(dots[j].get_center(), to_scene(C1[labels0[j]]))
                        for j in range(n)],
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
                    self.play(*self.label_anims(f"Round {r + 1} · Update"),
                              *[stars[k].animate.move_to(to_scene(Cn[k])) for k in range(K)],
                              run_time=per)

        # 6. converged
        _, final = HISTORY[-1]
        hulls = VGroup(*[
            SurroundingRectangle(VGroup(*[dots[j] for j in range(n) if final[j] == k]),
                                 color=PALETTE[k], corner_radius=0.4, buff=0.2, stroke_width=3)
            for k in range(K)
        ])
        with self.narrate("When no point switches groups, it's *converged.* Those are your *clusters.*") as t:
            self.set_label("Converged", color=PALETTE[1], stroke=PALETTE[1])
            self.play(LaggedStart(*[Create(h) for h in hulls], lag_ratio=0.2),
                      *[Indicate(s, scale_factor=1.3, color=s.get_fill_color()) for s in stars],
                      run_time=min(1.4, t.get_remaining_duration()))

        # 7. recap loop
        a = badge("Assign", size=40, stroke=FG)
        u = badge("Update", size=40, stroke=FG)
        VGroup(a, u).arrange(RIGHT, buff=1.4).move_to([SAFE_CENTER_X, -2.3, 0])
        top_arc = CurvedArrow(a.get_top() + UP * 0.1, u.get_top() + UP * 0.1, angle=-PI / 2.2, color=MUTED)
        bot_arc = CurvedArrow(u.get_bottom() + DOWN * 0.1, a.get_bottom() + DOWN * 0.1, angle=-PI / 2.2, color=MUTED)
        with self.narrate("That's the whole algorithm. Two steps, on a *loop,* until nothing moves.") as t:
            self.play(*self.label_anims(None),
                      VGroup(dots, stars, hulls).animate.scale(0.55).move_to([SAFE_CENTER_X, 1.2, 0]),
                      run_time=0.7)
            self.play(FadeIn(a, shift=UP * 0.2), FadeIn(u, shift=UP * 0.2), run_time=0.4)
            self.play(Create(top_arc), Create(bot_arc), run_time=min(0.9, t.get_remaining_duration()))

        with self.narrate("One catch: *you* choose K, and a *bad start* can lead to a worse answer."):
            pass

        # 8. outro
        with self.narrate("Follow for more machine learning, explained in *under a minute.*"):
            pass
        self.wait(0.5)
