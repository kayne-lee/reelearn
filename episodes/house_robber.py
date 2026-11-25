"""Episode: House Robber (LeetCode 198), explained without code.  (narrated, ~50 s, vertical, 3D)

Render:  ./make.sh house_robber silent    (no audio, no credits, 720p)
         ./make.sh house_robber           (ElevenLabs, 1080x1920)
"""
import sys
from pathlib import Path

import numpy as np
from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reelearn.scene import EpisodeScene  # noqa: E402
from reelearn.style import *  # noqa: E402,F403

# ---------------------------------------------------------------- the problem, solved for real
CASH = [2, 7, 9, 3, 1, 4]
N = len(CASH)


def solve(cash):
    """best[i] = most you can take from houses 0..i (no two neighbors). Also which houses."""
    best = []
    for i, c in enumerate(cash):
        skip = best[i - 1] if i >= 1 else 0
        rob = c + (best[i - 2] if i >= 2 else 0)
        best.append(max(skip, rob))
    picks, i = [], len(cash) - 1                       # trace back the chosen houses
    while i >= 0:
        if i == 0 or best[i] != best[i - 1]:
            picks.append(i)
            i -= 2
        else:
            i -= 1
    return best, sorted(picks)


BEST, PICKS = solve(CASH)
EVENS, ODDS = sum(CASH[0::2]), sum(CASH[1::2])
assert (BEST[-1], PICKS, EVENS, ODDS) == (15, [0, 2, 5], 12, 14), "script numbers out of sync with CASH"

# ---------------------------------------------------------------- layout
SPACING = 1.12
XS = [(i - (N - 1) / 2) * SPACING for i in range(N)]
CAMERA = dict(phi=66 * DEGREES, theta=-90 * DEGREES, zoom=1.0, frame_center=OUT * 0.6)
LABEL_Y_HERE = -3.0  # status badge sits just under the street
HOUSE_COLOR = "#4F56C9"   # indigo walls
ROOF_COLOR = "#E4572E"    # warm terracotta roofs
ROBBED = EMPH
ALARM = PALETTE[0]
TALLY = PALETTE[1]


def house(x, color=HOUSE_COLOR):
    w, d, h, rh = 0.9, 0.85, 1.0, 0.5
    body = Prism(dimensions=[w, d, h]).move_to([x, 0, h / 2]).set_fill(color, 1).set_stroke(WHITE, 0.6, 0.3)
    a, b = h, h + rh
    l, r, f, k = x - w / 2, x + w / 2, -d / 2, d / 2
    # ridge runs front-to-back, so the camera sees the triangular gable (reads as "house")
    roof = VGroup(
        Polygon([l, f, a], [r, f, a], [x, f, b]),                  # front gable
        Polygon([l, k, a], [r, k, a], [x, k, b]),                  # back gable
        Polygon([l, f, a], [l, k, a], [x, k, b], [x, f, b]),       # left slope
        Polygon([r, f, a], [r, k, a], [x, k, b], [x, f, b]),       # right slope
    ).set_fill(ROOF_COLOR, 1).set_stroke(WHITE, 0.6, 0.3)
    for p in roof:
        p.set_shade_in_3d(True)
    fy = f - 0.005  # just in front of the wall
    door = Polygon([x - 0.12, fy, 0], [x + 0.12, fy, 0], [x + 0.12, fy, 0.42], [x - 0.12, fy, 0.42])
    door.set_fill("#1B1E45", 1).set_stroke(width=0)
    window = Polygon([x - 0.3, fy, 0.55], [x - 0.16, fy, 0.55], [x - 0.16, fy, 0.7], [x - 0.3, fy, 0.7])
    window.set_fill("#FFE08A", 1).set_stroke(width=0)
    return VGroup(body, roof, door, window)


def cash_label(i):
    return T(f"${CASH[i]}", size=40, color=FG).move_to([XS[i], 0, 2.0])


def tally_badge(i, value=None, color=TALLY):
    text = "?" if value is None else str(value)
    return badge(text, size=34, color=color if value is not None else MUTED,
                 stroke=color if value is not None else FAINT).move_to([XS[i], -1.0, 0])


def street():
    return Rectangle(width=N * SPACING + 0.6, height=2.6, stroke_width=0,
                     fill_color="#1C1F4A", fill_opacity=0.85).move_to([0, -0.3, -0.01])


# ---------------------------------------------------------------- scene
class HouseRobber(EpisodeScene):
    def construct(self):
        self.set_camera_orientation(**CAMERA)
        self.label_y = LABEL_Y_HERE
        road = street()
        houses = VGroup(*[house(x) for x in XS])
        cash = VGroup(*[cash_label(i) for i in range(N)])
        self.add(road, houses)
        self.billboard(*cash)
        self.begin_camera_sway(amplitude=7 * DEGREES, period=14)

        def paint(idx, color, run_time=0.5, **kw):
            return [houses[i][0].animate.set_fill(color, 1) for i in idx]

        def reset_houses():
            return [h[0].animate.set_fill(HOUSE_COLOR, 1) for h in houses]

        # 1. hook: rob two neighbors, alarm
        with self.narrate("You're a robber on a street of houses. Rob two *neighbors,* and the alarm goes off. "
                          "What's the *most* you can take?") as t:
            budget = t.get_remaining_duration()
            self.wait(budget * 0.3)
            self.play(*paint([1, 2], ROBBED), run_time=0.4)
            rings = VGroup(*[Circle(radius=0.75, color=ALARM, stroke_width=6).move_to([XS[i], 0, 0.5])
                             .rotate(PI / 2, RIGHT) for i in (1, 2)])
            self.play(*[Flash(houses[i], color=ALARM, line_length=0.35, flash_radius=0.7) for i in (1, 2)],
                      *paint([1, 2], ALARM), FadeIn(rings, scale=0.6), run_time=0.6)
            self.play(FadeOut(rings, scale=1.4), *reset_houses(), run_time=0.6)

        # 2. every-other fails
        with self.narrate("Grabbing every other house gives *twelve,* or *fourteen.* But neither is the best.") as t:
            budget = t.get_remaining_duration()
            self.play(*paint([0, 2, 4], ROBBED), run_time=0.4)
            self.set_label(f"2 + 9 + 1 = {EVENS}", color=EMPH, stroke=EMPH)
            self.wait(budget * 0.25)
            self.play(*reset_houses(), run_time=0.3)
            self.play(*paint([1, 3, 5], ROBBED), *self.label_anims(f"7 + 3 + 4 = {ODDS}", color=EMPH, stroke=EMPH),
                      run_time=0.4)
            self.wait(max(0, t.get_remaining_duration() - 0.6))
            self.play(*reset_houses(), *self.label_anims(None), run_time=0.4)

        # 3. the trick: a running tally under each house
        tallies = [tally_badge(i) for i in range(N)]
        self.billboard(*tallies)
        for b in tallies:
            self.remove(b)
        with self.narrate("Here's the trick: walk the street *one house at a time,* "
                          "and write down the best haul so far.") as t:
            self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.2) for b in tallies], lag_ratio=0.12),
                      run_time=min(1.6, t.get_remaining_duration()))
            self.set_label("Best haul so far", color=TALLY, stroke=TALLY)

        def fill(i, color=TALLY, run_time=0.4):
            new = tally_badge(i, BEST[i], color)
            self.billboard(new)
            self.remove(new)
            old, tallies[i] = tallies[i], new
            return [FadeOut(old, scale=0.8), FadeIn(new, scale=1.3)]

        # 4. first two houses
        with self.narrate("House one: take the *two.* House two: seven beats two, so the best is *seven.*") as t:
            half = t.get_remaining_duration() / 2
            self.play(*paint([0], ROBBED), *fill(0), run_time=0.5)
            self.wait(max(0, half - 0.5))
            self.play(*paint([1], ROBBED), houses[0][0].animate.set_fill(HOUSE_COLOR, 1), *fill(1), run_time=0.5)
        self.play(*reset_houses(), run_time=0.3)

        # 5-6. the two choices, shown on house three
        with self.narrate("At each new house, you have *two choices.*"):
            self.play(Indicate(houses[2], color=EMPH, scale_factor=1.15), *self.label_anims("House 3", color=EMPH, stroke=EMPH),
                      run_time=0.8)

        with self.narrate("*Skip it,* and keep the best from the house before. "
                          "Or *rob it,* and add its cash to the best from *two houses back.*") as t:
            budget = t.get_remaining_duration()
            self.play(Indicate(tallies[1], color=TALLY, scale_factor=1.3),
                      *self.label_anims(f"Skip → {BEST[1]}", color=TALLY, stroke=TALLY), run_time=budget * 0.25)
            self.wait(budget * 0.2)
            self.play(*paint([2], ROBBED), Indicate(tallies[0], color=EMPH, scale_factor=1.3),
                      *self.label_anims(f"Rob → {CASH[2]} + {BEST[0]}", color=EMPH, stroke=EMPH),
                      run_time=budget * 0.25)

        # 7. house three resolved
        with self.narrate("House three: skip gives seven. Rob gives nine plus two, *eleven.* Keep eleven.") as t:
            budget = t.get_remaining_duration()
            self.wait(budget * 0.45)
            self.play(*self.label_anims(f"max(7, 11) = {BEST[2]}", color=EMPH, stroke=EMPH), *fill(2), run_time=0.6)
        self.play(*reset_houses(), run_time=0.3)

        # 8. the rest, quickly
        with self.narrate("Keep going. Eleven. Twelve. And at the last house, four plus eleven makes *fifteen.*") as t:
            per = t.get_remaining_duration() / 3
            for i in range(3, N):
                skip, rob = BEST[i - 1], CASH[i] + BEST[i - 2]
                took = rob > skip
                self.play(*paint([i], ROBBED if took else FAINT),
                          *self.label_anims(f"House {i + 1}: max({skip}, {CASH[i]} + {BEST[i - 2]})",
                                            color=EMPH, stroke=EMPH),
                          *fill(i, EMPH if i == N - 1 else TALLY), run_time=min(0.6, per * 0.5))
                self.wait(max(0, per - min(0.6, per * 0.5) - 0.25))
                self.play(houses[i][0].animate.set_fill(HOUSE_COLOR, 1), run_time=0.25)

        # 9. trace back the chosen houses
        with self.narrate("Trace it back, and you robbed the houses worth *two, nine, and four.*") as t:
            others = [i for i in range(N) if i not in PICKS]
            self.play(*paint(PICKS, ROBBED),
                      *[houses[i].animate.set_opacity(0.35) for i in others],
                      *[cash[i].animate.set_opacity(0.35) for i in others],
                      *self.label_anims("2 + 9 + 4 = 15", color=EMPH, stroke=EMPH),
                      run_time=min(1.0, t.get_remaining_duration()))
            self.play(*[Flash(houses[i], color=EMPH, line_length=0.3, flash_radius=0.65) for i in PICKS], run_time=0.8)

        # 10. recap
        skip_card = badge("Skip → best before", size=34, color=TALLY, stroke=TALLY)
        rob_card = badge("Rob → cash + best two back", size=34, color=EMPH, stroke=EMPH)
        cards = VGroup(skip_card, rob_card).arrange(DOWN, buff=0.3).move_to([SAFE_CENTER_X, -3.4, 0])
        self.overlay(cards)
        self.remove(cards)
        with self.narrate("That's dynamic programming: solve small pieces, and *reuse* the answers.") as t:
            self.play(*self.label_anims(None), run_time=0.3)
            self.play(LaggedStart(FadeIn(skip_card, shift=UP * 0.2), FadeIn(rob_card, shift=UP * 0.2), lag_ratio=0.4),
                      run_time=min(1.0, t.get_remaining_duration()))

        # 11. outro
        with self.narrate("Follow for more coding problems, explained *without the code.*"):
            pass
        self.wait(0.5)
