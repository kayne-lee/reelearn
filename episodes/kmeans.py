"""Episode: What is K-means clustering?  (~45 s, vertical)

Render:  ./make.sh kmeans          (high quality)
         ./make.sh kmeans -ql      (fast preview)
"""
import sys
from pathlib import Path

import numpy as np
from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reelearn.style import *  # noqa: E402,F403

# ---------------------------------------------------------------- data
RNG = np.random.default_rng(7)
PLOT_CENTER = np.array([SAFE_CENTER_X, 0.6])
BLOBS = [(-1.9, 1.6), (1.5, 2.0), (-0.1, -1.6)]
N_PER = 22
K = 3

points = np.vstack([
    RNG.normal(loc=c, scale=0.55, size=(N_PER, 2)) for c in BLOBS
])
# A deliberately bad start so the algorithm has to work for it
INIT = np.array([[-0.5, 0.4], [0.4, 0.6], [2.6, -2.4]])


def run_kmeans(X, C, max_iter=10):
    """Returns list of (centroids, labels) per iteration, ending at convergence."""
    history = []
    labels = None
    for _ in range(max_iter):
        d = np.linalg.norm(X[:, None, :] - C[None, :, :], axis=2)
        new_labels = d.argmin(axis=1)
        history.append((C.copy(), new_labels))
        if labels is not None and np.array_equal(new_labels, labels):
            break
        labels = new_labels
        # keep a centroid where it is if it loses all its points
        C = np.array([X[labels == k].mean(axis=0) if (labels == k).any() else C[k]
                      for k in range(len(C))])
    return history


HISTORY = run_kmeans(points, INIT)


def to_scene(xy):
    return np.array([xy[0] + PLOT_CENTER[0], xy[1] + PLOT_CENTER[1], 0])


def centroid_marker(color):
    star = Star(n=5, outer_radius=0.32, inner_radius=0.14,
                fill_color=color, fill_opacity=1, stroke_color=WHITE, stroke_width=4)
    return star


class KMeans(Scene):
    def construct(self):
        cap = VMobject()  # current caption
        step_tag = None

        def say(text, run_time=0.6, **kw):
            nonlocal cap
            new = caption(text, **kw)
            if len(cap.submobjects) or cap.has_points():
                self.play(FadeOut(cap, shift=UP * 0.3), FadeIn(new, shift=UP * 0.3), run_time=run_time)
            else:
                self.play(FadeIn(new, shift=UP * 0.3), run_time=run_time)
            cap = new

        def swap_anims(new_tag):
            nonlocal step_tag
            new_tag = new_tag.copy().move_to(step_tag)
            old, step_tag = step_tag, new_tag
            return [FadeOut(old, scale=0.9), FadeIn(new_tag, scale=1.1)]

        def swap_tag(new_tag):
            self.play(*swap_anims(new_tag), run_time=0.4)

        # ---------------------------------------------------- 1. hook
        title = T("K-MEANS", size=96, color=ACCENT).move_to([SAFE_CENTER_X, TITLE_Y, 0])
        subtitle = T("clustering, explained", size=36, color=MUTED, weight="NORMAL")
        subtitle.next_to(title, DOWN, buff=0.2)

        dots = VGroup(*[
            Dot(to_scene(p), radius=0.09, color=FG) for p in points
        ])
        self.add(title, subtitle)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.02), run_time=1.0)
        say("No labels. No answers.\nHow does a computer\nfind the groups?")
        self.wait(1.8)

        # ---------------------------------------------------- 2. pick K
        say("First, pick K: how many\ngroups you want. Say, 3.")
        self.wait(0.8)

        C0, _ = HISTORY[0]
        stars = VGroup(*[centroid_marker(PALETTE[k]).move_to(to_scene(C0[k])) for k in range(K)])
        self.play(LaggedStart(*[DrawBorderThenFill(s) for s in stars], lag_ratio=0.25), run_time=1.0)
        say("Drop 3 \"centroids\" at random.")
        self.wait(1.0)

        step_tag = pill("1 · ASSIGN").move_to([SAFE_CENTER_X, 5.0, 0])
        iter_tag = T("round 1", size=30, color=MUTED, weight="NORMAL").next_to(step_tag, DOWN, buff=0.15)
        self.play(FadeOut(subtitle), FadeIn(step_tag, scale=0.8), FadeIn(iter_tag), run_time=0.5)

        # ---------------------------------------------------- 3. assign (explained once, slowly)
        say("Each point joins the\nclosest centroid.")
        _, labels0 = HISTORY[0]
        demo_i = int(np.argmin(np.linalg.norm(points - np.array([0.6, -1.2]), axis=1)))
        demo = dots[demo_i]
        lines = VGroup(*[
            DashedLine(demo.get_center(), stars[k].get_center(), color=PALETTE[k],
                       stroke_width=6, dash_length=0.14)
            for k in range(K)
        ])
        self.play(demo.animate.scale(1.8), LaggedStart(*[Create(l) for l in lines], lag_ratio=0.3), run_time=1.0)
        win = labels0[demo_i]
        self.play(
            *[l.animate.set_opacity(0.15) for k, l in enumerate(lines) if k != win],
            lines[win].animate.set_stroke(width=8),
            demo.animate.set_color(PALETTE[win]),
            run_time=0.6,
        )
        self.wait(0.6)
        self.play(FadeOut(lines), demo.animate.scale(1 / 1.8), run_time=0.4)
        self.play(
            LaggedStart(*[d.animate.set_color(PALETTE[labels0[i]]) for i, d in enumerate(dots)], lag_ratio=0.015),
            run_time=1.2,
        )
        self.wait(0.4)

        # ---------------------------------------------------- 4. update (explained once)
        update_tag = pill("2 · UPDATE", color=PALETTE[1]).move_to(step_tag)
        swap_tag(update_tag)
        say("Each centroid moves to the\naverage of its points.")
        C1, _ = HISTORY[1]
        spokes = VGroup(*[
            Line(dots[i].get_center(), stars[labels0[i]].get_center(),
                 color=PALETTE[labels0[i]], stroke_width=2, stroke_opacity=0.45)
            for i in range(len(points))
        ])
        self.play(Create(spokes), run_time=0.7)
        self.play(
            *[stars[k].animate.move_to(to_scene(C1[k])) for k in range(K)],
            *[spokes[i].animate.put_start_and_end_on(dots[i].get_center(), to_scene(C1[labels0[i]]))
              for i in range(len(points))],
            run_time=1.4,
        )
        self.play(FadeOut(spokes), run_time=0.4)
        self.wait(0.3)

        # ---------------------------------------------------- 5. repeat quickly
        say("Now repeat. Assign, update,\nassign, update...")
        assign_tag = pill("1 · ASSIGN")
        update_tag = pill("2 · UPDATE", color=PALETTE[1])
        for r in range(1, len(HISTORY)):
            C, labels = HISTORY[r]
            new_iter = T(f"round {r + 1}", size=30, color=MUTED, weight="NORMAL").move_to(iter_tag)
            self.play(
                *swap_anims(assign_tag),
                FadeOut(iter_tag), FadeIn(new_iter),
                *[d.animate.set_color(PALETTE[labels[i]]) for i, d in enumerate(dots)],
                run_time=0.6,
            )
            iter_tag = new_iter
            if r + 1 < len(HISTORY):
                Cn, _ = HISTORY[r + 1]
                self.play(
                    *swap_anims(update_tag),
                    *[stars[k].animate.move_to(to_scene(Cn[k])) for k in range(K)],
                    run_time=0.8,
                )

        # ---------------------------------------------------- 6. converged
        done_tag = pill("CONVERGED", color=PALETTE[1]).move_to(step_tag)
        swap_tag(done_tag)
        say("Nobody switches teams?\nDone. You found the clusters.")
        hulls = VGroup()
        _, final = HISTORY[-1]
        for k in range(K):
            members = VGroup(*[dots[i] for i in range(len(points)) if final[i] == k])
            hulls.add(SurroundingRectangle(members, color=PALETTE[k], corner_radius=0.4,
                                           buff=0.2, stroke_width=3))
        self.play(LaggedStart(*[Create(h) for h in hulls], lag_ratio=0.2),
                  *[Indicate(s, scale_factor=1.3, color=s.get_fill_color()) for s in stars],
                  run_time=1.2)
        self.wait(1.4)

        # ---------------------------------------------------- 7. recap loop
        plot = VGroup(dots, stars, hulls)
        self.play(FadeOut(step_tag), FadeOut(iter_tag), plot.animate.scale(0.55).shift(UP * 1.9), run_time=0.8)

        a = pill("ASSIGN", size=38)
        u = pill("UPDATE", color=PALETTE[1], size=38)
        VGroup(a, u).arrange(RIGHT, buff=1.4).move_to([SAFE_CENTER_X, -1.3, 0])
        top_arc = CurvedArrow(a.get_top() + UP * 0.1, u.get_top() + UP * 0.1, angle=-PI / 2.2, color=FG)
        bot_arc = CurvedArrow(u.get_bottom() + DOWN * 0.1, a.get_bottom() + DOWN * 0.1, angle=-PI / 2.2, color=FG)
        self.play(FadeIn(a, shift=UP * 0.2), FadeIn(u, shift=UP * 0.2), run_time=0.5)
        self.play(Create(top_arc), Create(bot_arc), run_time=0.8)
        say("That's the whole algorithm.\nRepeat until nothing moves.")
        self.wait(1.6)

        say("The catch: YOU pick K, and\na bad start can mislead it.")
        self.wait(2.2)

        # ---------------------------------------------------- 8. outro
        outro = T("Follow for the next one", size=44, color=ACCENT).move_to([SAFE_CENTER_X, CAPTION_Y, 0])
        self.play(FadeOut(cap, shift=UP * 0.3), FadeIn(outro, shift=UP * 0.3), run_time=0.6)
        self.wait(1.5)
