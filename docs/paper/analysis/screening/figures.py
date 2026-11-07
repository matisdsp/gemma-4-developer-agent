"""Figures for the screening paper.

    uv run --with matplotlib python docs/paper/analysis/screening/figures.py \
        --analysis results/screening_analysis.json --explore results/screening_explore.json \
        --out docs/paper/figures

Figure 1: per recipe, how often the agent obeys it (rule off vs on) beside its effect on resolved
tasks. Figure 2: how many of the 32 configurations solve each task.
Colours follow the dataviz reference palette: one blue hue in two steps for off and on, ink for
estimates, a hairline grid.
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, BAND = "#e1e0d9", "#c3c2b7", "#f0efec"
OFF, ON = "#86b6ef", "#1c5cab"

ROWS = [  # (recipe key, label, obedience check or None)
    ("useful_test", "Useful test", "useful_test"),
    ("imposed_verification", "Imposed verification", "imposed_verification"),
    ("compile_check", "Compile check", "compile_check"),
    ("spec_first", "Spec first", "spec_first"),
    ("reproduce_first", "Reproduce first", "reproduce_first"),
    ("worked_example", "Worked example", None),
    ("thinking_256", "Thinking budget 256", None),
    ("temperature_0.7", "Temperature 0.7", None),
]
NOT_A_RULE = {"worked_example": "shown, not a rule", "thinking_256": "setting",
              "temperature_0.7": "setting"}


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.xaxis.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)


def figure_obeyed_helped(analysis, explore, out):
    fig, (left, right) = plt.subplots(1, 2, figsize=(9.6, 4.1), sharey=True,
                                      gridspec_kw={"width_ratios": [1, 1.15], "wspace": 0.08})
    fig.patch.set_facecolor(SURFACE)
    ys = list(range(len(ROWS)))[::-1]
    for ax in (left, right):
        style(ax)
    for y, (key, label, check) in zip(ys, ROWS):
        if check:
            ob = explore["obedience"][check]
            off, on = 100 * ob["off"], 100 * ob["on"]
            left.plot([off, on], [y, y], color=AXIS, linewidth=2, solid_capstyle="round", zorder=1)
            left.scatter([off], [y], s=60, color=OFF, edgecolor=SURFACE, linewidth=2, zorder=2)
            left.scatter([on], [y], s=60, color=ON, edgecolor=SURFACE, linewidth=2, zorder=3)
            left.text(on + 2.5, y, f"{on:.0f}%", va="center", ha="left", fontsize=8.5, color=INK2)
        else:
            left.text(2, y, NOT_A_RULE[key], va="center", ha="left", fontsize=8.5, color=MUTED,
                      style="italic")
    left.set_xlim(-4, 110)
    left.set_yticks(ys)
    left.set_yticklabels([label for _, label, _ in ROWS], fontsize=9.5, color=INK)
    left.set_xlabel("Attempts that follow the rule (%)", fontsize=9, color=INK2)
    left.set_title("Did the agent obey?", fontsize=10.5, color=INK, loc="left", pad=8)
    left.scatter([], [], s=60, color=OFF, label="rule off")
    left.scatter([], [], s=60, color=ON, label="rule on")
    left.legend(loc="lower right", frameon=False, fontsize=8.5, labelcolor=INK2,
                handletextpad=0.3, borderaxespad=0.2)

    right.axvspan(-3, 3, color=BAND, zorder=0)
    right.axvline(0, color=AXIS, linewidth=1, zorder=1)
    for y, (key, _, _) in zip(ys, ROWS):
        e = analysis["primary"][key]
        est, low, high = 100 * e["estimate"], 100 * e["low"], 100 * e["high"]
        right.plot([low, high], [y, y], color=INK2, linewidth=2, solid_capstyle="round", zorder=2)
        right.scatter([est], [y], s=60, color=INK, edgecolor=SURFACE, linewidth=2, zorder=3)
        right.text(4.2, y, f"{est:+.1f}  [{low:+.1f}, {high:+.1f}]", va="center", ha="left",
                   fontsize=8.5, color=INK2)
    right.set_xlim(-5, 10.5)
    right.set_xticks([-4, -2, 0, 2, 4])
    right.set_xlabel("Effect on resolved attempts (points), 90% interval", fontsize=9, color=INK2)
    right.set_title("Did it help?", fontsize=10.5, color=INK, loc="left", pad=8)
    right.text(0, -0.75, "±3 points", ha="center", va="center", fontsize=8, color=MUTED)
    right.set_ylim(-1.05, len(ROWS) - 0.5)
    fig.savefig(out / "fig1_obeyed_helped.png", dpi=200, bbox_inches="tight",
                facecolor=SURFACE)
    plt.close(fig)


def figure_task_spread(explore, out):
    counts = explore["configs_solving_task"]
    xs = list(range(33))
    vals = [counts[str(x)] for x in xs]
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    fig.patch.set_facecolor(SURFACE)
    style(ax)
    ax.xaxis.grid(False)
    ax.yaxis.grid(True, color=GRID, linewidth=1)
    ax.bar(xs, vals, width=0.7, color=ON, zorder=2)
    for x, v in zip(xs, vals):
        if v:
            ax.text(x, v + 0.8, str(v), ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_xlim(-0.8, 32.8)
    ax.set_xticks([0, 4, 8, 12, 16, 20, 24, 28, 32])
    ax.set_xlabel("Configurations (of 32) that resolve the task", fontsize=9, color=INK2)
    ax.set_ylabel("Tasks", fontsize=9, color=INK2)
    ax.set_title("Tasks by the number of configurations that resolve them", fontsize=10.5,
                 color=INK, loc="left", pad=8)
    fig.savefig(out / "fig2_task_spread.png", dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--explore", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    analysis = json.loads(Path(args.analysis).read_text())
    explore = json.loads(Path(args.explore).read_text())
    figure_obeyed_helped(analysis, explore, args.out)
    figure_task_spread(explore, args.out)
    print(f"figures in {args.out}")


if __name__ == "__main__":
    main()
