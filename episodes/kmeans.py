"""Episode: What is K-means clustering?  (narrated, ~45 s, vertical)

Render:  ./make.sh kmeans preview   (draft voice unless key set, 540x960)
         ./make.sh kmeans           (final, 1080x1920)
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
PLOT_CENTER = np.array([SAFE_CENTER_X, 0.6])
BLOBS = [(-1.9, 1.6), (1.5, 2.0), (-0.1, -1.6)]
K = 3
points = np.vstack([RNG.normal(loc=c, scale=0.55, size=(22, 2)) for c in BLOBS])
# Two centroids crammed in the middle: a bad start, converges in 4 rounds.
INIT = np.array([[-0.5, 0.4], [0.4, 0.6], [2.6, -2.4]])


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
    return np.array([xy[0] + PLOT_CENTER[0], xy[1] + PLOT_CENTER[1], 0])


def centroid_marker(color):
    return Star(n=5, outer_radius=0.32, inner_radius=0.14,
                fill_color=color, fill_opacity=1, stroke_color=WHITE, stroke_width=4)


# ---------------------------------------------------------------- scene
class KMeans(EpisodeScene):
    def construct(self):
        n = len(points)
        self.title_card("K-Means", "Clustering, Explained")
        dots = VGroup(*[Dot(to_scene(p), radius=0.09, color=FG) for p in points])

        # 1. hook
        with self.narrate("Here's a pile of data with no labels. "
                          "How does a computer find the groups on its own?",
                          caption_text="No labels. No answers.\nHow does a computer\nfind the groups?") as t:
            self.play(LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.02),
                      run_time=min(1.2, t.get_remaining_duration()))

        # 2. pick K + drop centroids
        with self.narrate("This is K-means. First, you pick K, the number of groups. Let's use three.",
                          caption_text="First, pick K:\nhow many groups.\nLet's use 3."):
            pass

        C0, labels0 = HISTORY[0]
        stars = VGroup(*[centroid_marker(PALETTE[k]).move_to(to_scene(C0[k])) for k in range(K)])
        with self.narrate("Then drop three centroids at random. Think of them as group centers.",
                          caption_text="Drop 3 centroids\nat random. They're\nthe group centers.") as t:
            self.play(LaggedStart(*[DrawBorderThenFill(s) for s in stars], lag_ratio=0.3),
                      run_time=min(1.5, t.get_remaining_duration()))

        # 3. assign, shown slowly once
        round_label = T("Round 1", size=30, color=MUTED, weight="NORMAL").move_to([SAFE_CENTER_X, TAG_Y - 0.65, 0])
        with self.narrate("Step one: assign. Every point joins whichever centroid is closest.",
                          caption_text="Step 1: Assign.\nEach point joins the\nclosest centroid.") as t:
            self.play(FadeOut(self._title[1]), *self.tag_anims("Step 1 · Assign"), FadeIn(round_label), run_time=0.4)
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
        with self.narrate("Step two: update. Each centroid moves to the average position of its points.",
                          caption_text="Step 2: Update.\nEach centroid moves\nto its points' average.") as t:
            self.set_tag("Step 2 · Update", color=PALETTE[1])
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
        with self.narrate("Then repeat. Assign, update. Assign, update.",
                          caption_text="Then repeat.\nAssign, update.\nAssign, update.") as t:
            steps = len(HISTORY) - 1
            per = t.get_remaining_duration() / max(1, 2 * steps - 1)
            for r in range(1, len(HISTORY)):
                C, labels = HISTORY[r]
                new_round = T(f"Round {r + 1}", size=30, color=MUTED, weight="NORMAL").move_to(round_label)
                self.play(*self.tag_anims("Step 1 · Assign"), FadeOut(round_label), FadeIn(new_round),
                          *[d.animate.set_color(PALETTE[labels[j]]) for j, d in enumerate(dots)],
                          run_time=per)
                round_label = new_round
                if r + 1 < len(HISTORY):
                    Cn, _ = HISTORY[r + 1]
                    self.play(*self.tag_anims("Step 2 · Update", PALETTE[1]),
                              *[stars[k].animate.move_to(to_scene(Cn[k])) for k in range(K)],
                              run_time=per)

        # 6. converged
        _, final = HISTORY[-1]
        hulls = VGroup(*[
            SurroundingRectangle(VGroup(*[dots[j] for j in range(n) if final[j] == k]),
                                 color=PALETTE[k], corner_radius=0.4, buff=0.2, stroke_width=3)
            for k in range(K)
        ])
        with self.narrate("When no point switches groups, it's converged. Those are your clusters.",
                          caption_text="No point switches?\nConverged. Those are\nyour clusters.") as t:
            self.set_tag("Converged", color=PALETTE[1])
            self.play(LaggedStart(*[Create(h) for h in hulls], lag_ratio=0.2),
                      *[Indicate(s, scale_factor=1.3, color=s.get_fill_color()) for s in stars],
                      run_time=min(1.4, t.get_remaining_duration()))

        # 7. recap loop
        a = pill("Assign", size=38)
        u = pill("Update", color=PALETTE[1], size=38)
        VGroup(a, u).arrange(RIGHT, buff=1.4).move_to([SAFE_CENTER_X, -0.7, 0])
        top_arc = CurvedArrow(a.get_top() + UP * 0.1, u.get_top() + UP * 0.1, angle=-PI / 2.2, color=FG)
        bot_arc = CurvedArrow(u.get_bottom() + DOWN * 0.1, a.get_bottom() + DOWN * 0.1, angle=-PI / 2.2, color=FG)
        with self.narrate("That's the whole algorithm. Two steps, on a loop, until nothing moves.",
                          caption_text="That's the whole\nalgorithm. Repeat\nuntil nothing moves.") as t:
            self.play(*self.tag_anims(None), FadeOut(round_label),
                      VGroup(dots, stars, hulls).animate.scale(0.55).shift(UP * 2.4).set_x(SAFE_CENTER_X), run_time=0.7)
            self.play(FadeIn(a, shift=UP * 0.2), FadeIn(u, shift=UP * 0.2), run_time=0.4)
            self.play(Create(top_arc), Create(bot_arc), run_time=min(0.9, t.get_remaining_duration()))

        with self.narrate("One catch: you choose K yourself, and a bad start can lead to a worse answer.",
                          caption_text="The catch: you pick K,\nand a bad start\ncan mislead it."):
            pass

        # 8. outro
        with self.narrate("Follow for more machine learning, explained in under a minute.",
                          caption_text="Follow for more ML\nin under a minute."):
            pass
        self.wait(0.5)
